/**
 * Agent 基类
 * 定义通用接口：execute, record, sync
 * 所有 Agent 必须继承此类
 */

import type {
  AgentContext,
  AgentExecutionResult,
  AgentRole,
  AgentState,
  GBrainRuleContext,
  IntrospectionResult,
} from "./types.js";
import { EventBus } from "./eventBus.js";
import { GBrainClient } from "../services/gbrainClient.js";

export abstract class Agent {
  /** Agent 唯一标识 */
  public readonly id: string;

  /** Agent 角色 */
  public readonly role: AgentRole;

  /** 当前状态 */
  public state: AgentState = "idle";

  /** 事件总线 */
  protected readonly eventBus: EventBus;

  /** GBrain 客户端（可选） */
  protected gbrainClient?: GBrainClient;

  /** GBrain 是否启用 */
  protected gbrainEnabled: boolean = false;

  /** GBrain 规则上下文 */
  protected ruleContext: GBrainRuleContext = {
    gbrainQueried: false,
    recordSubmitted: false,
    syncTriggered: false,
    selfApproved: false,
  };

  /** 执行上下文 */
  protected context: AgentContext | null = null;

  /** 事件日志 */
  protected eventLog: Array<{ timestamp: string; action: string; details: unknown }> = [];

  constructor(id: string, role: AgentRole, eventBus: EventBus) {
    this.id = id;
    this.role = role;
    this.eventBus = eventBus;
  }

  // ──────────────────────────────────────────
  // 核心接口
  // ──────────────────────────────────────────

  /**
   * 执行 Agent 任务
   * 子类必须实现此方法
   */
  abstract execute(context: AgentContext): Promise<AgentExecutionResult>;

  /**
   * 记录决策/发现到 GBrain（recordEverything 规则）
   */
  async record(
    context: AgentContext,
    slug: string,
    content: string
  ): Promise<boolean> {
    if (!context.gbrainEnabled || !context.gbrainClient) {
      this._log("record", { slug, content, skipped: "gbrainDisabled" });
      return false;
    }

    try {
      await context.gbrainClient.putPage(slug, content);
      context.ruleContext.recordSubmitted = true;
      this._log("record", { slug, success: true });

      // 发布记录事件
      await this.eventBus.emit(
        this.eventBus.createMessage(
          this.id,
          "gbrain_record",
          { slug, content, agent: this.id, role: this.role },
          { taskId: context.taskId }
        )
      );

      return true;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      this._log("record", { slug, error: errorMessage, success: false });
      return false;
    }
  }

  /**
   * 触发 GBrain 同步（syncAfterWrite 规则）
   */
  async sync(context: AgentContext): Promise<boolean> {
    if (!context.gbrainEnabled || !context.gbrainClient) {
      this._log("sync", { skipped: "gbrainDisabled" });
      return false;
    }

    try {
      await context.gbrainClient.sync();
      context.ruleContext.syncTriggered = true;
      this._log("sync", { success: true });

      await this.eventBus.emit(
        this.eventBus.createMessage(
          this.id,
          "gbrain_sync",
          { agent: this.id, role: this.role },
          { taskId: context.taskId }
        )
      );

      return true;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      this._log("sync", { error: errorMessage, success: false });
      return false;
    }
  }

  /**
   * 自省 — 所有 Agent 必须实现自省逻辑
   */
  abstract introspect(context: AgentContext, result: AgentExecutionResult): Promise<IntrospectionResult>;

  // ──────────────────────────────────────────
  // 状态管理
  // ──────────────────────────────────────────

  /**
   * 更新 Agent 状态并发布事件
   */
  protected async setState(newState: AgentState, context: AgentContext): Promise<void> {
    const previousState = this.state;
    this.state = newState;
    context.state = newState;

    this._log("state_change", { from: previousState, to: newState });

    await this.eventBus.emit(
      this.eventBus.createMessage(
        this.id,
        "state_changed",
        { agent: this.id, role: this.role, previousState, newState },
        { taskId: context.taskId }
      )
    );
  }

  // ──────────────────────────────────────────
  // GBrain 集成规则
  // ──────────────────────────────────────────

  /**
   * gbrainFirst 规则：执行前查询 GBrain
   */
  protected async gbrainFirst(
    context: AgentContext,
    query: string
  ): Promise<unknown | null> {
    if (!context.gbrainEnabled || !context.gbrainClient) {
      this._log("gbrainFirst", { query, skipped: "gbrainDisabled" });
      context.ruleContext.gbrainQueried = true; // 标记为已查询（降级模式）
      return null;
    }

    try {
      const result = await context.gbrainClient.search(query);
      context.ruleContext.gbrainQueried = true;
      context.ruleContext.gbrainSearchResult = result;
      this._log("gbrainFirst", { query, resultFound: (result as any)?.total ?? 0 });

      await this.eventBus.emit(
        this.eventBus.createMessage(
          this.id,
          "gbrain_query",
          { query, result, agent: this.id, role: this.role },
          { taskId: context.taskId }
        )
      );

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      this._log("gbrainFirst", { query, error: errorMessage, skipped: true });
      return null;
    }
  }

  /**
   * 自省后自动提交自省结果到 GBrain
   */
  protected async selfApprove(
    context: AgentContext,
    introspection: IntrospectionResult
  ): Promise<void> {
    context.ruleContext.selfApproved = true;
    context.ruleContext.introspectionResult = introspection;

    this._log("selfApprove", { taskId: introspection.taskId, passed: introspection.passed });

    await this.eventBus.emit(
      this.eventBus.createMessage(
        this.id,
        "introspection_result",
        { ...introspection, agent: this.id, role: this.role },
        { taskId: introspection.taskId }
      )
    );
  }

  // ──────────────────────────────────────────
  // 辅助方法
  // ──────────────────────────────────────────

  /**
   * 记录操作日志
   */
  protected _log(action: string, details: unknown): void {
    this.eventLog.push({
      timestamp: new Date().toISOString(),
      action,
      details,
    });
  }

  /**
   * 获取日志
   */
  getEventLog(): typeof this.eventLog {
    return [...this.eventLog];
  }

  /**
   * 清空日志
   */
  clearEventLog(): void {
    this.eventLog = [];
  }

  /**
   * 重置规则上下文
   */
  resetRuleContext(): void {
    this.ruleContext = {
      gbrainQueried: false,
      recordSubmitted: false,
      syncTriggered: false,
      selfApproved: false,
    };
  }
}

/**
 * 创建 Agent 实例的工厂函数类型
 */
export type AgentFactory<T extends Agent> = (
  eventBus: EventBus,
  gbrainClient?: GBrainClient
) => T;
