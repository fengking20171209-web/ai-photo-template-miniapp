/**
 * GBrain 工作流集成模块
 *
 * 实现 pi-agent.md 5 条集成规则：
 * - gbrainFirst: 任务开始前查询 GBrain 获取参考
 * - recordEverything: 记录任务决策到 GBrain
 * - syncAfterWrite: 写入后触发同步
 * - selfApproving: 任务完成后触发自省（预留接口）
 * - autoSelfApproving: 自动自省（预留接口）
 */

import type { GBrainClient } from "./gbrainClient.js";
import type { AppConfig } from "../config/appConfig.js";
import type { ImageTemplate } from "../types/template.js";

/** GBrain 客户端可能为 null（降级模式） */
export type GBrainClientOrNull = GBrainClient | null;

export interface GBrainSearchContext {
  /** GBrain 搜索返回的相关模板 ID */
  relatedTemplateIds: string[];
  /** GBrain 搜索返回的相关 prompt 片段 */
  relatedPrompts: string[];
  /** 搜索查询原文 */
  query: string;
  /** 搜索返回的总结果数 */
  totalResults: number;
}

export interface TaskDecisionRecord {
  task_id: string;
  template_id: string;
  decision_type: "prompt_generated" | "image_requested" | "fallback_used" | "error_handled";
  timestamp: string;
  details: Record<string, unknown>;
}

/**
 * gbrainFirst: 在任务开始前查询 GBrain 搜索相关模板和 prompt
 * 降级策略：gbrainEnabled=false 或 GBrain 不可达时，返回空上下文，不中断主流程
 */
export async function gbrainFirst(
  client: GBrainClientOrNull,
  templateId: string,
  config: AppConfig
): Promise<GBrainSearchContext> {
  if (!config.gbrainEnabled || !client) {
    return {
      relatedTemplateIds: [],
      relatedPrompts: [],
      query: `template:${templateId}`,
      totalResults: 0
    };
  }

  try {
    // 搜索相关模板
    const searchResult = await client.search(`template:${templateId} OR prompt:${templateId}`);

    const relatedTemplateIds = searchResult.items
      .filter((item) => item.category === "template" || item.slug.includes("template"))
      .map((item) => item.slug)
      .slice(0, 5);

    const relatedPrompts = searchResult.items
      .filter((item) => item.category === "prompt" || item.content.includes("prompt"))
      .map((item) => item.content.slice(0, 200))
      .slice(0, 3);

    return {
      relatedTemplateIds,
      relatedPrompts,
      query: `template:${templateId}`,
      totalResults: searchResult.total
    };
  } catch (error) {
    // GBrain 不可达时降级为本地模式，不中断主流程
    console.warn(`[GBrain] gbrainFirst 查询失败，降级为本地模式: ${error instanceof Error ? error.message : String(error)}`);
    return {
      relatedTemplateIds: [],
      relatedPrompts: [],
      query: `template:${templateId}`,
      totalResults: 0
    };
  }
}

/**
 * recordEverything: 记录任务决策到 GBrain
 * 降级策略：gbrainEnabled=false 或 GBrain 不可达时，仅本地记录日志，不中断主流程
 */
export async function recordEverything(
  client: GBrainClientOrNull,
  decision: TaskDecisionRecord,
  config: AppConfig
): Promise<void> {
  if (!config.gbrainEnabled || !client) {
    // 本地降级记录
    console.log(`[GBrain] recordEverything (本地模式): ${decision.decision_type} - ${decision.task_id}`);
    return;
  }

  try {
    // 写入决策记录到 GBrain
    const slug = `task/${decision.task_id}/${decision.decision_type}`;
    const content = JSON.stringify(decision, null, 2);
    await client.putPage(slug, content);

    // 添加时间线
    await client.addTimeline(`task/${decision.task_id}`, decision.decision_type);
  } catch (error) {
    // GBrain 不可达时降级，不中断主流程
    console.warn(`[GBrain] recordEverything 失败，本地记录: ${error instanceof Error ? error.message : String(error)}`);
    console.log(`[GBrain] 决策记录 (本地): ${JSON.stringify(decision)}`);
  }
}

/**
 * syncAfterWrite: 写入操作后触发 GBrain 索引同步
 * 降级策略：gbrainEnabled=false 或 GBrain 不可达时，跳过同步，不中断主流程
 */
export async function syncAfterWrite(
  client: GBrainClientOrNull,
  config: AppConfig
): Promise<void> {
  if (!config.gbrainEnabled || !client) {
    return;
  }

  try {
    await client.sync();
  } catch (error) {
    // GBrain 不可达时降级，不中断主流程
    console.warn(`[GBrain] syncAfterWrite 失败: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * 创建 GBrain 客户端（从 AppConfig 读取配置）
 */
export function createGBrainClientFromConfig(config: AppConfig): GBrainClient | null {
  if (!config.gbrainEnabled || !config.gbrainApiUrl) {
    return null;
  }

  // 动态导入避免循环依赖
  const { GBrainClient } = require("./gbrainClient.js");
  return new GBrainClient({
    baseUrl: config.gbrainApiUrl,
    timeoutMs: config.gbrainTimeoutMs
  });
}

/**
 * 获取 GBrain 客户端（可能为 null，表示降级模式）
 */
export function getGBrainClient(config: AppConfig): GBrainClientOrNull {
  return createGBrainClientFromConfig(config);
}