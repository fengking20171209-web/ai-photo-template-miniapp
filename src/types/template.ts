export type TemplateCategory =
  | "古风美女"
  | "职业形象"
  | "形象分析"
  | "漫画角色"
  | "产品海报"
  | "模特大赛"
  | "新中式概念"
  | "肚兜现代时装"
  | "SIUF 2026 内衣秀"
  | "人像写真"
  | "幻系插画";

export interface PromptBlocks {
  subject: string;
  face: string;
  clothing: string;
  scene: string;
  lighting: string;
  camera: string;
  quality: string;
  commercial_use: string;
}

export interface TemplateOptions {
  quality: "draft" | "standard" | "high";
  face_strength: number;
  output_count: number;
}

export interface ImageTemplate {
  template_id: string;
  category: TemplateCategory;
  title: string;
  version: string;
  ratio: string;
  face_lock: boolean;
  style: string;
  scene: string;
  clothing: string;
  prompt_blocks: PromptBlocks;
  options: TemplateOptions;
  negative_prompt: string[];
  tags?: string[];
  description?: string;
}
