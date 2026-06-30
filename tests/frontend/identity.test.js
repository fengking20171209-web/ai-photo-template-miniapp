import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  IDENTITY_REINFORCE, BODY_NEGATIVE, DEFAULT_IDENTITY_PROMPT, DEFAULT_MODEL_NEGATIVE, applyModelIdentity,
} from '../../public/identity.js';

test('无模特时 prompt/negative 原样返回', () => {
  const r = applyModelIdentity({ basePrompt: 'hotel, silk dress', baseNegative: 'blurry' });
  assert.equal(r.prompt, 'hotel, silk dress');
  assert.equal(r.negative, 'blurry');
});

test('选中模特：用户输入在前 + 注入身份强化 + 一致性负面', () => {
  const model = { identity_prompt: 'same CC face', negative_prompt: 'no glasses' };
  const r = applyModelIdentity({ basePrompt: 'rooftop', baseNegative: 'lowres', activeModel: model });
  // 用户输入最高优先（在最前）
  assert.ok(r.prompt.startsWith('rooftop'));
  assert.ok(r.prompt.includes(IDENTITY_REINFORCE));
  assert.ok(r.prompt.includes('same CC face'));
  // 负面：用户 + 模特负面 + 防换身材
  assert.ok(r.negative.includes('lowres'));
  assert.ok(r.negative.includes('no glasses'));
  assert.ok(r.negative.includes(BODY_NEGATIVE));
});

test('空 base + 模特：无前导分隔符', () => {
  const model = { identity_prompt: 'face A', negative_prompt: 'x' };
  const r = applyModelIdentity({ basePrompt: '', baseNegative: '', activeModel: model });
  assert.ok(!r.prompt.startsWith('，'));
  assert.ok(!r.negative.startsWith('，'));
  assert.ok(r.prompt.includes(IDENTITY_REINFORCE));
});

test('默认身份/负面常量含身材一致性', () => {
  assert.match(DEFAULT_IDENTITY_PROMPT, /body/);
  assert.match(DEFAULT_MODEL_NEGATIVE, /different body|changed figure/);
});
