/**
 * copilot.js — Prompt Copilot Agent v1, pure & testable helpers.
 *
 * Deterministic, rule-based prompt composition. No DOM, no global state,
 * no network. The DOM/streaming glue (cpAutoComplete, cpWriteDraft, etc.)
 * stays in app.js and calls these helpers.
 */
import { tokenConcepts, conceptsOf } from './cre.js';

export const CP_FIELDS = ['Model', 'Background', 'Outfit', 'Pose', 'Lighting', 'Camera', 'Style Keywords'];
export const CP_POSE = ['natural standing pose', 'elegant seated pose', 'walking candid pose', 'over-the-shoulder glance', 'leaning against a wall', 'three-quarter turn pose'];
export const CP_LIGHT = ['soft cinematic lighting', 'warm golden-hour light', 'studio softbox lighting', 'dramatic rim light', 'cool blue-tone lighting', 'window natural light'];
export const CP_CAMERA = ['medium half-body shot, 50mm', 'close-up portrait, 85mm', 'full-body wide shot, 35mm', 'three-quarter shot, shallow depth of field', 'low-angle editorial shot', 'eye-level editorial framing'];
export const CP_STYLE_BASE = 'cinematic fashion photography, high detail skin texture';

export function cpTokens(text) {
  return (text || '').toLowerCase().split(/[\s,+，、/|]+/).filter(Boolean);
}
export function cpConcepts(tokens) {
  const s = new Set();
  tokens.forEach((t) => tokenConcepts(t).forEach((c) => s.add(c)));
  return s;
}
export function cpLibHay(kind, it) {
  return (kind === 'bg'
    ? [it.name, ...(it.category || []), ...(it.space || []), ...(it.atmosphere || []), ...(it.lighting || []), ...(it.prompt_keywords || [])]
    : [it.name, ...(it.category || []), ...(it.style_tags || []), ...(it.fabric_tags || []), ...(it.fashion_keywords || [])]
  ).join(' ').toLowerCase();
}
export function cpBestLib(kind, pool, tokens, concepts) {
  let best = null, bestScore = 0;
  for (const it of pool) {
    const hay = cpLibHay(kind, it);
    let raw = 0; tokens.forEach((t) => { if (t.length >= 2 && hay.includes(t)) raw++; });
    let ov = 0; const cc = conceptsOf(kind, it); concepts.forEach((c) => { if (cc.has(c)) ov++; });
    const s = raw * 2 + ov;
    if (s > bestScore) { bestScore = s; best = it; }
  }
  return bestScore > 0 ? best : null;
}
export function cpBestModel(models, tokens, concepts) {
  let best = null, bestScore = 0;
  for (const m of models) {
    const hay = (m.name + ' ' + (m.tags || []).join(' ')).toLowerCase();
    let raw = 0; tokens.forEach((t) => { if (t.length >= 2 && hay.includes(t)) raw++; });
    let ov = 0; const cc = conceptsOf('model', m); concepts.forEach((c) => { if (cc.has(c)) ov++; });
    const s = raw * 3 + ov;
    if (s > bestScore) { bestScore = s; best = m; }
  }
  return bestScore > 0 ? best : null;
}
export function cpInferBg(c) {
  if (c.has('hotel') || c.has('luxury')) return 'cinematic luxury hotel suite, warm lighting, soft shadows';
  if (c.has('bedroom')) return 'cozy modern bedroom, soft warm light';
  if (c.has('studio') || c.has('editorial')) return 'minimal studio backdrop, clean lighting';
  if (c.has('neon') || c.has('city')) return 'neon-lit city street at night';
  if (c.has('street') || c.has('streetwear')) return 'urban street, daylight';
  if (c.has('nature')) return 'natural outdoor setting, soft daylight';
  return 'clean neutral backdrop, soft studio lighting';
}
export function cpInferOutfit(c) {
  if (c.has('silk') || c.has('elegant')) return 'silk fashion dress, editorial styling';
  if (c.has('streetwear')) return 'modern streetwear with jacket';
  if (c.has('sexy')) return 'lingerie-inspired fashion, editorial sheer styling';
  if (c.has('cute')) return 'sweet casual fashion, soft tones';
  if (c.has('sport')) return 'athleisure activewear set';
  return 'modern fashion outfit, editorial styling';
}
export function cpLightFor(c, idx) {
  if (c.has('warm')) return 'warm golden-hour light';
  if (c.has('neon')) return 'neon ambient lighting';
  if (c.has('cool')) return 'cool blue-tone lighting';
  if (c.has('studio')) return 'studio softbox lighting';
  return CP_LIGHT[idx % CP_LIGHT.length];
}
export function cpStyleExtra(c) {
  const ex = [];
  if (c.has('editorial')) ex.push('editorial high fashion');
  if (c.has('vintage')) ex.push('subtle retro mood');
  if (c.has('cinematic')) ex.push('cinematic color grading');
  return ex.length ? ', ' + ex.join(', ') : '';
}
export function cpRenderDraft(f) {
  return CP_FIELDS.map((k) => `[${k}]: ${f[k] || ''}`).join('\n');
}
export function cpParseDraft(text) {
  const f = {}; let structured = false;
  (text || '').split(/\n+/).forEach((line) => {
    const m = line.match(/^\s*\[([^\]]+)\]\s*[:：]\s*(.*)$/);
    if (m && CP_FIELDS.includes(m[1].trim())) { f[m[1].trim()] = m[2].trim(); structured = true; }
  });
  return { fields: f, structured };
}

/**
 * 组装严格 7 段结构化草稿（纯函数，统一 autoComplete/random/smartGenerate 三处构建）。
 * model/bg/outfit 为对象或 null；pose/lighting/camera 可显式覆盖，否则按概念/默认推断。
 */
export function composeDraft({ model = null, bg = null, outfit = null, concepts = new Set(), pose, lighting, camera } = {}) {
  return {
    Model: model ? `${model.name}（锁定身份/脸）` : '(未选择，可上传参考图或留空)',
    Background: bg ? (bg.prompt_keywords || []).join(', ') : cpInferBg(concepts),
    Outfit: outfit ? (outfit.fashion_keywords || []).join(', ') : cpInferOutfit(concepts),
    Pose: pose || CP_POSE[0],
    Lighting: lighting || cpLightFor(concepts, 0),
    Camera: camera || CP_CAMERA[0],
    'Style Keywords': CP_STYLE_BASE + cpStyleExtra(concepts),
  };
}
