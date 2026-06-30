import type { ImageTemplate, TemplateCategory } from "../types/template.js";

const allowedCategories = new Set<TemplateCategory>([
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
  "幻系插画"
]);

const allowedQuality = new Set(["draft", "standard", "high"]);

export function parseTemplate(value: unknown): ImageTemplate {
  if (!isRecord(value)) {
    throw new Error("Template JSON must be an object");
  }

  const promptBlocks = value.prompt_blocks;
  const options = value.options;

  if (!isRecord(promptBlocks)) {
    throw new Error("Template prompt_blocks must be an object");
  }

  if (!isRecord(options)) {
    throw new Error("Template options must be an object");
  }

  const template: ImageTemplate = {
    template_id: readString(value, "template_id"),
    category: readCategory(value, "category"),
    title: readString(value, "title"),
    version: readString(value, "version"),
    ratio: readString(value, "ratio"),
    face_lock: readBoolean(value, "face_lock"),
    style: readString(value, "style"),
    scene: readString(value, "scene"),
    clothing: readString(value, "clothing"),
    prompt_blocks: {
      subject: readString(promptBlocks, "subject"),
      face: readString(promptBlocks, "face"),
      clothing: readString(promptBlocks, "clothing"),
      scene: readString(promptBlocks, "scene"),
      lighting: readString(promptBlocks, "lighting"),
      camera: readString(promptBlocks, "camera"),
      quality: readString(promptBlocks, "quality"),
      commercial_use: readString(promptBlocks, "commercial_use")
    },
    options: {
      quality: readQuality(options, "quality"),
      face_strength: readNumber(options, "face_strength", 0, 1),
      output_count: readInteger(options, "output_count", 1, 9)
    },
    negative_prompt: readStringArray(value, "negative_prompt")
  };

  return template;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readString(record: Record<string, unknown>, key: string): string {
  const value = record[key];
  if (typeof value !== "string" || value.trim() === "") {
    throw new Error(`Template field "${key}" must be a non-empty string`);
  }
  return value;
}

function readBoolean(record: Record<string, unknown>, key: string): boolean {
  const value = record[key];
  if (typeof value !== "boolean") {
    throw new Error(`Template field "${key}" must be a boolean`);
  }
  return value;
}

function readCategory(record: Record<string, unknown>, key: string): TemplateCategory {
  const value = readString(record, key);
  if (!allowedCategories.has(value as TemplateCategory)) {
    throw new Error(`Template field "${key}" has unsupported category: ${value}`);
  }
  return value as TemplateCategory;
}

function readQuality(record: Record<string, unknown>, key: string): "draft" | "standard" | "high" {
  const value = readString(record, key);
  if (!allowedQuality.has(value)) {
    throw new Error(`Template field "${key}" has unsupported quality: ${value}`);
  }
  return value as "draft" | "standard" | "high";
}

function readNumber(record: Record<string, unknown>, key: string, min: number, max: number): number {
  const value = record[key];
  if (typeof value !== "number" || Number.isNaN(value) || value < min || value > max) {
    throw new Error(`Template field "${key}" must be a number between ${min} and ${max}`);
  }
  return value;
}

function readInteger(record: Record<string, unknown>, key: string, min: number, max: number): number {
  const value = readNumber(record, key, min, max);
  if (!Number.isInteger(value)) {
    throw new Error(`Template field "${key}" must be an integer`);
  }
  return value;
}

function readStringArray(record: Record<string, unknown>, key: string): string[] {
  const value = record[key];
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string" || item.trim() === "")) {
    throw new Error(`Template field "${key}" must be an array of non-empty strings`);
  }
  return value;
}
