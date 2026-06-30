import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  CP_FIELDS, cpTokens, cpConcepts, cpLibHay, cpBestLib, cpBestModel,
  cpInferBg, cpInferOutfit, cpLightFor, cpStyleExtra, cpRenderDraft, cpParseDraft,
} from '../../public/copilot.js';

test('cpTokens 按多种分隔符切分', () => {
  assert.deepEqual(cpTokens('hotel + bunny, korean model'), ['hotel', 'bunny', 'korean', 'model']);
  assert.deepEqual(cpTokens(''), []);
});

test('cpConcepts 把 token 归一为概念', () => {
  const c = cpConcepts(cpTokens('hotel silk'));
  assert.ok(c.has('hotel'));
  assert.ok(c.has('silk'));
});

test('cpRenderDraft / cpParseDraft 往返一致，含 7 段', () => {
  const f = { Model: 'CC', Background: 'hotel', Outfit: 'silk dress', Pose: 'standing', Lighting: 'warm', Camera: '50mm', 'Style Keywords': 'cinematic' };
  const text = cpRenderDraft(f);
  assert.equal(text.split('\n').length, 7);
  CP_FIELDS.forEach((k) => assert.ok(text.includes(`[${k}]:`)));
  const { fields, structured } = cpParseDraft(text);
  assert.ok(structured);
  assert.equal(fields.Background, 'hotel');
  assert.equal(fields['Style Keywords'], 'cinematic');
});

test('cpParseDraft 非结构化文本 -> structured=false', () => {
  const { structured } = cpParseDraft('随便写的一段话，没有方括号字段');
  assert.equal(structured, false);
});

test('cpBestLib: "bunny" 命中兔女郎服装；"hotel" 命中酒店背景', () => {
  const outfits = [
    { id: 'o1', name: '真丝裙', style_tags: ['优雅'], fashion_keywords: ['silk dress'] },
    { id: 'o2', name: '兔女郎风时装', style_tags: ['派对'], fashion_keywords: ['bunny-inspired fashion bodysuit'] },
  ];
  const tokens = cpTokens('bunny');
  const pick = cpBestLib('outfit', outfits, tokens, cpConcepts(tokens));
  assert.equal(pick.id, 'o2');

  const bgs = [
    { id: 'b1', name: '霓虹街道', category: ['城市'], atmosphere: ['霓虹'], lighting: ['夜晚霓虹'], prompt_keywords: ['neon street'] },
    { id: 'b2', name: '豪华酒店套房', category: ['酒店'], atmosphere: ['温暖'], lighting: ['暖光'], prompt_keywords: ['luxury hotel suite'] },
  ];
  const t2 = cpTokens('hotel');
  const pickBg = cpBestLib('bg', bgs, t2, cpConcepts(t2));
  assert.equal(pickBg.id, 'b2');
});

test('cpBestModel 按名称/标签匹配', () => {
  const models = [{ id: 'm1', name: 'CC', tags: ['御姐'] }, { id: 'm2', name: 'UU', tags: ['韩系', '清纯'] }];
  const tokens = cpTokens('uu korean');
  const pick = cpBestModel(models, tokens, cpConcepts(tokens));
  assert.equal(pick.id, 'm2');
});

test('cpInferBg / cpInferOutfit / cpLightFor 概念映射', () => {
  assert.match(cpInferBg(new Set(['hotel'])), /hotel/);
  assert.match(cpInferBg(new Set(['neon'])), /neon|city/);
  assert.match(cpInferOutfit(new Set(['silk'])), /silk/);
  assert.match(cpInferOutfit(new Set(['streetwear'])), /streetwear/);
  assert.equal(cpLightFor(new Set(['warm']), 0), 'warm golden-hour light');
  assert.match(cpStyleExtra(new Set(['editorial'])), /editorial/);
});
