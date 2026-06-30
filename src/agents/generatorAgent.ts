/**
 * Generator Agent — 集成现有工作流
 *
 * 职责：
 * 1. 调用 generatePromptWorkflow 生成 prompt
 * 2. 调用 runImageTaskWorkflow 执行图像生成任务
 * 3. 遵循 gbrainFirst 和 recordEverything 规则
 */

import { Agent } from "./agentBase.js";
import type {
  AgentContext,
  AgentExecutionResult,
  IntrospectionResult,
} from "./types.js";
import { EventBus } from "./eventBus.js";
import { generatePromptWorkflow } from "../workflows/generatePromptWorkflow.js";
import { runImageTaskWorkflow } from "../workflows/runImageTaskWorkflow.js";
import type { GeneratePromptResult } from "../workflows/generatePromptWorkflow.js";
import type { RunImageTaskResult } from "../workflows/runImageTaskWorkflow.js";

export interface GeneratorAgentConfig {
  /** 是否执行图像生成（true = 完整流程，false = 仅生成 prompt） */
  fullPipeline: boolean;
  /** 默认模板 ID（当 context 中没有 template 时使用） */
  defaultTemplateId?: string;
}

export class GeneratorAgent extends Agent {
  private config: GeneratorAgentConfig;

  constructor(
    id: string,
    eventBus: EventBus,
    config?: Partial<GeneratorAgentConfig>
  ) {
    super(id, "generator", eventBus);
    this.config = {
      fullPipeline: true,
      defaultTemplateId: undefined,
      ...config,
    };
  }

  // ──────────────────────────────────────────
  // Agent 基类实现
  // ──────────────────────────────────────────

  async execute(context: AgentContext): Promise<AgentExecutionResult> {
    await this.setState("working", context);
    this.resetRuleContext();

    try {
      // ── gbrainFirst: 执行前查询 GBrain ──
      const searchQuery = context.template?.template_id
        ? `template:${context.template.template_id}`
        : this.config.defaultTemplateId
          ? `template:${this.config.defaultTemplateId}`
          : "image-template";

      const gbrainResult = await this.gbrainFirst(context, searchQuery);

      // ── 执行工作流 ──
      let promptResult: GeneratePromptResult | null = null;
      let imageResult: RunImageTaskResult | null = null;

      // 1. 生成 prompt
      const templateId =
        context.template?.template_id ?? this.config.defaultTemplateId;
      if (!templateId) {
        throw new Error(
          "Generator: no template_id available in context or config"
        );
      }

      promptResult = generatePromptWorkflow(context.config, templateId);
      context.metadata.promptGenerated = true;
      context.metadata.promptFile = promptResult.promptFile;

      this._log("generate_prompt", {
        taskId: promptResult.task.task_id,
        templateId,
        promptFile: promptResult.promptFile,
      });

      // 发布 prompt 生成事件
      await this.eventBus.emit(
        this.eventBus.createMessage(
          this.id,
          "prompt_generated",
          {
            taskId: promptResult.task.task_id,
            templateId,
            promptPreview: promptResult.prompt.slice(0, 200),
            promptFile: promptResult.promptFile,
          },
          { taskId: context.taskId ?? promptResult.task.task_id, role: "generator" }
        )
      );

      // 2. 执行图像生成（如果启用完整流程）
      if (this.config.fullPipeline) {
        imageResult = await runImageTaskWorkflow(context.config, templateId);
        context.metadata.imageGenerated = true;
        context.metadata.resultFile = imageResult.resultFile;

        this._log("run_image_task", {
          taskId: imageResult.task.task_id,
          status: imageResult.task.status,
          resultFile: imageResult.resultFile,
        });

        // 发布图像任务完成事件
        await this.eventBus.emit(
          this.eventBus.createMessage(
            this.id,
            "task_completed",
            {
              taskId: imageResult.task.task_id,
              status: imageResult.task.status,
              resultFile: imageResult.resultFile,
            },
            { taskId: context.taskId ?? imageResult.task.task_id, role: "generator" }
          )
        );
      }

      // ── recordEverything: 记录决策到 GBrain ──
      if (context.gbrainEnabled) {
        const taskId = context.taskId ?? promptResult?.task.task_id ?? "unknown";
        const recordSlug = `generator/${taskId}/execution`;
        const recordContent = JSON.stringify(
          {
            agent: this.id,
            role: this.role,
            timestamp: new Date().toISOString(),
            templateId,
            promptFile: promptResult?.promptFile,
            resultFile: imageResult?.resultFile,
            taskStatus: imageResult?.task.status ?? promptResult?.task.status,
            gbrainSearched: !!gbrainResult,
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
        output: {
          promptResult,
          imageResult,
        },
        metadata: {
          ...context.metadata,
          templateId,
          fullPipeline: this.config.fullPipeline,
        },
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      await this.setState("error", context);

      return {
        success: false,
        state: "error",
        error: errorMessage,
        metadata: context.metadata,
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

    if (!result.success) {
      introspection.recommendations.push(
        "生成失败，检查模板文件是否存在、promptBuilder 是否正常"
      );
    }

    // 检查 gbrainFirst 规则是否遵守
    if (!context.ruleContext.gbrainQueried && context.gbrainEnabled) {
      introspection.issues.push("违反 gbrainFirst 规则：执行前未查询 GBrain");
      introspection.score = Math.max(0, introspection.score - 20);
    }

    // 检查 recordEverything 规则是否遵守
    if (!context.ruleContext.recordSubmitted && context.gbrainEnabled) {
      introspection.issues.push("违反 recordEverything 规则：未记录决策到 GBrain");
      introspection.score = Math.max(0, introspection.score - 15);
    }

    introspection.passed = introspection.score >= 70;

    await this.selfApprove(context, introspection);

    return introspection;
  }

  /**
   * 仅生成 prompt（不执行图像生成）
   */
  async generatePromptOnly(context: AgentContext): Promise<GeneratePromptResult> {
    const prevFullPipeline = this.config.fullPipeline;
    this.config.fullPipeline = false;
    try {
      const result = await this.execute(context);
      if (!result.success || !result.output?.promptResult) {
        throw new Error(result.error ?? "Prompt generation failed");
      }
      return result.output.promptResult;
    } finally {
      this.config.fullPipeline = prevFullPipeline;
    }
  }

  /**
   * 设置默认模板 ID
   */
  setDefaultTemplateId(templateId: string): void {
    this.config.defaultTemplateId = templateId;
  }
}

/**
 * 创建 Generator Agent
 */
export function createGeneratorAgent(
  id: string = "generator-1",
  eventBus?: EventBus,
  config?: Partial<GeneratorAgentConfig>
): GeneratorAgent {
  const bus = eventBus ?? new EventBus();
  return new GeneratorAgent(id, bus, config);
}
