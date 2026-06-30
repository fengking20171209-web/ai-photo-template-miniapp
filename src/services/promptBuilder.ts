import type { ImageTemplate } from "../types/template.js";

export function buildPrompt(template: ImageTemplate): string {
  const blocks = template.prompt_blocks;

  return `
【模板名称】
${template.title}

【分类】
${template.category}

【画幅】
${template.ratio}

【风格】
${template.style}

【生成目标】
${blocks.subject}

【脸部保真】
${blocks.face}

【服装造型】
${blocks.clothing}

【场景环境】
${blocks.scene}

【光影氛围】
${blocks.lighting}

【镜头构图】
${blocks.camera}

【画质要求】
${blocks.quality}

【商业用途】
${blocks.commercial_use}

【安全与品质要求】
保留用户真实五官、脸型、肤色，不要过度磨皮，不要低俗，不要裸露，不要生成夸张身体比例，服装完整得体，整体高级、干净、商业可用。

【负面提示】
${buildNegativePrompt(template)}
`.trim();
}

export function buildNegativePrompt(template: ImageTemplate): string {
  return template.negative_prompt.join(", ");
}
