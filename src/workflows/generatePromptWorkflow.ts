import fs from "node:fs";
import path from "node:path";
import type { AppConfig } from "../config/appConfig.js";
import { createReservedImageRequest } from "../services/aiImageService.js";
import { buildPrompt } from "../services/promptBuilder.js";
import { TemplateRepository } from "../templates/templateRepository.js";
import type { GenerateTask } from "../types/task.js";
import { gbrainFirst, recordEverything, syncAfterWrite, getGBrainClient } from "../services/gbrainIntegration.js";

export interface GeneratePromptResult {
  task: GenerateTask;
  prompt: string;
  promptFile: string;
  taskFile: string;
}

export async function generatePromptWorkflow(config: AppConfig, templateId: string): Promise<GeneratePromptResult> {
  // gbrainEnabled 条件判断：未配置时降级为本地模式
  const gbrainClient = getGBrainClient(config);

  // gbrainFirst: 生成 prompt 前搜索 GBrain 获取历史模板/prompt 参考
  const gbrainContext = await gbrainFirst(gbrainClient, templateId, config);
  if (gbrainContext.totalResults > 0) {
    console.log(`[GBrain] gbrainFirst 找到 ${gbrainContext.totalResults} 条相关记录，相关模板: ${gbrainContext.relatedTemplateIds.join(", ")}`);
  }

  const repository = new TemplateRepository(config.templatesDir);
  const template = repository.load(templateId);
  const prompt = buildPrompt(template);

  fs.mkdirSync(config.outputDir, { recursive: true });

  const promptFile = path.join(config.outputDir, "prompt.txt");
  const taskFile = path.join(config.outputDir, "task.json");
  fs.writeFileSync(promptFile, prompt, "utf-8");

  const task: GenerateTask = {
    task_id: createTaskId(template.template_id),
    created_at: new Date().toISOString(),
    status: "api_reserved",
    template: {
      template_id: template.template_id,
      category: template.category,
      title: template.title,
      ratio: template.ratio,
      style: template.style
    },
    prompt_file: promptFile,
    image_request: {
      provider: "reserved",
      api_url: config.aiImageApiUrl,
      will_call_api: false,
      request_body: createReservedImageRequest(template, prompt)
    }
  };

  fs.writeFileSync(taskFile, `${JSON.stringify(task, null, 2)}\n`, "utf-8");

  // recordEverything: 记录 prompt 生成决策到 GBrain
  await recordEverything(gbrainClient,
    {
      task_id: task.task_id,
      template_id: template.template_id,
      decision_type: "prompt_generated",
      timestamp: new Date().toISOString(),
      details: {
        prompt_length: prompt.length,
        gbrain_context: gbrainContext
      }
    },
    config
  );

  // syncAfterWrite: 写入后触发 GBrain 同步
  await syncAfterWrite(gbrainClient, config);

  return {
    task,
    prompt,
    promptFile,
    taskFile
  };
}

function createTaskId(templateId: string): string {
  const stamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
  return `task_${templateId}_${stamp}`;
}
