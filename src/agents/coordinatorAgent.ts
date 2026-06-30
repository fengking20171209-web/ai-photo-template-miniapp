/**
 * Coordinator Agent — 任务分发和状态管理
 *
 * 职责：
 * 1. 接收任务请求，分派给 Generator / Reviewer
 * 2. 维护任务状态机
 * 3. 协调 Agent 间协作
 * 4. 触发自省流程
 */

import { Agent } from "./agentBase.js";
import type {
  AgentContext,
  AgentExecutionResult,
  AgentRole,
  AgentState,
  CoordinatorState,
  IntrospectionResult,
  TaskAssignment,
} from "./types.js";
import { EventBus } from "./eventBus.js";
import { AGENT_TERMINAL_STATES } from "./types.js";

export class CoordinatorAgent extends Agent {
  /** Coordinator 内部状态 */
  private stateStore: CoordinatorState = {
    assignments: new Map(),
    agentStates: new Map(),
    eventLog: [],
  };

  /** 注册的 Agent */
  private registeredAgents: Map<AgentRole, Agent> = new Map();

  constructor(id: string, eventBus: EventBus) {
    super(id, "coordinator", eventBus);
  }

  /**
   * 注册子 Agent
   */
  registerAgent(agent: Agent): void {
    this.registeredAgents.set(agent.role, agent);
    this.stateStore.agentStates.set(agent.id, "idle");
    this._log("register_agent", { agentId: agent.id, role: agent.role });
  }

  /**
   * 获取已注册 Agent
   */
  getAgent(role: AgentRole): Agent | undefined {
    return this.registeredAgents.get(role);
  }

  /**
   * 获取所有注册 Agent
   */
  getAllAgents(): Agent[] {
    return [...this.registeredAgents.values()];
  }

  /**
   * 获取 Coordinator 状态快照
   */
  getStateSnapshot(): CoordinatorState {
    return {
      assignments: new Map(this.stateStore.assignments),
      agentStates: new Map(this.stateStore.agentStates),
      eventLog: [...this.stateStore.eventLog],
    };
  }

  // ──────────────────────────────────────────
  // Agent 基类实现
  // ──────────────────────────────────────────

  async execute(context: AgentContext): Promise<AgentExecutionResult> {
    await this.setState("working", context);

    try {
      // gbrainFirst: 执行前查询 GBrain 获取任务上下文
      if (context.taskId) {
        await this.gbrainFirst(context, `task:${context.taskId}`);
      }

      // 执行任务分派
      const result = await this._dispatchTask(context);

      // recordEverything: 记录分派结果
      if (context.gbrainEnabled) {
        const recordSlug = `coordinator/${context.taskId ?? "unknown"}/dispatch`;
        const recordContent = JSON.stringify(
          {
            agent: this.id,
            role: this.role,
            timestamp: new Date().toISOString(),
            assignments: Object.fromEntries(this.stateStore.assignments),
          },
          null,
          2
        );
        await this.record(context, recordSlug, recordContent);
        await this.sync(context);
      }

      await this.setState("idle", context);

      return {
        success: true,
        state: "idle",
        output: result,
        metadata: { assignmentsCount: this.stateStore.assignments.size },
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      await this.setState("error", context);

      return {
        success: false,
        state: "error",
        error: errorMessage,
        metadata: { errorStack: errorMessage },
      };
    }
  }

  async introspect(
    context: AgentContext,
    result: AgentExecutionResult
  ): Promise<IntrospectionResult> {
    const introspection: IntrospectionResult = {
      taskId: context.taskId ?? "unknown",
      passed: result.success,
      score: result.success ? 100 : 0,
      issues: result.error ? [result.error] : [],
      recommendations: [],
      timestamp: new Date().toISOString(),
      agentRole: this.role,
    };

    // 检查子 Agent 状态
    for (const [role, agent] of this.registeredAgents) {
      if (AGENT_TERMINAL_STATES.has(agent.state)) {
        introspection.issues.push(
          `Agent ${agent.id} (${role}) ended in terminal state: ${agent.state}`
        );
        introspection.score = Math.max(0, introspection.score - 20);
      }
    }

    // 检查任务完成情况
    const completed = [...this.stateStore.assignments.values()].filter(
      (a) => a.status === "completed"
    ).length;
    const failed = [...this.stateStore.assignments.values()].filter(
      (a) => a.status === "failed"
    ).length;

    if (failed > 0) {
      introspection.recommendations.push(`有 ${failed} 个子任务失败，需要重试`);
      introspection.score = Math.max(0, introspection.score - failed * 10);
    }

    introspection.passed = introspection.score >= 60;

    // 提交自省结果
    await this.selfApprove(context, introspection);

    return introspection;
  }

  // ──────────────────────────────────────────
  // 任务分派逻辑
  // ──────────────────────────────────────────

  /**
   * 分派任务到子 Agent
   */
  private async _dispatchTask(context: AgentContext): Promise<{
    assignments: TaskAssignment[];
  }> {
    if (!context.taskId) {
      throw new Error("Coordinator: taskId is required for dispatch");
    }

    const assignments: TaskAssignment[] = [];

    // 分派给 Generator
    const generator = this.registeredAgents.get("generator");
    if (generator) {
      const assignment: TaskAssignment = {
        taskId: context.taskId,
        templateId: context.template?.template_id ?? "unknown",
        assignedTo: "generator",
        createdAt: new Date().toISOString(),
        status: "running",
      };
      this.stateStore.assignments.set(context.taskId, assignment);
      this.stateStore.agentStates.set(generator.id, "working");
      assignments.push(assignment);

      // 发布任务分配事件
      await this.eventBus.emit(
        this.eventBus.createMessage(
          this.id,
          "task_assigned",
          { taskId: context.taskId, assignedTo: "generator", templateId: assignment.templateId },
          { taskId: context.taskId, role: "coordinator" }
        )
      );

      // 执行 Generator
      const generatorContext: AgentContext = {
        ...context,
        taskId: context.taskId,
        state: "working",
      };
      const generatorResult = await generator.execute(generatorContext);

      assignment.status = generatorResult.success ? "completed" : "failed";
      assignment.result = generatorResult;
      this.stateStore.agentStates.set(generator.id, generatorResult.state);
      this.stateStore.assignments.set(context.taskId, assignment);

      // 发布任务完成事件
      await this.eventBus.emit(
        this.eventBus.createMessage(
          this.id,
          generatorResult.success ? "task_completed" : "task_failed",
          { taskId: context.taskId, agent: generator.id, result: generatorResult },
          { taskId: context.taskId, role: "coordinator" }
        )
      );
    }

    // 分派给 Reviewer（如果 Generator 成功）
    const reviewer = this.registeredAgents.get("reviewer");
    const generatorAssignment = assignments.find((a) => a.assignedTo === "generator");
    if (reviewer && generatorAssignment?.status === "completed") {
      const reviewerAssignment: TaskAssignment = {
        taskId: context.taskId,
        templateId: context.template?.template_id ?? "unknown",
        assignedTo: "reviewer",
        createdAt: new Date().toISOString(),
        status: "running",
      };
      this.stateStore.assignments.set(`${context.taskId}:review`, reviewerAssignment);
      this.stateStore.agentStates.set(reviewer.id, "working");

      await this.eventBus.emit(
        this.eventBus.createMessage(
          this.id,
          "task_assigned",
          { taskId: context.taskId, assignedTo: "reviewer", templateId: reviewerAssignment.templateId },
          { taskId: context.taskId, role: "coordinator" }
        )
      );

      const reviewerContext: AgentContext = {
        ...context,
        taskId: context.taskId,
        state: "working",
      };
      const reviewerResult = await reviewer.execute(reviewerContext);

      reviewerAssignment.status = reviewerResult.success ? "completed" : "failed";
      reviewerAssignment.result = reviewerResult;
      this.stateStore.agentStates.set(reviewer.id, reviewerResult.state);
      this.stateStore.assignments.set(`${context.taskId}:review`, reviewerAssignment);

      await this.eventBus.emit(
        this.eventBus.createMessage(
          this.id,
          reviewerResult.success ? "task_completed" : "task_failed",
          { taskId: context.taskId, agent: reviewer.id, result: reviewerResult },
          { taskId: context.taskId, role: "coordinator" }
        )
      );
    }

    return { assignments };
  }

  /**
   * 查询任务状态
   */
  getTaskStatus(taskId: string): TaskAssignment | undefined {
    return this.stateStore.assignments.get(taskId);
  }

  /**
   * 重置 Coordinator 状态
   */
  reset(): void {
    this.stateStore = {
      assignments: new Map(),
      agentStates: new Map(),
      eventLog: [],
    };
    this.resetRuleContext();
    this.clearEventLog();
  }
}

/**
 * 创建 Coordinator Agent
 */
export function createCoordinatorAgent(
  id: string = "coordinator-1",
  eventBus?: EventBus
): CoordinatorAgent {
  const bus = eventBus ?? new EventBus();
  return new CoordinatorAgent(id, bus);
}
