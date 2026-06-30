/**
 * cre.js — Cross Recommendation Engine (CRE v2), pure & testable.
 *
 * No DOM, no global state, no localStorage. All session inputs (active model,
 * context concepts, usage counts, mode) are passed in explicitly so the engine
 * is deterministic and unit-testable.
 *
 * Scoring (v2): concept_overlap*1.0 + usage*0.3 + model_affinity*0.5 + context*0.4
 */

// 统一概念空间：把不同库的标签/关键词归一到同一组概念，便于跨库重叠打分
export const CONCEPT_RULES = [
  { p: ['韩系', 'korean'], c: ['korean', 'soft', 'warm', 'indoor'] },
  { p: ['清纯', '气质', 'delicate', 'soft'], c: ['soft', 'warm', 'daylight', 'bedroom'] },
  { p: ['甜美', '可爱', 'cute', 'youthful', '学院', 'jk', 'sailor', 'preppy', 'lolita'], c: ['cute', 'soft', 'daylight', 'bedroom', 'nature'] },
  { p: ['优雅', 'elegant', 'gown', 'evening'], c: ['elegant', 'warm', 'hotel', 'luxury'] },
  { p: ['御姐', '冷艳', '酷感', '成熟', 'strong', 'mature'], c: ['strong', 'studio', 'city', 'editorial'] },
  { p: ['性感', 'sexy', 'lingerie', 'sheer', '蕾丝', 'lace', '纱质', 'tulle', 'intimate'], c: ['sexy', 'elegant', 'hotel', 'night'] },
  { p: ['复古', 'vintage', 'retro', '旗袍', 'qipao', '浴衣', 'yukata'], c: ['vintage', 'warm', 'elegant'] },
  { p: ['派对', 'party', '华丽', '亮片', 'sequin'], c: ['party', 'neon', 'night', 'city'] },
  { p: ['运动', '活力', 'sport', 'athleisure', 'yoga', 'cycling', 'tracksuit'], c: ['sport', 'daylight', 'studio'] },
  { p: ['街头', 'streetwear', 'denim', 'leather', 'hoodie', 'techwear', '机能', '皮'], c: ['streetwear', 'street', 'city', 'neon'] },
  { p: ['editorial', 'fashion', '时尚'], c: ['editorial', 'studio'] },
  { p: ['真丝', '缎面', 'silk', 'satin'], c: ['silk', 'elegant', 'warm', 'hotel', 'luxury'] },
  { p: ['职业', 'suit', 'blazer', 'business', 'tailored'], c: ['editorial', 'city', 'strong'] },
  { p: ['泳装', 'swimsuit', 'bikini', 'swimwear', 'beach'], c: ['nature', 'daylight', 'sexy'] },
  // 背景相关
  { p: ['酒店', 'hotel', 'suite', '套房', '豪华', 'luxury'], c: ['hotel', 'indoor', 'warm', 'luxury', 'elegant'] },
  { p: ['卧室', 'bedroom'], c: ['bedroom', 'indoor', 'soft', 'warm'] },
  { p: ['影棚', 'studio', 'cyclorama'], c: ['studio', 'editorial', 'minimal'] },
  { p: ['城市', 'city', '高楼', 'skyscraper', 'rooftop', '天台'], c: ['city', 'editorial', 'strong'] },
  { p: ['街', 'street', 'alley', '巷', '商业'], c: ['street', 'city', 'streetwear'] },
  { p: ['霓虹', 'neon', '夜', 'night'], c: ['neon', 'city', 'night', 'party'] },
  { p: ['暖', 'warm', 'golden', 'sunset', '黄昏'], c: ['warm'] },
  { p: ['冷', 'cool', 'blue'], c: ['cool', 'strong'] },
  { p: ['电影', 'cinematic'], c: ['cinematic', 'warm', 'strong'] },
  { p: ['清晨', '正午', 'morning', 'midday', 'daylight', '自然', '清新', 'natural'], c: ['daylight', 'soft', 'nature'] },
  { p: ['海', 'beach', '森林', 'forest', '花', 'field', '草原', 'grass', '湖', 'lake', 'nature', '雪', 'snow', '沙漠', 'desert'], c: ['nature', 'daylight', 'soft'] },
  { p: ['浴室', '客厅', '书房', '厨房', '室内', 'indoor', '茶室', '咖啡', 'cafe'], c: ['indoor', 'warm'] },
];

export const CRE_WEIGHTS = { overlap: 1.0, usage: 0.3, affinity: 0.5, context: 0.4 };

export function tokenConcepts(token) {
  const t = (token || '').toLowerCase();
  const out = new Set();
  for (const r of CONCEPT_RULES) {
    if (r.p.some((pat) => t.includes(pat))) r.c.forEach((c) => out.add(c));
  }
  return out;
}

/** Concepts for an asset. Memoized on the item (静态库) for <50ms latency. */
export function conceptsOf(kind, it) {
  if (kind !== 'model' && it.__c) return it.__c;
  let tokens = [];
  if (kind === 'model') tokens = it.tags || [];
  else if (kind === 'bg') tokens = [].concat(it.category || [], it.atmosphere || [], it.lighting || []);
  else tokens = [].concat(it.style_tags || [], it.fashion_keywords || []);
  const set = new Set();
  tokens.forEach((tok) => tokenConcepts(tok).forEach((c) => set.add(c)));
  if (kind !== 'model') it.__c = set;
  return set;
}

export function normUsage(count, max) {
  return max > 0 ? Math.log(1 + count) / Math.log(1 + max) : 0;
}

const defaultUsageOf = (it) => it.usage_count || 0;

/** Score one candidate. Pure: usage comes from injected usageOf. */
export function scoreCandidate(src, aff, ctx, cand, kind, maxUsage, mode, usageOf = defaultUsageOf) {
  const cc = conceptsOf(kind, cand);
  const matched = [];
  src.forEach((c) => { if (cc.has(c)) matched.push(c); });
  const overlap = matched.length;
  if (mode === 'v1') {
    return { score: overlap, overlap, matched, usageB: 0, affinityB: 0, contextB: 0, trend: '·' };
  }
  const usageB = normUsage(usageOf(cand), maxUsage);
  let aN = 0; if (aff && aff.size) aff.forEach((c) => { if (cc.has(c)) aN++; });
  const affinityB = aff && aff.size ? aN / aff.size : 0;
  let xN = 0; if (ctx && ctx.size) ctx.forEach((c) => { if (cc.has(c)) xN++; });
  const contextB = ctx && ctx.size ? xN / ctx.size : 0;
  const score = overlap * CRE_WEIGHTS.overlap + usageB * CRE_WEIGHTS.usage + affinityB * CRE_WEIGHTS.affinity + contextB * CRE_WEIGHTS.context;
  const boost = usageB * CRE_WEIGHTS.usage + affinityB * CRE_WEIGHTS.affinity + contextB * CRE_WEIGHTS.context;
  const trend = boost > 0.25 ? '↑' : (boost > 0.05 ? '↗' : '·');
  return { score, overlap, matched, usageB, affinityB, contextB, trend };
}

export function buildReason(d) {
  const parts = [];
  if (d.matched.length) parts.push(`概念匹配 ${d.matched.slice(0, 3).join('/')}`);
  if (d.affinityB > 0.01) parts.push(`模特偏好 +${(d.affinityB * CRE_WEIGHTS.affinity).toFixed(2)}`);
  if (d.usageB > 0.01) parts.push(`高人气 +${(d.usageB * CRE_WEIGHTS.usage).toFixed(2)}`);
  if (d.contextB > 0.01) parts.push(`会话上下文 +${(d.contextB * CRE_WEIGHTS.context).toFixed(2)}`);
  return parts.join(' · ') || '基础匹配';
}

/** Top-5 candidates for a target library. Deterministic ordering. */
export function topMatches(kind, pool, src, aff, ctx, mode = 'v2', usageOf = defaultUsageOf) {
  const maxUsage = pool.reduce((m, it) => Math.max(m, usageOf(it)), 0);
  return pool
    .map((it) => { const d = scoreCandidate(src, aff, ctx, it, kind, maxUsage, mode, usageOf); return Object.assign({ it, reason: buildReason(d) }, d); })
    .filter((x) => x.score > 0)
    .sort((a, b) => (b.score - a.score) || (b.overlap - a.overlap) || String(a.it.id).localeCompare(String(b.it.id)))
    .slice(0, 5);
}

/**
 * Recommend related assets. Selecting one kind returns the OTHER two kinds.
 * All session state injected via opts (no globals).
 */
export function recommend(opts) {
  const { kind, item, models = [], backgrounds = [], outfits = [], activeModel = null, contextConcepts = new Set(), mode = 'v2', usageOf = defaultUsageOf } = opts;
  const src = conceptsOf(kind, item);
  const modelInPlay = kind === 'model' ? item : activeModel;
  const aff = modelInPlay ? conceptsOf('model', modelInPlay) : new Set();
  const res = {};
  if (kind !== 'model') res.models = topMatches('model', models, src, aff, contextConcepts, mode, usageOf);
  if (kind !== 'bg') res.backgrounds = topMatches('bg', backgrounds, src, aff, contextConcepts, mode, usageOf);
  if (kind !== 'outfit') res.outfits = topMatches('outfit', outfits, src, aff, contextConcepts, mode, usageOf);
  return res;
}
