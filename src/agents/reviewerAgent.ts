/**
 * Reviewer Agent — Prompt 质量校验和模板合规检查
 *
 * 职责：
 * 1. 校验 prompt 质量（完整性、合规性、可读性）
 * 2. 校验模板合规性（必填字段、分类合法性、负面提示）
 * 3. 输出审查报告和修改建议
 * 4. 遵循 gbrainFirst 和 recordEverything 规则
 */

import { Agent } from "./agentBase.js";
import type {
  AgentContext,
  AgentExecutionResult,
  IntrospectionResult,
} from "./types.js";
import { EventBus } from "./eventBus.js";
import type { ImageTemplate } from "../types/template.js";
import { parseTemplate } from "../templates/templateSchema.js";
import { TemplateRepository } from "../templates/templateRepository.js";
import type { AppConfig } from "../config/appConfig.js";

// ──────────────────────────────────────────
// 审查结果类型
// ──────────────────────────────────────────

export interface ReviewResult {
  passed: boolean;
  score: number; // 0-100
  promptChecks: PromptCheckResult[];
  templateChecks: TemplateCheckResult[];
  issues: string[];
  recommendations: string[];
  timestamp: string;
}

export interface PromptCheckResult {
  check: string;
  passed: boolean;
  score: number;
  message: string;
}

export interface TemplateCheckResult {
  check: string;
  passed: boolean;
  score: number;
  message: string;
}

// ──────────────────────────────────────────
// Reviewer 配置
// ──────────────────────────────────────────

export interface ReviewerAgentConfig {
  /** 最低通过分数 */
  minPassScore: number;
  /** 是否启用严格模式（任何单项检查失败即整体失败） */
  strictMode: boolean;
  /** 自定义检查项（可选） */
  customChecks?: Array<{
    name: string;
    fn: (prompt: string, template?: ImageTemplate) => PromptCheckResult;
  }>;
}

// ──────────────────────────────────────────
// Reviewer Agent
// ──────────────────────────────────────────

export class ReviewerAgent extends Agent {
  private config: ReviewerAgentConfig;

  constructor(
    id: string,
    eventBus: EventBus,
    config?: Partial<ReviewerAgentConfig>
  ) {
    super(id, "reviewer", eventBus);
    this.config = {
      minPassScore: 70,
      strictMode: false,
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
      // ── gbrainFirst: 执行前查询 GBrain 获取历史审查记录/模板参考 ──
      const searchQuery = context.template?.template_id
        ? `review:${context.template.template_id}`
        : "prompt-review-history";

      await this.gbrainFirst(context, searchQuery);

      // ── 执行审查 ──
      const reviewResult = await this._review(context);

      // 发布审查结果事件
      await this.eventBus.emit(
        this.eventBus.createMessage(
          this.id,
          "prompt_reviewed",
          {
            taskId: context.taskId ?? "unknown",
            passed: reviewResult.passed,
            score: reviewResult.score,
            issuesCount: reviewResult.issues.length,
          },
          { taskId: context.taskId, role: "reviewer" }
        )
      );

      // ── recordEverything: 记录审查结果到 GBrain ──
      if (context.gbrainEnabled) {
        const recordSlug = `reviewer/${context.taskId ?? "unknown"}/review`;
        const recordContent = JSON.stringify(
          {
            agent: this.id,
            role: this.role,
            timestamp: new Date().toISOString(),
            passed: reviewResult.passed,
            score: reviewResult.score,
            issues: reviewResult.issues,
            recommendations: reviewResult.recommendations,
            promptChecks: reviewResult.promptChecks,
            templateChecks: reviewResult.templateChecks,
          },
          null,
          2
        );
        await this.record(context, recordSlug, recordContent);
        await this.sync(context);
      }

      await this.setState(reviewResult.passed ? "approved" : "rejected", context);

      return {
        success: reviewResult.passed,
        state: reviewResult.passed ? "approved" : "rejected",
        output: reviewResult,
        metadata: {
          score: reviewResult.score,
          issuesCount: reviewResult.issues.length,
        },
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      await this.setState("error", context);

      return {
        success: false,
        state: "error",
        error: errorMessage,
        metadata: {},
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
      score: result.success ? 100 : 50,
      issues: result.error ? [result.error] : [],
      recommendations: [],
      timestamp: new Date().toISOString(),
      agentRole: this.role,
    };

    if (!result.success) {
      introspection.recommendations.push(
        "审查失败，检查审查逻辑是否过于严格或模板文件是否有问题"
      );
    }

    // 检查规则遵守情况
    if (!context.ruleContext.gbrainQueried && context.gbrainEnabled) {
      introspection.issues.push("违反 gbrainFirst 规则：审查前未查询 GBrain");
      introspection.score = Math.max(0, introspection.score - 15);
    }

    if (!context.ruleContext.recordSubmitted && context.gbrainEnabled) {
      introspection.issues.push("违反 recordEverything 规则：未记录审查结果到 GBrain");
      introspection.score = Math.max(0, introspection.score - 10);
    }

    introspection.passed = introspection.score >= 70;

    await this.selfApprove(context, introspection);

    return introspection;
  }

  // ──────────────────────────────────────────
  // 审查逻辑
  // ──────────────────────────────────────────

  /**
   * 执行完整审查流程
   */
  private async _review(context: AgentContext): Promise<ReviewResult> {
    const promptChecks: PromptCheckResult[] = [];
    const templateChecks: TemplateCheckResult[] = [];
    const issues: string[] = [];
    const recommendations: string[] = [];

    // ── 读取 prompt 文件 ──
    let promptText = "";
    let template: ImageTemplate | undefined = context.template;

    if (context.metadata?.promptFile) {
      const fs = await import("node:fs");
      try {
        promptText = fs.readFileSync(context.metadata.promptFile as string, "utf-8");
      } catch {
        // prompt 文件不存在，尝试从 context 获取
      }
    }

    // ── 如果 context 中有 template，加载并审查 ──
    if (context.template) {
      template = context.template;
    } else if (context.metadata?.templateId) {
      // 尝试从模板仓库加载
      try {
        const repo = new TemplateRepository(context.config.templatesDir);
        template = repo.load(context.metadata.templateId as string);
      } catch {
        // 模板不存在
      }
    }

    // ── Prompt 质量检查 ──
    promptChecks.push(this._checkPromptLength(promptText));
    promptChecks.push(this._checkPromptStructure(promptText));
    promptChecks.push(this._checkPromptCompleteness(promptText));
    promptChecks.push(this._checkPromptSafety(promptText));
    promptChecks.push(this._checkPromptLanguage(promptText));

    // 自定义检查
    if (this.config.customChecks) {
      for (const customCheck of this.config.customChecks) {
        promptChecks.push(customCheck.fn(promptText, template));
      }
    }

    // ── 模板合规检查 ──
    if (template) {
      templateChecks.push(this._checkTemplateRequiredFields(template));
      templateChecks.push(this._checkTemplateCategory(template));
      templateChecks.push(this._checkTemplateOptions(template));
      templateChecks.push(this._checkTemplateNegativePrompt(template));
    } else {
      templateChecks.push({
        check: "template_exists",
        passed: false,
        score: 0,
        message: "未找到模板，无法进行模板合规检查",
      });
    }

    // ── 汇总 ──
    const allChecks = [...promptChecks, ...templateChecks];
    const totalScore = allChecks.reduce((sum, c) => sum + c.score, 0);
    const maxScore = allChecks.length * 20; // 每项满分 20
    const score = Math.round((totalScore / maxScore) * 100);

    const failedChecks = allChecks.filter((c) => !c.passed);
    for (const check of failedChecks) {
      issues.push(`[${check.check}] ${check.message}`);
    }

    // 生成建议
    if (score < 100) {
      recommendations.push(
        `当前得分 ${score}/100，建议优化以下方面：`
      );
      for (const check of failedChecks) {
        recommendations.push(`  - ${check.message}`);
      }
    }

    if (promptText.length < 100) {
      recommendations.push("prompt 过短，建议增加细节描述");
    }

    const passed =
      score >= this.config.minPassScore &&
      (!this.config.strictMode || failedChecks.length === 0);

    return {
      passed,
      score,
      promptChecks,
      templateChecks,
      issues,
      recommendations,
      timestamp: new Date().toISOString(),
    };
  }

  // ──────────────────────────────────────────
  // 单项检查
  // ──────────────────────────────────────────

  private _checkPromptLength(prompt: string): PromptCheckResult {
    const len = prompt.length;
    if (len >= 300) {
      return { check: "prompt_length", passed: true, score: 20, message: "Prompt 长度充足" };
    }
    if (len >= 150) {
      return { check: "prompt_length", passed: true, score: 15, message: `Prompt 长度偏短 (${len} 字符)` };
    }
    return { check: "prompt_length", passed: false, score: 5, message: `Prompt 过短 (${len} 字符)，建议至少 150 字符` };
  }

  private _checkPromptStructure(prompt: string): PromptCheckResult {
    const requiredSections = [
      "模板名称",
      "分类",
      "画幅",
      "风格",
      "生成目标",
      "脸部保真",
      "服装造型",
      "场景环境",
      "光影氛围",
      "镜头构图",
      "画质要求",
    ];

    const missing = requiredSections.filter((section) => !prompt.includes(`【${section}】`));
    if (missing.length === 0) {
      return { check: "prompt_structure", passed: true, score: 20, message: "Prompt 结构完整" };
    }
    if (missing.length <= 2) {
      return {
        check: "prompt_structure",
        passed: true,
        score: 15,
        message: `缺少 ${missing.length} 个章节: ${missing.join(", ")}`,
      };
    }
    return {
      check: "prompt_structure",
      passed: false,
      score: 5,
      message: `缺少 ${missing.length} 个关键章节: ${missing.join(", ")}`,
    };
  }

  private _checkPromptCompleteness(prompt: string): PromptCheckResult {
    const keywords = [
      "prompt",
      "negative",
      "ratio",
      "quality",
      "face",
    ];
    const found = keywords.filter((kw) => prompt.toLowerCase().includes(kw.toLowerCase()));
    const ratio = found.length / keywords.length;

    if (ratio === 1) {
      return { check: "prompt_completeness", passed: true, score: 20, message: "Prompt 内容完整" };
    }
    if (ratio >= 0.6) {
      return { check: "prompt_completeness", passed: true, score: 15, message: `缺少部分关键词 (${found.length}/${keywords.length})` };
    }
    return { check: "prompt_completeness", passed: false, score: 5, message: `关键词覆盖率低 (${found.length}/${keywords.length})` };
  }

  private _checkPromptSafety(prompt: string): PromptCheckResult {
    const unsafeKeywords = [
      "nude",
      "naked",
      "porn",
      "explicit",
      "nsfw",
      "裸露",
      "色情",
      "低俗",
    ];

    const found = unsafeKeywords.filter((kw) =>
      prompt.toLowerCase().includes(kw.toLowerCase())
    );

    // 检查是否有安全声明
    const hasSafetyDeclaration =
      prompt.includes("安全") ||
      prompt.includes("不要过度磨皮") ||
      prompt.includes("不要低俗") ||
      prompt.includes("不要裸露");

    if (found.length === 0 && hasSafetyDeclaration) {
      return { check: "prompt_safety", passed: true, score: 20, message: "Prompt 安全合规" };
    }
    if (found.length === 0) {
      return { check: "prompt_safety", passed: true, score: 15, message: "Prompt 无敏感词，但缺少安全声明" };
    }
    return {
      check: "prompt_safety",
      passed: false,
      score: 0,
      message: `发现敏感词: ${found.join(", ")}`,
    };
  }

  private _checkPromptLanguage(prompt: string): PromptCheckResult {
    // 检查是否有中英文混合（AI 绘画 prompt 通常中英文混合更优）
    const hasChinese = /[\u4e00-\u9fff]/.test(prompt);
    const hasEnglish = /[a-zA-Z]/.test(prompt);

    if (hasChinese && hasEnglish) {
      return { check: "prompt_language", passed: true, score: 20, message: "中英文混合，适合 AI 绘画" };
    }
    if (hasChinese) {
      return { check: "prompt_language", passed: true, score: 15, message: "仅中文，建议补充英文关键词" };
    }
    if (hasEnglish) {
      return { check: "prompt_language", passed: true, score: 15, message: "仅英文，建议补充中文说明" };
    }
    return { check: "prompt_language", passed: false, score: 5, message: "无有效语言内容" };
  }

  private _checkTemplateRequiredFields(template: ImageTemplate): TemplateCheckResult {
    const requiredFields: Array<keyof ImageTemplate> = [
      "template_id",
      "category",
      "title",
      "version",
      "ratio",
      "style",
    ];

    const missing = requiredFields.filter((field) => !template[field]);
    if (missing.length === 0) {
      return { check: "template_required_fields", passed: true, score: 20, message: "模板必填字段完整" };
    }
    return {
      check: "template_required_fields",
      passed: false,
      score: 0,
      message: `缺少必填字段: ${missing.join(", ")}`,
    };
  }

  private _checkTemplateCategory(template: ImageTemplate): TemplateCheckResult {
    const allowedCategories = [
      "古风美女",
      "职业形象",
      "形象分析",
      "漫画角色",
      "产品海报",
      "模特大赛",
      "新中式概念",
      "肚兜现代时装",
      "SIUF 2026 内衣秀",
      "人像写真",
      "幻系插画",
    ];

    if (allowedCategories.includes(template.category)) {
      return { check: "template_category", passed: true, score: 20, message: `分类合法: ${template.category}` };
    }
    return {
      check: "template_category",
      passed: false,
      score: 0,
      message: `非法分类: ${template.category}`,
    };
  }

  private _checkTemplateOptions(template: ImageTemplate): TemplateCheckResult {
    const issues: string[] = [];

    if (template.options.quality !== "draft" && template.options.quality !== "standard" && template.options.quality !== "high") {
      issues.push(`非法 quality: ${template.options.quality}`);
    }
    if (template.options.face_strength < 0 || template.options.face_strength > 1) {
      issues.push(`face_strength 超出范围 [0,1]: ${template.options.face_strength}`);
    }
    if (template.options.output_count < 1 || template.options.output_count > 9) {
      issues.push(`output_count 超出范围 [1,9]: ${template.options.output_count}`);
    }

    if (issues.length === 0) {
      return { check: "template_options", passed: true, score: 20, message: "模板选项配置合法" };
    }
    return {
      check: "template_options",
      passed: false,
      score: 5,
      message: issues.join("; "),
    };
  }

  private _checkTemplateNegativePrompt(template: ImageTemplate): TemplateCheckResult {
    if (!template.negative_prompt || template.negative_prompt.length === 0) {
      return {
        check: "template_negative_prompt",
        passed: false,
        score: 5,
        message: "缺少负面提示（negative_prompt），建议添加以控制生成质量",
      };
    }
    if (template.negative_prompt.length >= 3) {
      return { check: "template_negative_prompt", passed: true, score: 20, message: `负面提示充足 (${template.negative_prompt.length} 项)` };
    }
    return {
      check: "template_negative_prompt",
      passed: true,
      score: 15,
      message: `负面提示较少 (${template.negative_prompt.length} 项)，建议补充`,
    };
  }

  /**
   * 直接审查一个 prompt 字符串（不依赖上下文）
   */
  async reviewPrompt(prompt: string, template?: ImageTemplate): Promise<ReviewResult> {
    const mockContext: AgentContext = {
      config: {} as AppConfig,
      gbrainEnabled: false,
      ruleContext: {
        gbrainQueried: true,
        recordSubmitted: false,
        syncTriggered: false,
        selfApproved: false,
      },
      state: "working",
      template,
      metadata: { promptFile: undefined },
    };

    // 临时覆盖 _review 中的 promptText
    const result = await this._review(mockContext);
    // 用传入的 prompt 覆盖
    result.promptChecks = [
      this._checkPromptLength(prompt),
      this._checkPromptStructure(prompt),
      this._checkPromptCompleteness(prompt),
      this._checkPromptSafety(prompt),
      this._checkPromptLanguage(prompt),
    ];

    const allChecks = [...result.promptChecks, ...result.templateChecks];
    const totalScore = allChecks.reduce((sum, c) => sum + c.score, 0);
    const maxScore = allChecks.length * 20;
    result.score = Math.round((totalScore / maxScore) * 100);
    result.passed = result.score >= this.config.minPassScore;

    return result;
  }
}

/**
 * 创建 Reviewer Agent
 */
export function createReviewerAgent(
  id: string = "reviewer-1",
  eventBus?: EventBus,
  config?: Partial<ReviewerAgentConfig>
): ReviewerAgent {
  const bus = eventBus ?? new EventBus();
  return new ReviewerAgent(id, bus, config);
}
