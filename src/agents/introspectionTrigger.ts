/**
 * IntrospectionTrigger — 自省触发器系统
 * 
 * 实现任务完成、失败、Prompt 质量评分等触发器的自动自省机制
 */

import { randomUUID } from "node:crypto";
import type {
  TriggerConfig,
  TriggerType,
  TriggerAction,
  IntrospectionResult,
  IntrospectionResultStatus,
  IntrospectionFinding,
  AgentContext,
  AgentRole,
  DEFAULT_TRIGGERS
} from "./types.js";
import type { ImageTask, GenerateTask } from "../types/task.js";
import { getGlobalEventBus } from "./eventBus.js";

// ============================================================================
// Prompt 质量评分器
// ============================================================================

export interface PromptQualityScore {
  /** 总体评分（0-100） */
  overallScore: number;
  /** 各维度评分 */
  dimensions: {
    clarity: number;      // 清晰度
    specificity: number;  // 具体性
    completeness: number; // 完整性
    style_consistency: number; // 风格一致性
    negative_prompt_quality: number; // 负向提示词质量
  };
  /** 评分说明 */
  explanation: string;
  /** 改进建议 */
  improvementSuggestions: string[];
}

/**
 * 基于规则对 Prompt 进行质量评分
 * 
 * 评分维度：
 * - 清晰度：Prompt 是否表达明确
 * - 具体性：细节描述是否充分
 * - 完整性：必要元素是否齐全
 * - 风格一致性：风格描述是否一致
 * - 负向提示词质量：负向提示词是否有效
 */
export function scorePromptQuality(prompt: string, negativePrompt?: string): PromptQualityScore {
  const dimensions = {
    clarity: scoreClarity(prompt),
    specificity: scoreSpecificity(prompt),
    completeness: scoreCompleteness(prompt),
    style_consistency: scoreStyleConsistency(prompt),
    negative_prompt_quality: negativePrompt ? scoreNegativePrompt(negativePrompt) : 0
  };

  // 加权计算总体评分
  const weights = {
    clarity: 0.25,
    specificity: 0.25,
    completeness: 0.20,
    style_consistency: 0.15,
    negative_prompt_quality: 0.15
  };

  const overallScore = Math.round(
    dimensions.clarity * weights.clarity +
    dimensions.specificity * weights.specificity +
    dimensions.completeness * weights.completeness +
    dimensions.style_consistency * weights.style_consistency +
    dimensions.negative_prompt_quality * weights.negative_prompt_quality
  );

  const improvementSuggestions = generateImprovementSuggestions(dimensions, prompt);

  return {
    overallScore,
    dimensions,
    explanation: generateExplanation(overallScore, dimensions),
    improvementSuggestions
  };
}

function scoreClarity(prompt: string): number {
  // 检查是否有明确的主体描述
  const hasSubject = /(?:person|character|subject|figure|portrait|face|body)/i.test(prompt);
  // 检查是否有动作或姿态描述
  const hasAction = /(?:standing|sitting|looking|wearing|holding|posing)/i.test(prompt);
  // 检查是否有环境描述
  const hasEnvironment = /(?:background|scene|setting|environment|atmosphere)/i.test(prompt);
  // 检查长度是否合理（太短可能不清晰）
  const reasonableLength = prompt.length >= 50;

  let score = 0;
  if (hasSubject) score += 25;
  if (hasAction) score += 25;
  if (hasEnvironment) score += 25;
  if (reasonableLength) score += 25;

  return score;
}

function scoreSpecificity(prompt: string): number {
  // 检查细节描述词汇
  const detailIndicators = [
    /(?:detailed|intricate|fine|precise|sharp)/i,
    /(?:texture|material|pattern|design)/i,
    /(?:lighting|shadow|illumination|glow)/i,
    /(?:color|hue|tone|palette)/i,
    /(?:expression|emotion|mood)/i
  ];

  let score = 0;
  detailIndicators.forEach(regex => {
    if (regex.test(prompt)) score += 20;
  });

  // 检查是否有具体数值或量化描述
  if (/\d+(?:px|%|kg|cm|inches?)/i.test(prompt)) score += 10;

  return Math.min(score, 100);
}

function scoreCompleteness(prompt: string): number {
  // 检查必要元素
  const checks = {
    subject: /(?:person|character|portrait|figure)/i.test(prompt),
    style: /(?:style|art|aesthetic|look|vibe)/i.test(prompt),
    composition: /(?:composition|framing|angle|perspective)/i.test(prompt),
    lighting: /(?:light|shadow|illumination|bright|dark)/i.test(prompt),
    quality: /(?:quality|resolution|detail|sharp|clear)/i.test(prompt)
  };

  const passed = Object.values(checks).filter(Boolean).length;
  return Math.round((passed / Object.keys(checks).length) * 100);
}

function scoreStyleConsistency(prompt: string): number {
  // 检查风格描述是否冲突
  const styleKeywords = prompt.toLowerCase().match(/(?:style|art|aesthetic|look|vibe|genre)/gi) || [];
  
  // 如果风格关键词过多（>3），可能存在冲突
  if (styleKeywords.length > 3) return 40;
  if (styleKeywords.length === 0) return 50;

  // 检查是否有明确的风格指向
  const explicitStyles = [
    'realistic', 'photorealistic', 'cinematic', 'anime', 'cartoon',
    'painting', 'oil painting', 'watercolor', 'sketch', 'digital art',
    'cyberpunk', 'steampunk', 'fantasy', 'sci-fi', 'noir', 'vintage'
  ];

  const hasExplicitStyle = explicitStyles.some(style => 
    new RegExp(style, 'i').test(prompt)
  );

  return hasExplicitStyle ? 90 : 70;
}

function scoreNegativePrompt(negativePrompt: string): number {
  if (!negativePrompt || negativePrompt.trim().length === 0) return 30;

  // 检查负向提示词是否包含常见负面元素
  const negativeIndicators = [
    /(?:blurry|blur|noise|grain|artifact)/i,
    /(?:deformed|distorted|bad anatomy|bad hands)/i,
    /(?:low quality|worst quality|ugly)/i,
    /(?:duplicate|extra limbs|extra fingers)/i,
    /(?:text|watermark|signature)/i
  ];

  let score = 0;
  negativeIndicators.forEach(regex => {
    if (regex.test(negativePrompt)) score += 20;
  });

  // 长度检查
  if (negativePrompt.length >= 30) score += 10;

  return Math.min(score, 100);
}

function generateExplanation(score: number, dimensions: PromptQualityScore["dimensions"]): string {
  if (score >= 85) {
    return `Prompt 质量优秀（${score}分）。各维度表现均衡，描述清晰具体，风格一致。`;
  } else if (score >= 70) {
    return `Prompt 质量良好（${score}分）。整体结构完整，但在${getWeakDimension(dimensions)}方面还有提升空间。`;
  } else if (score >= 50) {
    return `Prompt 质量一般（${score}分）。需要加强${getWeakDimension(dimensions)}等维度的描述。`;
  } else {
    return `Prompt 质量较低（${score}分）。建议大幅优化描述，特别是${getWeakDimension(dimensions)}。`;
  }
}

function getWeakDimension(dimensions: PromptQualityScore["dimensions"]): string {
  const sorted = Object.entries(dimensions)
    .sort((a, b) => a[1] - b[1]);
  return sorted[0][0].replace('_', ' ');
}

function generateImprovementSuggestions(
  dimensions: PromptQualityScore["dimensions"],
  prompt: string
): string[] {
  const suggestions: string[] = [];

  if (dimensions.clarity < 70) {
    suggestions.push("增加明确的主体描述，说明人物/场景的核心特征");
  }
  if (dimensions.specificity < 70) {
    suggestions.push("添加更多细节描述，如材质、光影、色彩等");
  }
  if (dimensions.completeness < 70) {
    suggestions.push("补充缺失的元素：风格、构图、光影、质量描述");
  }
  if (dimensions.style_consistency < 70) {
    suggestions.push("统一风格描述，避免使用相互冲突的艺术风格词汇");
  }
  if (dimensions.negative_prompt_quality < 50) {
    suggestions.push("优化负向提示词，包含常见的质量问题（模糊、变形、低质量等）");
  }

  if (suggestions.length === 0) {
    suggestions.push("Prompt 质量良好，可考虑添加个性化元素或实验性描述");
  }

  return suggestions;
}

// ============================================================================
// 自省触发器
// ============================================================================

export interface TriggerExecutionResult {
  /** 触发器 ID */
  triggerId: string;
  /** 是否触发 */
  triggered: boolean;
  /** 触发原因 */
  reason?: string;
  /** 执行的动作 */
  executedActions: TriggerAction[];
  /** 自省结果（如果触发了 introspect） */
  introspectionResult?: IntrospectionResult;
  /** 执行时间戳 */
  timestamp: string;
}

export class IntrospectionTrigger {
  private triggers: Map<string, TriggerConfig> = new Map();
  private lastTriggerTimes: Map<string, string> = new Map();
  private introspectorId: string;

  constructor(introspectorId: string = "introspector-001") {
    this.introspectorId = introspectorId;
    // 初始化默认触发器
    for (const trigger of DEFAULT_TRIGGERS) {
      this.triggers.set(trigger.id, trigger);
    }
  }

  /** 注册自定义触发器 */
  registerTrigger(config: TriggerConfig): void {
    this.triggers.set(config.id, config);
  }

  /** 启用/禁用触发器 */
  setTriggerEnabled(triggerId: string, enabled: boolean): void {
    const trigger = this.triggers.get(triggerId);
    if (trigger) {
      trigger.enabled = enabled;
    }
  }

  /** 获取所有触发器 */
  getAllTriggers(): TriggerConfig[] {
    return Array.from(this.triggers.values());
  }

  /** 评估任务完成触发器 */
  evaluateTaskCompleted(task: ImageTask | GenerateTask): TriggerExecutionResult {
    return this.evaluateTrigger("auto-self-approving", {
      task,
      conditionMet: task.status === "completed"
    });
  }

  /** 评估任务失败触发器 */
  evaluateTaskFailed(task: ImageTask | GenerateTask, error?: Error): TriggerExecutionResult {
    return this.evaluateTrigger("failure-introspection", {
      task,
      error,
      conditionMet: task.status === "failed" || !!error
    });
  }

  /** 评估 Prompt 质量触发器 */
  evaluatePromptQuality(
    prompt: string,
    negativePrompt?: string,
    threshold: number = 70
  ): TriggerExecutionResult {
    const score = scorePromptQuality(prompt, negativePrompt);
    const conditionMet = score.overallScore < threshold;

    return this.evaluateTrigger("prompt-quality-check", {
      prompt,
      negativePrompt,
      qualityScore: score,
      threshold,
      conditionMet
    });
  }

  /** 通用触发器评估 */
  private evaluateTrigger(
    triggerId: string,
    context: Record<string, unknown>
  ): TriggerExecutionResult {
    const trigger = this.triggers.get(triggerId);
    if (!trigger || !trigger.enabled) {
      return {
        triggerId,
        triggered: false,
        executedActions: [],
        timestamp: new Date().toISOString()
      };
    }

    // 检查冷却时间
    const lastTriggerTime = this.lastTriggerTimes.get(triggerId);
    if (lastTriggerTime) {
      const lastTime = new Date(lastTriggerTime).getTime();
      const now = Date.now();
      if (now - lastTime < trigger.cooldownMs) {
        return {
          triggerId,
          triggered: false,
          reason: `冷却中，距离上次触发还有 ${trigger.cooldownMs - (now - lastTime)}ms`,
          executedActions: [],
          timestamp: new Date().toISOString()
        };
      }
    }

    const conditionMet = context.conditionMet as boolean;
    if (!conditionMet) {
      return {
        triggerId,
        triggered: false,
        reason: `条件不满足: ${trigger.condition}`,
        executedActions: [],
        timestamp: new Date().toISOString()
      };
    }

    // 记录触发时间
    this.lastTriggerTimes.set(triggerId, new Date().toISOString());

    // 执行触发动作
    const executedActions: TriggerAction[] = [];
    let introspectionResult: IntrospectionResult | undefined;

    for (const action of trigger.actions) {
      switch (action) {
        case "introspect":
          introspectionResult = this.performIntrospection(trigger, context);
          executedActions.push(action);
          break;
        case "notify":
          // 通过 EventBus 通知
          this.notifyCoordinator(trigger, context, introspectionResult);
          executedActions.push(action);
          break;
        case "sync_to_gbrain":
          // GBrain 同步将在 Coordinator 中处理
          executedActions.push(action);
          break;
        case "correct":
          // 自动修正将在 Coordinator 中处理
          executedActions.push(action);
          break;
        case "rollback":
          executedActions.push(action);
          break;
      }
    }

    return {
      triggerId,
      triggered: true,
      reason: `条件满足: ${trigger.condition}`,
      executedActions,
      introspectionResult,
      timestamp: new Date().toISOString()
    };
  }

  /** 执行自省分析 */
  private performIntrospection(
    trigger: TriggerConfig,
    context: Record<string, unknown>
  ): IntrospectionResult {
    const startTime = Date.now();
    const findings: IntrospectionFinding[] = [];
    const correctionSuggestions: string[] = [];

    const task = context.task as ImageTask | GenerateTask | undefined;
    const qualityScore = context.qualityScore as PromptQualityScore | undefined;
    const error = context.error as Error | undefined;

    // 分析任务状态
    if (task) {
      if (task.status === "failed" || error) {
        findings.push({
          description: error?.message || "任务执行失败",
          severity: "high",
          category: "parameter_error",
          suggestedCorrection: "检查参数配置和 API 连接"
        });
      }

      if (task.image_response?.raw?.fallback) {
        findings.push({
          description: "使用了降级/备用生成方案",
          severity: "medium",
          category: "output_quality",
          suggestedCorrection: "检查主生成服务可用性，考虑优化请求参数"
        });
      }
    }

    // 分析 Prompt 质量
    if (qualityScore) {
      if (qualityScore.overallScore < 70) {
        findings.push({
          description: `Prompt 质量评分较低（${qualityScore.overallScore}分）`,
          severity: qualityScore.overallScore < 50 ? "high" : "medium",
          category: "prompt_quality",
          suggestedCorrection: qualityScore.improvementSuggestions[0]
        });
        correctionSuggestions.push(...qualityScore.improvementSuggestions);
      }
    }

    // 生成自省结果
    const status = this.determineIntrospectionStatus(findings);

    return {
      introspectionId: randomUUID(),
      taskId: task?.task_id || "unknown",
      status,
      timestamp: new Date().toISOString(),
      findings,
      correctionSuggestions,
      suggestRollback: status === "rollback_needed",
      durationMs: Date.now() - startTime,
      introspectorId: this.introspectorId,
      taskSnapshot: task ? this.createTaskSnapshot(task) : undefined
    };
  }

  /** 确定自省结果状态 */
  private determineIntrospectionStatus(findings: IntrospectionFinding[]): IntrospectionResultStatus {
    if (findings.length === 0) {
      return "passed";
    }

    const criticalFindings = findings.filter(f => f.severity === "critical");
    const highFindings = findings.filter(f => f.severity === "high");

    if (criticalFindings.length > 0) {
      return "rollback_needed";
    }

    if (highFindings.length > 0) {
      return "needs_correction";
    }

    const mediumFindings = findings.filter(f => f.severity === "medium");
    if (mediumFindings.length > 2) {
      return "needs_review";
    }

    return "needs_correction";
  }

  /** 创建任务快照（用于回滚） */
  private createTaskSnapshot(task: ImageTask | GenerateTask): Partial<ImageTask | GenerateTask> {
    return {
      task_id: task.task_id,
      status: task.status,
      created_at: task.created_at,
      updated_at: "updated_at" in task ? task.updated_at : undefined,
      template: task.template,
      prompt_file: "prompt_file" in task ? task.prompt_file : undefined,
      image_request: task.image_request
    };
  }

  /** 通知 Coordinator */
  private notifyCoordinator(
    trigger: TriggerConfig,
    context: Record<string, unknown>,
    introspectionResult?: IntrospectionResult
  ): void {
    const eventBus = getGlobalEventBus();
    eventBus.publish({
      type: "trigger_fired",
      sourceAgent: this.introspectorId,
      targetAgent: "coordinator",
      payload: {
        triggerId: trigger.id,
        triggerType: trigger.type,
        context,
        introspectionResult
      },
      priority: trigger.priority
    });
  }
}

/** 创建默认自省触发器实例 */
export function createIntrospectionTrigger(): IntrospectionTrigger {
  return new IntrospectionTrigger();
}
