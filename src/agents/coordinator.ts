/**
 * Coordinator — Agent 协调器
 * 
 * 统一调度所有 Agent 和自省触发器，管理事件流、状态流转和 GBrain 同步
 */

import { randomUUID } from "node:crypto";
import type {
  CoordinatorConfig,
  AgentContext,
  AgentRole,
  AgentState,
  AgentStateTransition,
  IntrospectionResult,
  IntrospectionResultStatus,
  TriggerExecutionResult,
  DEFAULT_COORDINATOR_CONFIG
} from "./types.js";
import type { ImageTask, GenerateTask } from "../types/task.js";
import { IntrospectionTrigger, scorePromptQuality } from "./introspectionTrigger.js";
import { getGlobalEventBus } from "./eventBus.js";
import type { GBrainClient } from "../services/gbrainClient.js";

// ============================================================================
// Coordinator 内部状态
// ============================================================================

interface CoordinatorState {
  /** 当前状态 */
  state: AgentState;
  /** 关联的当前任务 */
  currentTask?: ImageTask | GenerateTask;
  /** 当前自省结果 */
  currentIntrospection?: IntrospectionResult;
  /** 修正尝试次数 */
  correctionAttempts: number;
  /** 是否正在处理事件 */
  processingEvents: boolean;
}

// ============================================================================
// Coordinator 事件处理回调
// ============================================================================

export type CorrectionHandler = (
  task: ImageTask | GenerateTask,
  introspection: IntrospectionResult
) => Promise<{
  success: boolean;
  correctedTask?: ImageTask | GenerateTask;
  message: string;
}>;

export type RollbackHandler = (
  task: ImageTask | GenerateTask,
  introspection: IntrospectionResult
) => Promise<{
  success: boolean;
  rolledBackTo?: string;
  message: string;
}>;

export type GBrainSyncHandler = (
  timelineSlug: string,
  summary: string,
  details: Record<string, unknown>
) => Promise<boolean>;

// ============================================================================
// Coordinator 主类
// ============================================================================

export class Coordinator {
  private config: CoordinatorConfig;
  private state: CoordinatorState;
  private introspectionTrigger: IntrospectionTrigger;
  private gbrainClient?: GBrainClient;
  private agentContexts: Map<string, AgentContext> = new Map();
  private correctionHandler?: CorrectionHandler;
  private rollbackHandler?: RollbackHandler;
  private gbrainSyncHandler?: GBrainSyncHandler;

  constructor(
    config: Partial<CoordinatorConfig> = {},
    gbrainClient?: GBrainClient
  ) {
    this.config = { ...DEFAULT_COORDINATOR_CONFIG, ...config };
    this.state = {
      state: "idle",
      correctionAttempts: 0,
      processingEvents: false
    };
    this.introspectionTrigger = new IntrospectionTrigger();
    this.gbrainClient = gbrainClient;

    // 初始化默认 Agent 上下文
    this.initializeAgentContexts();

    // 订阅全局 EventBus
    this.subscribeToEventBus();
  }

  /** 初始化 Agent 上下文 */
  private initializeAgentContexts(): void {
    const roles: AgentRole[] = ["coordinator", "generator", "reviewer", "introspector", "syncer"];
    for (const role of roles) {
      this.agentContexts.set(role, {
        agentId: `${role}-001`,
        role,
        state: "idle",
        stateHistory: [],
        failureCount: 0,
        successCount: 0
      });
    }
  }

  /** 订阅 EventBus 事件 */
  private subscribeToEventBus(): void {
    const eventBus = getGlobalEventBus();

    // 订阅任务完成事件
    eventBus.subscribe({
      id: "coordinator-task-completed",
      eventType: "task_completed",
      callback: async (event) => this.handleTaskCompleted(event.payload),
      priority: 10,
      once: false
    });

    // 订阅任务失败事件
    eventBus.subscribe({
      id: "coordinator-task-failed",
      eventType: "task_failed",
      callback: async (event) => this.handleTaskFailed(event.payload),
      priority: 10,
      once: false
    });

    // 订阅触发器 fired 事件
    eventBus.subscribe({
      id: "coordinator-trigger-fired",
      eventType: "trigger_fired",
      callback: async (event) => this.handleTriggerFired(event.payload),
      priority: 5,
      once: false
    });

    // 订阅自省完成事件
    eventBus.subscribe({
      id: "coordinator-introspection-done",
      eventType: "introspection_completed",
      callback: async (event) => this.handleIntrospectionCompleted(event.payload),
      priority: 5,
      once: false
    });
  }

  /** 设置自定义修正处理函数 */
  setCorrectionHandler(handler: CorrectionHandler): void {
    this.correctionHandler = handler;
  }

  /** 设置自定义回滚处理函数 */
  setRollbackHandler(handler: RollbackHandler): void {
    this.rollbackHandler = handler;
  }

  /** 设置自定义 GBrain 同步处理函数 */
  setGBrainSyncHandler(handler: GBrainSyncHandler): void {
    this.gbrainSyncHandler = handler;
  }

  // ========================================================================
  // 任务生命周期处理
  // ========================================================================

  /** 处理任务开始 */
  async handleTaskStarted(task: ImageTask | GenerateTask): Promise<void> {
    this.state.currentTask = task;
    this.updateAgentState("generator", "working");

    await this.publishEvent("task_started", {
      taskId: task.task_id,
      templateId: task.template.template_id,
      timestamp: new Date().toISOString()
    });
  }

  /** 处理任务完成（autoSelfApproving） */
  async handleTaskCompleted(payload: Record<string, unknown>): Promise<void> {
    const task = payload.task as ImageTask | GenerateTask | undefined;
    if (!task) return;

    this.state.currentTask = task;
    this.updateAgentState("generator", "idle");
    this.updateAgentState("coordinator", "introspecting");

    // 触发自省
    const triggerResult = this.introspectionTrigger.evaluateTaskCompleted(task);
    
    if (triggerResult.triggered && triggerResult.introspectionResult) {
      await this.processIntrospectionResult(triggerResult.introspectionResult);
    }

    // 同步到 GBrain
    if (this.config.gbrainSyncEnabled && task.status === "completed") {
      await this.syncToGBrain(task, "task_completed");
    }
  }

  /** 处理任务失败 */
  async handleTaskFailed(payload: Record<string, unknown>): Promise<void> {
    const task = payload.task as ImageTask | GenerateTask | undefined;
    const error = payload.error as Error | undefined;
    if (!task) return;

    this.state.currentTask = task;
    this.updateAgentState("generator", "error");
    this.updateAgentState("coordinator", "introspecting");

    // 更新失败计数
    const generatorContext = this.agentContexts.get("generator");
    if (generatorContext) {
      generatorContext.failureCount++;
    }

    // 触发失败自省
    const triggerResult = this.introspectionTrigger.evaluateTaskFailed(task, error);
    
    if (triggerResult.triggered && triggerResult.introspectionResult) {
      await this.processIntrospectionResult(triggerResult.introspectionResult);
    }

    // 同步到 GBrain
    if (this.config.gbrainSyncEnabled) {
      await this.syncToGBrain(task, "task_failed", { error: error?.message });
    }
  }

  /** 处理 Prompt 质量检查 */
  async handlePromptQualityCheck(
    prompt: string,
    negativePrompt?: string,
    threshold: number = 70
  ): Promise<TriggerExecutionResult> {
    const triggerResult = this.introspectionTrigger.evaluatePromptQuality(
      prompt, negativePrompt, threshold
    );

    if (triggerResult.triggered && triggerResult.introspectionResult) {
      // 发布质量评分事件
      await this.publishEvent("prompt_quality_scored", {
        score: triggerResult.introspectionResult.findings[0]?.description,
        suggestions: triggerResult.introspectionResult.correctionSuggestions
      });

      // 自动尝试修正
      if (this.correctionHandler && this.state.currentTask) {
        const correctionResult = await this.correctionHandler(
          this.state.currentTask,
          triggerResult.introspectionResult
        );
        
        if (correctionResult.success) {
          await this.publishEvent("correction_applied", {
            message: correctionResult.message
          });
        }
      }
    }

    return triggerResult;
  }

  // ========================================================================
  // 自省结果处理
  // ========================================================================

  /** 处理自省结果 */
  private async processIntrospectionResult(result: IntrospectionResult): Promise<void> {
    this.state.currentIntrospection = result;
    this.updateAgentState("introspector", "approving");

    // 发布自省完成事件
    await this.publishEvent("introspection_completed", {
      introspectionId: result.introspectionId,
      taskId: result.taskId,
      status: result.status,
      findingsCount: result.findings.length,
      suggestRollback: result.suggestRollback
    });

    // 根据自省结果状态执行相应操作
    switch (result.status) {
      case "passed":
        await this.handleIntrospectionPassed(result);
        break;
      case "needs_correction":
        await this.handleIntrospectionNeedsCorrection(result);
        break;
      case "needs_review":
        await this.handleIntrospectionNeedsReview(result);
        break;
      case "rollback_needed":
        await this.handleIntrospectionRollbackNeeded(result);
        break;
    }

    // 同步自省结果到 GBrain
    if (this.config.gbrainSyncEnabled) {
      await this.syncIntrospectionToGBrain(result);
    }

    this.updateAgentState("coordinator", "idle");
  }

  /** 处理自省通过 */
  private async handleIntrospectionPassed(result: IntrospectionResult): Promise<void> {
    this.updateAgentState("introspector", "approved");
    const generatorContext = this.agentContexts.get("generator");
    if (generatorContext) {
      generatorContext.successCount++;
    }

    await this.publishEvent("agent_state_changed", {
      agentRole: "introspector",
      newState: "approved"
    });
  }

  /** 处理需要修正 */
  private async handleIntrospectionNeedsCorrection(result: IntrospectionResult): Promise<void> {
    this.updateAgentState("introspector", "rejected");

    if (this.correctionHandler && this.state.currentTask) {
      if (this.state.correctionAttempts < this.config.maxAutoCorrectionAttempts) {
        this.state.correctionAttempts++;
        
        const correctionResult = await this.correctionHandler(this.state.currentTask, result);
        
        if (correctionResult.success) {
          await this.publishEvent("correction_applied", {
            attempts: this.state.correctionAttempts,
            message: correctionResult.message
          });

          // 修正后重新评估
          if (correctionResult.correctedTask) {
            this.state.currentTask = correctionResult.correctedTask;
            // 可以重新触发质量检查
          }
        } else {
          // 修正失败，增加失败计数
          const introspectorContext = this.agentContexts.get("introspector");
          if (introspectorContext) {
            introspectorContext.failureCount++;
          }
        }
      } else {
        // 达到最大尝试次数，需要人工介入
        await this.publishEvent("correction_failed", {
          attempts: this.state.correctionAttempts,
          maxAttempts: this.config.maxAutoCorrectionAttempts,
          suggestions: result.correctionSuggestions
        });
      }
    }
  }

  /** 处理需要人工审查 */
  private async handleIntrospectionNeedsReview(result: IntrospectionResult): Promise<void> {
    this.updateAgentState("introspector", "rejected");
    
    await this.publishEvent("review_required", {
      introspectionId: result.introspectionId,
      findings: result.findings,
      suggestions: result.correctionSuggestions
    });
  }

  /** 处理需要回滚 */
  private async handleIntrospectionRollbackNeeded(result: IntrospectionResult): Promise<void> {
    this.updateAgentState("coordinator", "rollback");
    this.updateAgentState("introspector", "rejected");

    if (this.rollbackHandler && this.state.currentTask) {
      const rollbackResult = await this.rollbackHandler(this.state.currentTask, result);
      
      if (rollbackResult.success) {
        await this.publishEvent("rollback_completed", {
          rolledBackTo: rollbackResult.rolledBackTo,
          message: rollbackResult.message
        });
      }
    }
  }

  // ========================================================================
  // 事件处理
  // ========================================================================

  private async handleTriggerFired(payload: Record<string, unknown>): Promise<void> {
    // 触发器 fired 事件已在 evaluate 方法中处理
    // 这里可以做额外的日志记录或监控
  }

  private async handleIntrospectionCompleted(payload: Record<string, unknown>): Promise<void> {
    // 自省完成后的后续处理
  }

  // ========================================================================
  // GBrain 同步
  // ========================================================================

  /** 同步任务状态到 GBrain 时间线 */
  private async syncToGBrain(
    task: ImageTask | GenerateTask,
    event: string,
    extraDetails?: Record<string, unknown>
  ): Promise<void> {
    if (!this.gbrainClient || !this.gbrainSyncHandler) {
      return;
    }

    const timelineSlug = `${this.config.gbrainTimelinePrefix}_${task.task_id}`;
    const summary = `[${event}] Task ${task.task_id}: ${task.status}`;
    const details = {
      taskId: task.task_id,
      templateId: task.template.template_id,
      status: task.status,
      timestamp: new Date().toISOString(),
      ...extraDetails
    };

    try {
      const success = await this.gbrainSyncHandler(timelineSlug, summary, details);
      if (success) {
        await this.gbrainClient.sync();
      }
    } catch (error) {
      console.error("[Coordinator] GBrain sync failed:", error);
    }
  }

  /** 同步自省结果到 GBrain */
  private async syncIntrospectionToGBrain(result: IntrospectionResult): Promise<void> {
    if (!this.gbrainClient || !this.gbrainSyncHandler) {
      return;
    }

    const timelineSlug = `${this.config.gbrainTimelinePrefix}_${result.introspectionId}`;
    const summary = `[Introspection] Task ${result.taskId}: ${result.status}`;
    const details = {
      introspectionId: result.introspectionId,
      taskId: result.taskId,
      status: result.status,
      findings: result.findings.map(f => ({
        description: f.description,
        severity: f.severity,
        category: f.category
      })),
      suggestions: result.correctionSuggestions,
      durationMs: result.durationMs,
      timestamp: result.timestamp
    };

    try {
      const success = await this.gbrainSyncHandler(timelineSlug, summary, details);
      if (success) {
        await this.gbrainClient.sync();
      }
    } catch (error) {
      console.error("[Coordinator] GBrain introspection sync failed:", error);
    }
  }

  // ========================================================================
  // 状态管理
  // ========================================================================

  /** 更新 Agent 状态 */
  private updateAgentState(role: AgentRole, newState: AgentState): void {
    const context = this.agentContexts.get(role);
    if (!context) return;

    const transition: AgentStateTransition = {
      from: context.state,
      to: newState,
      trigger: "coordinator_update",
      timestamp: new Date().toISOString()
    };

    context.state = newState;
    context.stateHistory.push(transition);
  }

  /** 获取 Agent 上下文 */
  getAgentContext(role: AgentRole): AgentContext | undefined {
    return this.agentContexts.get(role);
  }

  /** 获取所有 Agent 上下文 */
  getAllAgentContexts(): Map<string, AgentContext> {
    return new Map(this.agentContexts);
  }

  /** 获取当前状态 */
  getState(): CoordinatorState {
    return { ...this.state };
  }

  /** 发布事件 */
  private async publishEvent(
    type: Parameters<typeof getGlobalEventBus>["0"]["publish"]["type"],
    payload: Record<string, unknown>
  ): Promise<string> {
    const eventBus = getGlobalEventBus();
    return eventBus.publish({
      type,
      sourceAgent: this.config.coordinatorId,
      payload,
      priority: 5
    });
  }

  /** 获取自省触发器 */
  getIntrospectionTrigger(): IntrospectionTrigger {
    return this.introspectionTrigger;
  }

  /** 获取配置 */
  getConfig(): CoordinatorConfig {
    return { ...this.config };
  }
}

/** 创建默认 Coordinator 实例 */
export function createCoordinator(
  config?: Partial<CoordinatorConfig>,
  gbrainClient?: GBrainClient
): Coordinator {
  return new Coordinator(config, gbrainClient);
}
