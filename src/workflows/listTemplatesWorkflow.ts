import type { AppConfig } from "../config/appConfig.js";
import { TemplateRepository } from "../templates/templateRepository.js";
import type { ImageTemplate } from "../types/template.js";
import { gbrainFirst, getGBrainClient } from "../services/gbrainIntegration.js";

export interface TemplateSummary {
  template_id: string;
  category: string;
  title: string;
  ratio: string;
  style: string;
  quality: string;
  face_strength: number;
}

export async function listTemplatesWorkflow(config: AppConfig): Promise<TemplateSummary[]> {
  // gbrainEnabled 条件判断：未配置时降级为本地模式
  const gbrainClient = getGBrainClient(config);

  // gbrainFirst: 列出模板前搜索 GBrain 获取推荐/分类信息
  // 搜索所有模板分类，获取推荐信息
  const gbrainContext = await gbrainFirst(gbrainClient, "*", config);
  if (gbrainContext.totalResults > 0) {
    console.log(`[GBrain] gbrainFirst 找到 ${gbrainContext.totalResults} 条相关记录，推荐模板: ${gbrainContext.relatedTemplateIds.join(", ")}`);
  }

  const repository = new TemplateRepository(config.templatesDir);

  return repository
    .listTemplateIds()
    .map((templateId) => toSummary(repository.load(templateId)));
}

function toSummary(template: ImageTemplate): TemplateSummary {
  return {
    template_id: template.template_id,
    category: template.category,
    title: template.title,
    ratio: template.ratio,
    style: template.style,
    quality: template.options.quality,
    face_strength: template.options.face_strength
  };
}
