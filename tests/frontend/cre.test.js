import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  tokenConcepts, conceptsOf, normUsage, scoreCandidate, topMatches, recommend, buildReason,
} from '../../public/cre.js';

const arr = (s) => [...s];

// --- 概念映射 ---------------------------------------------------------------
test('tokenConcepts 映射韩系/酒店/未知', () => {
  assert.deepEqual(arr(tokenConcepts('韩系')).sort(), ['indoor', 'korean', 'soft', 'warm']);
  assert.ok(arr(tokenConcepts('luxury hotel suite')).includes('hotel'));
  assert.equal(arr(tokenConcepts('完全无关的词xyz')).length, 0);
});

test('conceptsOf 按库取不同字段', () => {
  const bg = { id: 'b', category: ['室内', '酒店'], atmosphere: ['温暖'], lighting: ['黄昏暖光'] };
  const outfit = { id: 'o', style_tags: ['优雅'], fashion_keywords: ['white silk slip dress'] };
  const model = { id: 'm', tags: ['韩系', '清纯'] };
  assert.ok(arr(conceptsOf('bg', bg)).includes('hotel'));
  assert.ok(arr(conceptsOf('bg', bg)).includes('warm'));
  assert.ok(arr(conceptsOf('outfit', outfit)).includes('silk'));
  assert.ok(arr(conceptsOf('model', model)).includes('korean'));
});

// --- 打分 -------------------------------------------------------------------
test('normUsage 对数归一，max=0 返回 0', () => {
  assert.equal(normUsage(5, 0), 0);
  assert.equal(normUsage(0, 10), 0);
  assert.ok(normUsage(10, 10) === 1);
  assert.ok(normUsage(3, 10) > 0 && normUsage(3, 10) < 1);
});

test('scoreCandidate: v1 仅概念重叠；v2 叠加各加成', () => {
  const src = new Set(['silk', 'elegant', 'warm', 'hotel', 'luxury']);
  const cand = { id: 'b', category: ['室内', '酒店'], atmosphere: ['温暖'], lighting: ['黄昏暖光'] };
  const v1 = scoreCandidate(src, new Set(), new Set(), cand, 'bg', 0, 'v1');
  assert.equal(v1.score, v1.overlap);
  assert.equal(v1.usageB, 0);
  // v2：注入用量 + 模特亲和 + 上下文，分数应高于纯重叠
  const aff = new Set(['warm', 'hotel']);
  const ctx = new Set(['silk', 'warm']);
  const usageOf = () => 10;
  const v2 = scoreCandidate(src, aff, ctx, cand, 'bg', 10, 'v2', usageOf);
  assert.ok(v2.score > v2.overlap, 'v2 应包含加成');
  assert.ok(v2.affinityB > 0 && v2.usageB > 0 && v2.contextB > 0);
});

test('buildReason 列出匹配概念与加成（可解释）', () => {
  const d = { matched: ['hotel', 'warm'], affinityB: 0.5, usageB: 0.2, contextB: 0 };
  const r = buildReason(d);
  assert.ok(r.includes('概念匹配'));
  assert.ok(r.includes('模特偏好'));
  assert.ok(r.includes('高人气'));
  assert.ok(!r.includes('会话上下文'));
});

// --- 排序 & 推荐 ------------------------------------------------------------
test('topMatches: 真丝裙 -> 酒店背景优先于街道，确定性排序', () => {
  const src = conceptsOf('outfit', { id: 'o', style_tags: ['优雅'], fashion_keywords: ['silk satin dress'] });
  const bgHotel = { id: 'bg_hotel', category: ['室内', '酒店'], atmosphere: ['温暖'], lighting: ['黄昏暖光'] };
  const bgStreet = { id: 'bg_street', category: ['城市', '街道'], atmosphere: ['霓虹'], lighting: ['夜晚霓虹'] };
  const top = topMatches('bg', [bgStreet, bgHotel], src, new Set(), new Set(), 'v2');
  assert.equal(top[0].it.id, 'bg_hotel');
  assert.ok(top.length <= 5);
});

test('recommend: 选服装 -> 返回模特+背景，不含服装本类', () => {
  const outfit = { id: 'o', style_tags: ['优雅'], fashion_keywords: ['silk dress'] };
  const res = recommend({
    kind: 'outfit', item: outfit,
    models: [{ id: 'm', tags: ['韩系'] }],
    backgrounds: [{ id: 'bg', category: ['酒店'], atmosphere: ['温暖'], lighting: ['暖光'] }],
    outfits: [{ id: 'o2', style_tags: ['街头'], fashion_keywords: ['denim'] }],
  });
  assert.ok(res.models, '应推荐模特');
  assert.ok(res.backgrounds, '应推荐背景');
  assert.equal(res.outfits, undefined, '不应推荐服装本类');
});

test('recommend: 选模特 -> 返回背景+服装，不含模特本类', () => {
  const model = { id: 'm', tags: ['韩系', '清纯'] };
  const res = recommend({
    kind: 'model', item: model,
    models: [{ id: 'm2', tags: ['御姐'] }],
    backgrounds: [{ id: 'bg', category: ['酒店'], atmosphere: ['温暖'], lighting: ['暖光'] }],
    outfits: [{ id: 'o', style_tags: ['优雅'], fashion_keywords: ['silk dress'] }],
  });
  assert.equal(res.models, undefined);
  assert.ok(res.backgrounds);
  assert.ok(res.outfits);
});
