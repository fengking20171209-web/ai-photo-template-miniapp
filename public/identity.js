/**
 * identity.js — Model identity consistency layer (pure & testable).
 *
 * No LoRA: identity consistency relies on a bound reference face (img2img)
 * plus auto-injected identity / anti-drift prompts. This module centralizes
 * the prompt/negative assembly so the "consistency guard" is unit-testable.
 */

export const DEFAULT_IDENTITY_PROMPT = 'same person, identical face and identical body, consistent identity, same facial features, same body type and figure, same height and proportions, same hairstyle, full-body consistency';
export const DEFAULT_MODEL_NEGATIVE = 'face change, different person, inconsistent identity, multiple faces, different body, different body type, changed figure, altered proportions, distorted face, deformed body';
// 始终注入的强化一致性子句（连老模特也生效，确保脸+身材一起保持）
export const IDENTITY_REINFORCE = 'keep the exact same person as the reference image: identical face AND identical body type, same figure, height, proportions, skin tone and hairstyle, fully consistent appearance from head to toe';
export const BODY_NEGATIVE = 'different body, different body type, changed figure, altered proportions, different height, different weight';

/**
 * Assemble final (prompt, negative) for generation.
 * 严格分层：用户输入(最高) > 模特身份 > 防换脸/换身材负面。
 * 用户输入始终在前；选中模特时追加身份强化与一致性负面词。
 *
 * @param {object} o
 * @param {string} o.basePrompt   用户输入(标签+自定义)
 * @param {string} o.baseNegative 用户负面词
 * @param {object|null} o.activeModel 当前模特 {identity_prompt, negative_prompt}
 * @returns {{prompt: string, negative: string}}
 */
export function applyModelIdentity({ basePrompt = '', baseNegative = '', activeModel = null } = {}) {
  let prompt = basePrompt;
  let negative = baseNegative;
  if (activeModel) {
    prompt = [basePrompt, IDENTITY_REINFORCE, activeModel.identity_prompt].filter(Boolean).join('，');
    negative = [baseNegative, activeModel.negative_prompt, BODY_NEGATIVE].filter(Boolean).join('，');
  }
  return { prompt, negative };
}
