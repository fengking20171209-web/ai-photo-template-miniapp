import fs from "node:fs";
import path from "node:path";
import type { ImageTemplate } from "../types/template.js";
import { parseTemplate } from "./templateSchema.js";

export class TemplateRepository {
  constructor(private readonly templatesDir: string) {}

  listTemplateIds(): string[] {
    return fs
      .readdirSync(this.templatesDir)
      .filter((file) => file.endsWith(".json"))
      .map((file) => path.basename(file, ".json"))
      .sort();
  }

  load(templateId: string): ImageTemplate {
    const safeTemplateId = path.basename(templateId, ".json");
    const templatePath = path.join(this.templatesDir, `${safeTemplateId}.json`);

    if (!fs.existsSync(templatePath)) {
      const available = this.listTemplateIds().join(", ");
      throw new Error(`Template not found: ${safeTemplateId}. Available templates: ${available}`);
    }

    const raw = fs.readFileSync(templatePath, "utf-8");
    const parsed = JSON.parse(raw);
    return parseTemplate(parsed);
  }
}
