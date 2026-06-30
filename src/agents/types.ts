/**
 * 多 Agent 框架类型定义
 * 
 * 包含 Agent 角色、状态机、触发器配置、事件协议等核心类型
 */

import type { ImageTask, GenerateTask } from "../types/task.js";

// ============================================================================
// Agent 角色定义
// ============================================================================

export type AgentRole = 
  | "coordinator"    // 协调器：统一调度所有 Agent 和触发器
  | "generator"      // 生成器：负责 prompt 生成和图像生成
  | "reviewer"       // 审查器：审查 prompt 质量和生成结果
  | "introspector"   // 自省器：执行自省分析和修正建议
  | "syncer";        // 同步器：负责与 GBrain 同步数据

// ============================================================================
// Agent 状态机
// ============================================================================

export type AgentState = 
  | "idle"           // 空闲，等待任务
  | "working"        // 正在执行任务
  | "introspecting"  // 正在执行自省
  | "approving"      // 正在审批自省结果
  | "approved"       // 自省通过
  | "rejected"       // 自省不通过，需要修正
  | "error"          // 发生错误
  | "rollback";      // 正在回滚

export interface AgentStateTransition {
  from: AgentState;
  to: AgentState;
  trigger: string;
  timestamp: string;
}

// ============================================================================
// 触发器配置
// ============================================================================

export type TriggerType = 
  | "task_completed"    // 任务完成触发器 (autoSelfApproving)
  | "task_failed"       // 任务失败触发器
  | "prompt_quality"    // Prompt 质量评分触发器
  | "manual";           // 手动触发器

export type TriggerAction = 
  | "introspect"        // 触发自省
  | "correct"           // 尝试自动修正
  | "notify"            // 通知 Coordinator
  | "rollback"          // 回滚到上一个状态
  | "sync_to_gbrain";   // 同步到 GBrain

export interface TriggerThreshold {
  /** 触发阈值 */
  value: number;
  /** 比较操作符: less_than | greater_than | equals | between */
  operator: "less_than" | "greater_than" | "equals" | "between";
  /** 用于 between 操作符的上界 */
  upperBound?: number;
}

export interface TriggerConfig {
  /** 触发器唯一标识 */
  id: string;
  /** 触发器类型 */
  type: TriggerType;
  /** 触发条件描述 */
  condition: string;
  /** 阈值配置（用于质量评分等量化触发器） */
  threshold?: TriggerThreshold;
  /** 触发动作列表 */
  actions: TriggerAction[];
  /** 是否启用 */
  enabled: boolean;
  /** 优先级（数字越小优先级越高） */
  priority: number;
  /** 冷却时间（毫秒），防止重复触发 */
  cooldownMs: number;
  /** 最大重试次数 */
  maxRetries: number;
  /** 关联的 Agent 角色 */
  agentRole: AgentRole;
}

// 默认触发器配置
export const DEFAULT_TRIGGERS: TriggerConfig[] = [
  {
    id: "auto-self-approving",
    type: "task_completed",
    condition: "任务状态变为 completed 时自动触发自省",
    actions: ["introspect", "sync_to_gbrain"],
    enabled: true,
    priority: 1,
    cooldownMs: 5000,
    maxRetries: 3,
    agentRole: "introspector"
  },
  {
    id: "failure-introspection",
    type: "task_failed",
    condition: "任务状态变为 failed 或发生异常时触发自省并尝试修正",
    actions: ["introspect", "correct", "notify"],
    enabled: true,
    priority: 0,
    cooldownMs: 2000,
    maxRetries: 2,
    agentRole: "introspector"
  },
  {
    id: "prompt-quality-check",
    type: "prompt_quality",
    condition: "Prompt 质量评分低于阈值时触发修正",
    threshold: {
      value: 70,
      operator: "less_than"
    },
    actions: ["introspect", "correct", "notify"],
    enabled: true,
    priority: 2,
    cooldownMs: 3000,
    maxRetries: 3,
    agentRole: "reviewer"
  }
];

// ============================================================================
// 自省结果
// ============================================================================

export type IntrospectionResultStatus = 
  | "passed"           // 自省通过
  | "needs_correction" // 需要修正
  | "needs_review"     // 需要人工审查
  | "rollback_needed"; // 需要回滚

export interface IntrospectionFinding {
  /** 发现的问题描述 */
  description: string;
  /** 问题严重程度 */
  severity: "low" | "medium" | "high" | "critical";
  /** 问题类别 */
  category: "prompt_quality" | "template_mismatch" | "parameter_error" | "output_quality" | "other";
  /** 建议的修正措施 */
  suggestedCorrection?: string;
  /** 相关证据（日志、截图路径等） */
  evidence?: string;
}

export interface IntrospectionResult {
  /** 自省唯一标识 */
  introspectionId: string;
  /** 关联的任务 ID */
  taskId: string;
  /** 自省状态 */
  status: IntrospectionResultStatus;
  /** 自省时间 */
  timestamp: string;
  /** 发现的问题列表 */
  findings: IntrospectionFinding[];
  /** 修正建议 */
  correctionSuggestions: string[];
  /** 是否建议回滚 */
  suggestRollback: boolean;
  /** 回滚目标（如果有） */
  rollbackTarget?: string;
  /** 自省耗时（毫秒） */
  durationMs: number;
  /** 自省者 Agent ID */
  introspectorId: string;
  /** 原始任务数据快照 */
  taskSnapshot?: Partial<ImageTask | GenerateTask>;
}

// ============================================================================
// 事件协议
// ============================================================================

export type EventType = 
  | "task_started"
  | "task_completed"
  | "task_failed"
  | "trigger_fired"
  | "introspection_started"
  | "introspection_completed"
  | "correction_applied"
  | "rollback_started"
  | "rollback_completed"
  | "sync_to_gbrain"
  | "agent_state_changed"
  | "prompt_quality_scored";

export interface AgentEvent {
  /** 事件唯一标识 */
  eventId: string;
  /** 事件类型 */
  type: EventType;
  /** 事件来源 Agent */
  sourceAgent: string;
  /** 事件目标 Agent（可选） */
  targetAgent?: string;
  /** 事件时间戳 */
  timestamp: string;
  /** 事件负载数据 */
  payload: Record<string, unknown>;
  /** 事件优先级 */
  priority: number;
}

// ============================================================================
// Coordinator 配置
// ============================================================================

export interface CoordinatorConfig {
  /** Coordinator ID */
  coordinatorId: string;
  /** 启用的触发器 ID 列表 */
  enabledTriggerIds: string[];
  /** 事件队列最大长度 */
  maxEventQueueSize: number;
  /** 自省超时时间（毫秒） */
  introspectionTimeoutMs: number;
  /** 自动修正最大尝试次数 */
  maxAutoCorrectionAttempts: number;
  /** 是否启用 GBrain 同步 */
  gbrainSyncEnabled: boolean;
  /** GBrain 时间线前缀 */
  gbrainTimelinePrefix: string;
}

export const DEFAULT_COORDINATOR_CONFIG: CoordinatorConfig = {
  coordinatorId: "coordinator-001",
  enabledTriggerIds: DEFAULT_TRIGGERS.map(t => t.id),
  maxEventQueueSize: 100,
  introspectionTimeoutMs: 30000,
  maxAutoCorrectionAttempts: 3,
  gbrainSyncEnabled: true,
  gbrainTimelinePrefix: "introspection"
};

// ============================================================================
// Agent 上下文
// ============================================================================

export interface AgentContext {
  /** Agent ID */
  agentId: string;
  /** Agent 角色 */
  role: AgentRole;
  /** 当前状态 */
  state: AgentState;
  /** 状态流转历史 */
  stateHistory: AgentStateTransition[];
  /** 关联的任务 ID（如果有） */
  taskId?: string;
  /** 当前自省结果（如果有） */
  currentIntrospection?: IntrospectionResult;
  /** 最后一次触发时间 */
  lastTriggerTime?: string;
  /** 失败计数 */
  failureCount: number;
  /** 成功计数 */
  successCount: number;
}
