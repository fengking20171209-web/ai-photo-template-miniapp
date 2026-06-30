/**
 * 多 Agent 编排框架 — 公共导出
 *
 * 模块结构:
 * src/agents/
 *   ├── index.ts              ← 本文件（公共 API）
 *   ├── types.ts              核心类型定义
 *   ├── eventBus.ts           事件总线
 *   ├── agentBase.ts          Agent 基类
 *   ├── coordinatorAgent.ts   Coordinator Agent
 *   ├── generatorAgent.ts     Generator Agent
 *   └── reviewerAgent.ts      Reviewer Agent
 */

// 类型导出
export type {
  AgentRole,
  AgentState,
  AgentMessage,
  MessageType,
  AgentContext,
  AgentExecutionResult,
  GBrainRuleContext,
  IntrospectionResult,
  TaskAssignment,
  CoordinatorState,
  EventFilter,
} from "./types.js";

// EventBus
export { EventBus, createEventBus } from "./eventBus.js";
export type { EventHandler } from "./eventBus.js";

// Agent 基类
export { Agent } from "./agentBase.js";
export type { AgentFactory } from "./agentBase.js";

// Coordinator Agent
export { CoordinatorAgent, createCoordinatorAgent } from "./coordinatorAgent.js";

// Generator Agent
export { GeneratorAgent, createGeneratorAgent } from "./generatorAgent.js";
export type { GeneratorAgentConfig } from "./generatorAgent.js";

// Reviewer Agent
export { ReviewerAgent, createReviewerAgent } from "./reviewerAgent.js";
export type {
  ReviewerAgentConfig,
  ReviewResult,
  PromptCheckResult,
  TemplateCheckResult,
} from "./reviewerAgent.js";

// 工具常量
export { AGENT_TERMINAL_STATES } from "./types.js";
