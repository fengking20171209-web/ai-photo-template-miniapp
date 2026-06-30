/* settings.js — 模型管理（左右两栏，独立页面） */
const API = '/api/config/models';
const $ = (id) => document.getElementById(id);

let cfg = null;        // 工作态配置（可编辑）
let selectedId = null; // 当前选中模型

const ICONS = { sensenova: '⚡', agnes: '✨', mock: '🎭' };
const icon = (id) => ICONS[id] || '⚙️';

function toast(msg) {
  const t = $('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2200);
}
function esc(s) {
  return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function provById(id) { return (cfg.providers || []).find((p) => p.id === id); }

/* ===== 左侧列表 ===== */
function renderList() {
  const box = $('modelList');
  box.innerHTML = '';
  (cfg.providers || []).forEach((p) => {
    const btn = document.createElement('button');
    btn.className = 'model-card' + (p.id === selectedId ? ' active' : '');
    btn.dataset.id = p.id;
    btn.innerHTML = `
      <span class="model-ico">${icon(p.id)}</span>
      <span class="model-meta">
        <span class="model-name">${esc(p.name || p.id)}</span>
        <span class="model-status"><span class="dot ${p.enabled ? 'on' : 'off'}"></span>${p.enabled ? '已启用' : '已禁用'}</span>
      </span>`;
    btn.addEventListener('click', () => selectModel(p.id));
    box.appendChild(btn);
  });
}

/* ===== 右侧详情 ===== */
function selectModel(id) {
  selectedId = id;
  renderList();
  renderDetail();
}

function renderDetail() {
  const p = provById(selectedId);
  if (!p) return;
  $('detailIco').textContent = icon(p.id);
  $('detailName').textContent = p.name || p.id;
  const badge = $('detailBadge');
  badge.textContent = p.enabled ? '已启用' : '已禁用';
  badge.classList.toggle('off', !p.enabled);

  $('f_enabled').checked = !!p.enabled;
  $('f_name').value = p.name || '';
  $('f_model').value = p.model || '';
  $('f_base_url').value = p.base_url || '';
  $('f_api_key').value = p._newKey || '';
  $('f_api_key').type = 'password';

  const keyHint = p.has_key
    ? `已配置（${esc(p.key_preview || '****')}，来源：${p.key_source === 'config' ? '配置' : 'env'}）`
    : '未配置';
  $('keyHint').textContent = '当前：' + keyHint;

  const caps = $('f_caps');
  caps.innerHTML = (p.capabilities || []).length
    ? p.capabilities.map((c) => `<span class="cap">${esc(c)}</span>`).join('')
    : '<span class="cap">—</span>';

  $('testResult').classList.add('hidden');
}

/* 详情输入实时写回工作态 */
function bindDetailInputs() {
  $('f_enabled').addEventListener('change', (e) => {
    const p = provById(selectedId); if (!p) return;
    p.enabled = e.target.checked;
    renderList();
    const badge = $('detailBadge');
    badge.textContent = p.enabled ? '已启用' : '已禁用';
    badge.classList.toggle('off', !p.enabled);
  });
  $('f_name').addEventListener('input', (e) => {
    const p = provById(selectedId); if (!p) return;
    p.name = e.target.value;
    $('detailName').textContent = p.name || p.id;
    const card = document.querySelector(`.model-card[data-id="${CSS.escape(p.id)}"] .model-name`);
    if (card) card.textContent = p.name || p.id;
  });
  $('f_model').addEventListener('input', (e) => { const p = provById(selectedId); if (p) p.model = e.target.value; });
  $('f_base_url').addEventListener('input', (e) => { const p = provById(selectedId); if (p) p.base_url = e.target.value; });
  $('f_api_key').addEventListener('input', (e) => { const p = provById(selectedId); if (p) p._newKey = e.target.value; });

  $('toggleKeyBtn').addEventListener('click', () => {
    const inp = $('f_api_key');
    inp.type = inp.type === 'password' ? 'text' : 'password';
  });

  $('testBtn').addEventListener('click', testConnection);
}

/* 测试连接：用 /generate/providers 反映后端识别到的配置状态 */
async function testConnection() {
  const p = provById(selectedId); if (!p) return;
  const box = $('testResult');
  box.classList.remove('hidden');
  box.textContent = '检测中...';
  try {
    const res = await fetch('/generate/providers');
    const data = await res.json();
    const found = (data.providers || []).find((x) => x.id === p.id);
    if (!found) {
      box.textContent = '该模型不在后端可调用列表中（仅 sensenova / agnes 支持真实调用）。';
      return;
    }
    box.textContent = `后端识别：${found.configured ? '已配置密钥 ✓' : '未配置密钥 ✗'} · 真实生图开关：${data.real_enabled ? '开启' : '关闭'} · 模型：${found.model || '—'}`;
  } catch (e) {
    box.textContent = '检测失败：' + e.message;
  }
}

/* ===== 全局生成参数 ===== */
function renderGeneration(gen) {
  $('gen_temperature').value = gen.temperature ?? 0.8;
  $('tempVal').textContent = gen.temperature ?? 0.8;
  $('gen_max_tokens').value = gen.max_tokens ?? 1024;
  $('gen_n').value = gen.n ?? 1;
  $('gen_size').value = gen.size ?? '';
}

/* ===== 载入 / 保存 ===== */
async function load() {
  try {
    const res = await fetch(API);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    cfg = await res.json();
    (cfg.providers || []).forEach((p) => { p._newKey = ''; });
    if (!selectedId || !provById(selectedId)) selectedId = (cfg.providers[0] || {}).id || null;
    renderList();
    renderDetail();
    renderGeneration(cfg.generation || {});
  } catch (e) {
    toast('载入失败：' + e.message);
  }
}

function collect() {
  const providers = (cfg.providers || []).map((p) => ({
    id: p.id,
    name: (p.name || '').trim() || p.id,
    provider_type: p.provider_type || p.id,
    base_url: (p.base_url || '').trim(),
    model: (p.model || '').trim(),
    api_key: (p._newKey || '').trim(), // 留空→后端保留原值
    enabled: !!p.enabled,
    capabilities: p.capabilities || [],
  }));
  return {
    providers,
    default_provider: cfg.default_provider,
    generation: {
      temperature: parseFloat($('gen_temperature').value),
      max_tokens: parseInt($('gen_max_tokens').value, 10) || 1024,
      n: parseInt($('gen_n').value, 10) || 1,
      size: $('gen_size').value.trim(),
      stop: (cfg.generation && cfg.generation.stop) || [],
    },
  };
}

async function save() {
  try {
    const res = await fetch(API, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(collect()),
    });
    if (!res.ok) {
      let detail = 'HTTP ' + res.status;
      try { const j = await res.json(); if (j.error) detail = j.error; } catch {}
      throw new Error(detail);
    }
    cfg = await res.json();
    (cfg.providers || []).forEach((p) => { p._newKey = ''; });
    if (!provById(selectedId)) selectedId = (cfg.providers[0] || {}).id || null;
    renderList();
    renderDetail();
    renderGeneration(cfg.generation || {});
    toast('已保存 ✓');
  } catch (e) {
    toast('保存失败：' + e.message);
  }
}

$('gen_temperature').addEventListener('input', (e) => { $('tempVal').textContent = e.target.value; });
$('saveBtn').addEventListener('click', save);
$('reloadBtn').addEventListener('click', load);

bindDetailInputs();
load();
