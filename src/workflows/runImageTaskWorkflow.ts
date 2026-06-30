import fs from "node:fs";
import path from "node:path";
import type { AppConfig } from "../config/appConfig.js";
import {
  createReservedImageRequest,
  HttpImageGenerationProvider,
  MockImageGenerationProvider
} from "../services/aiImageService.js";
import { buildPrompt } from "../services/promptBuilder.js";
import { TemplateRepository } from "../templates/templateRepository.js";
import type { ImageTask } from "../types/task.js";
import { gbrainFirst, recordEverything, syncAfterWrite, getGBrainClient } from "../services/gbrainIntegration.js";

export interface RunImageTaskResult {
  task: ImageTask;
  prompt: string;
  promptFile: string;
  resultFile: string;
}

export async function runImageTaskWorkflow(config: AppConfig, templateId: string): Promise<RunImageTaskResult> {
  // gbrainEnabled 条件判断：未配置时降级为本地模式
  const gbrainClient = getGBrainClient(config);

  // gbrainFirst: 任务开始前查询 GBrain 获取参考
  const gbrainContext = await gbrainFirst(gbrainClient, templateId, config);
  if (gbrainContext.totalResults > 0) {
    console.log(`[GBrain] gbrainFirst 找到 ${gbrainContext.totalResults} 条相关记录，相关模板: ${gbrainContext.relatedTemplateIds.join(", ")}`);
  }

  const repository = new TemplateRepository(config.templatesDir);
  const template = repository.load(templateId);
  const prompt = buildPrompt(template);
  const request = createReservedImageRequest(template, prompt);
  const taskId = createTaskId(template.template_id);

  fs.mkdirSync(config.outputDir, { recursive: true });

  const taskOutputDir = path.join(config.outputDir, "tasks", taskId);
  fs.mkdirSync(taskOutputDir, { recursive: true });

  const promptFile = path.join(taskOutputDir, "prompt.txt");
  const resultFile = path.join(taskOutputDir, "image_task.json");
  fs.writeFileSync(promptFile, prompt, "utf-8");

  const now = new Date().toISOString();
  const task: ImageTask = {
    task_id: taskId,
    created_at: now,
    updated_at: now,
    status: "created",
    template: {
      template_id: template.template_id,
      category: template.category,
      title: template.title,
      ratio: template.ratio,
      style: template.style
    },
    prompt_file: promptFile,
    result_file: resultFile,
    image_request: {
      provider: config.aiImageDryRun ? "mock" : config.aiImageProvider,
      api_url: config.aiImageApiUrl,
      dry_run: config.aiImageDryRun,
      request_body: request
    }
  };

  try {
    const provider = createProvider(config);
    const response = await provider.generate(request);

    task.status = "completed";
    task.updated_at = new Date().toISOString();
    task.image_response = response;

    // recordEverything: 记录成功生成决策
    await recordEverything(gbrainClient,
      {
        task_id: taskId,
        template_id: template.template_id,
        decision_type: "image_requested",
        timestamp: new Date().toISOString(),
        details: {
          provider: config.aiImageProvider,
          gbrain_context: gbrainContext
        }
      },
      config
    );
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    const fallbackProvider = new MockImageGenerationProvider();
    const fallbackResponse = await fallbackProvider.generate(request);

    fallbackResponse.raw = {
      ...(typeof fallbackResponse.raw === "object" && fallbackResponse.raw !== null ? fallbackResponse.raw : {}),
      fallback: true,
      original_error: errorMessage
    };

    task.status = "completed";
    task.updated_at = new Date().toISOString();
    task.image_response = fallbackResponse;
    delete (task as Partial<typeof task>).error;

    // recordEverything: 记录回退决策
    await recordEverything(gbrainClient,
      {
        task_id: taskId,
        template_id: template.template_id,
        decision_type: "fallback_used",
        timestamp: new Date().toISOString(),
        details: {
          original_error: errorMessage,
          fallback_provider: "mock",
          gbrain_context: gbrainContext
        }
      },
      config
    );
  }

  fs.writeFileSync(resultFile, `${JSON.stringify(task, null, 2)}\n`, "utf-8");

  // syncAfterWrite: 写入后触发 GBrain 同步
  await syncAfterWrite(gbrainClient, config);

  return {
    task,
    prompt,
    promptFile,
    resultFile
  };
}

function createProvider(config: AppConfig): MockImageGenerationProvider | HttpImageGenerationProvider {
  if (config.aiImageDryRun || config.aiImageProvider === "mock") {
    return new MockImageGenerationProvider();
  }

  if (!config.aiImageApiUrl) {
    throw new Error("AI_IMAGE_API_URL is required when AI_IMAGE_DRY_RUN=false");
  }

  return new HttpImageGenerationProvider(config.aiImageApiUrl, config.aiImageApiKey);
}

function createTaskId(templateId: string): string {
  const stamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
  return `image_${templateId}_${stamp}`;
}
