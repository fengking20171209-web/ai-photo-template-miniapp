// AI Photo Template Miniapp — app.js (重构版，适配极简布局)
import { escapeHtml } from './utils.js';
import { api, trackEvent } from './api.js';
import { tokenConcepts, conceptsOf, topMatches, recommend } from './cre.js';
import {
  CP_FIELDS, CP_POSE, CP_LIGHT, CP_CAMERA, CP_STYLE_BASE,
  cpTokens, cpConcepts, cpLibHay, cpBestLib, cpBestModel,
  cpInferBg, cpInferOutfit, cpLightFor, cpStyleExtra, cpRenderDraft, cpParseDraft, composeDraft,
} from './copilot.js';
import { DEFAULT_IDENTITY_PROMPT, DEFAULT_MODEL_NEGATIVE, applyModelIdentity } from './identity.js';

/* ===== 常量 ===== */
const FAVORITES_KEY = 'apt_favorites';
const DEMO_TEMPLATES = ['ancient_diaochan', 'fantasy_01', 'career_flight_attendant', 'portrait_soft_airy_window'];
const DEMO_STEPS = [
  { action: 'select', delay: 2500, desc: '选择模板' },
  { action: 'generate', delay: 3500, desc: '生成中' },
  { action: 'result', delay: 4000, desc: '展示结果' },
];

/* ===== 状态 ===== */
function loadFavorites() {
  try { return JSON.parse(localStorage.getItem(FAVORITES_KEY) || '[]'); } catch { return []; }
}
function saveFavorites(list) {
  localStorage.setItem(FAVORITES_KEY, JSON.stringify(list));
}

let demoTimer = null;
let demoStepIndex = 0;
let demoTemplateIndex = 0;

const state = {
  templates: [],
  selectedId: null,
  currentResult: null,
  currentImageUrl: null,
  activeCategory: '全部',
  searchQuery: '',
  sidebarCollapsed: false,
  favorites: loadFavorites(),
  batchSelected: new Set(),
  queue: [],
  queueRunning: false,
  demoMode: false,
  quickFilter: null,
  controlExpanded: false,
  refImage: null,       // 图生图参考图(Data URI)
  refImageName: '',
  selectedTags: [],     // 提示词库已选词
  variations: [],       // 本次会话生成的变体图
  models: [],           // 模特库
  activeModel: null,    // 当前调用的模特
  editingModelId: null, // 正在编辑的模特id
  modelRefImage: null,  // 弹窗里待保存的参考脸(Data URI)
  backgrounds: [],      // 背景库(只读JSON)
  outfits: [],          // 服装库(只读JSON)
  assetsLoaded: false,
  assetTags: { bg: new Set(), outfit: new Set() },  // 多标签筛选
  assetSearch: { bg: '', outfit: '' },
  assetUsage: {},        // CRE v2: 资源用量计数 {id: count}(localStorage)
  context: { concepts: new Set() },  // CRE v2: 会话上下文概念袋
  lastRec: null,         // 最近一次推荐来源 {kind, item}(供模式切换重渲染)
  gallerySelect: { active: false, ids: new Set() },  // 精品库多选管理
};

/* ===== DOM 引用 ===== */
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

const els = {
  // 侧边栏
  sidebar: $('#sidebar'),
  sidebarToggle: $('#sidebarToggle'),
  showSidebarBtn: $('#showSidebarBtn'),
  templateList: $('#templateList'),
  categoryFilter: $('#categoryFilter'),
  quickFilters: $('#quickFilters'),
  templateSearch: $('#templateSearch'),
  clearSearchBtn: $('#clearSearchBtn'),

  // 状态
  statusDot: $('#statusDot'),
  statusText: $('#statusText'),

  // 图片舞台
  imageStage: $('#imageStage'),
  stagePlaceholder: $('#stagePlaceholder'),
  resultImage: $('#resultImage'),
  stageLoading: $('#stageLoading'),
  loadingText: $('#loadingText'),
  loadingProgressWrap: $('#loadingProgressWrap'),
  loadingProgressBar: $('#loadingProgressBar'),
  imageActions: $('#imageActions'),
  stepIndicator: $('#stepIndicator'),

  // 控制栏
  controlBar: $('#controlBar'),
  controlCollapsed: $('#controlCollapsed'),
  controlExpanded: $('#controlExpanded'),
  templateChip: $('#templateChip'),
  templateChipLabel: $('#templateChipLabel'),
  promptInline: $('#promptInline'),
  generateBtn: $('#generateBtn'),
  expandCloseBtn: $('#expandCloseBtn'),
  expCategory: $('#expCategory'),
  expTitle: $('#expTitle'),
  expMeta: $('#expMeta'),
  expScene: $('#expScene'),
  promptInput: $('#promptInput'),
  generateTemplateBtn: $('#generateTemplateBtn'),

  // 操作按钮
  regenBtn: $('#regenBtn'),
  downloadBtn: $('#downloadBtn'),
  copyPromptBtn: $('#copyPromptBtn'),
  zoomBtn: $('#zoomBtn'),

  // 作品集
  galleryGrid: $('#galleryGrid'),
  refreshGalleryBtn: $('#refreshGalleryBtn'),

  // 上传
  fileInput: $('#fileInput'),
  selectFilesBtn: $('#selectFilesBtn'),
  uploadDropzone: $('#uploadDropzone'),
  uploadProgress: $('#uploadProgress'),

  // 批量
  batchBar: $('#batchBar'),
  batchCount: $('#batchCount'),
  batchClearBtn: $('#batchClearBtn'),
  batchGenerateBtn: $('#batchGenerateBtn'),

  // 灯箱
  lightbox: $('#lightbox'),
  lightboxImg: $('#lightboxImg'),
  lightboxBackdrop: $('#lightboxBackdrop'),
  lightboxClose: $('#lightboxClose'),

  // Demo
  demoBtn: $('#demoBtn'),
};

/* ===== 状态栏 ===== */
function setStatus(text, isError = false) {
  if (els.statusText) els.statusText.textContent = text;
  if (els.statusDot) {
    els.statusDot.className = 'status-dot' + (isError ? ' err' : ' ok');
  }
}

/* ===== Tab 切换 ===== */
$$('.tab-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    $$('.tab-btn').forEach((b) => b.classList.remove('active'));
    $$('.tab-panel').forEach((p) => p.classList.remove('active'));
    btn.classList.add('active');
    const panel = document.getElementById('tab-' + btn.dataset.tab);
    if (panel) panel.classList.add('active');
    if (btn.dataset.tab === 'gallery') loadGallery();
    if (btn.dataset.tab === 'models') renderModelsView();
    if (btn.dataset.tab === 'backgrounds') openAssetLib('bg');
    if (btn.dataset.tab === 'outfits') openAssetLib('outfit');
  });
});

function switchTab(name) {
  $$('.tab-btn').forEach((b) => b.classList.toggle('active', b.dataset.tab === name));
  $$('.tab-panel').forEach((p) => p.classList.toggle('active', p.id === 'tab-' + name));
  if (name === 'gallery') loadGallery();
  if (name === 'models') renderModelsView();
  if (name === 'backgrounds') openAssetLib('bg');
  if (name === 'outfits') openAssetLib('outfit');
}

/* ===== 色调切换 ===== */
const THEME_KEY = 'apt_theme';
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme === 'dark' ? '' : theme);
  if (theme === 'dark') document.documentElement.removeAttribute('data-theme');
  localStorage.setItem(THEME_KEY, theme);
  $$('.theme-dot').forEach(d => d.classList.toggle('active', d.dataset.theme === theme));
}
$$('.theme-dot').forEach(dot => {
  dot.addEventListener('click', () => applyTheme(dot.dataset.theme));
});
applyTheme(localStorage.getItem(THEME_KEY) || 'dark');

/* ===== 模型选择器 ===== */
const modelSelect = $('#modelSelect');

// 从后端加载可用模型列表
async function loadProviders() {
  try {
    const data = await api('/generate/providers');
    if (!modelSelect) return;
    modelSelect.innerHTML = '';
    // 始终有 mock
    const mockOpt = document.createElement('option');
    mockOpt.value = 'mock'; mockOpt.textContent = '🎭 Mock（测试）';
    modelSelect.appendChild(mockOpt);
    // 真实模型
    (data.providers || []).forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = (p.id === 'agnes' ? '✨ ' : '⚡ ') + p.name;
      if (!p.configured) { opt.textContent += ' (未配置)'; opt.disabled = true; }
      modelSelect.appendChild(opt);
    });
    // 默认选中后端推荐的 provider
    const def = data.real_enabled ? (data.default || 'sensenova') : 'mock';
    modelSelect.value = def;
  } catch {
    // 加载失败保留静态选项
  }
}

function getSelectedProvider() {
  return modelSelect?.value || 'mock';
}

/* ===== 尺寸随模型联动 ===== */
const MODEL_SIZES = {
  sensenova: [
    ['2048x2048', '2048×2048 · 1:1 方图'],
    ['1824x2272', '1824×2272 · 3:4 竖图'],
    ['1664x2496', '1664×2496 · 2:3 竖图'],
    ['2272x1824', '2272×1824 · 4:3 横图'],
    ['1536x2752', '1536×2752 · 9:16 长竖'],
    ['2752x1536', '2752×1536 · 16:9 宽幅'],
  ],
  agnes: [
    ['1024x1024', '1024×1024 · 1:1 方图'],
    ['1024x1365', '1024×1365 · 3:4 竖图'],
    ['1024x1536', '1024×1536 · 2:3 竖图'],
    ['1365x1024', '1365×1024 · 4:3 横图'],
    ['1536x1024', '1536×1024 · 3:2 横图'],
    ['768x1365', '768×1365 · 9:16 长竖'],
    ['1365x768', '1365×768 · 16:9 宽幅'],
  ],
  mock: [],
};

function renderSizeOptions(provider) {
  const sel = document.getElementById('sizeSelect');
  if (!sel) return;
  const prev = sel.value;
  const list = MODEL_SIZES[provider] || [];
  let html = '<option value="">跟随模板 / 默认</option>';
  for (const [v, label] of list) html += `<option value="${v}">${label}</option>`;
  sel.innerHTML = html;
  // 保留之前的选择（若新模型仍支持），否则回到默认
  sel.value = [...sel.options].some((o) => o.value === prev) ? prev : '';
}

modelSelect?.addEventListener('change', () => renderSizeOptions(getSelectedProvider()));
function toggleSidebar() {
  state.sidebarCollapsed = !state.sidebarCollapsed;
  els.sidebar.classList.toggle('collapsed', state.sidebarCollapsed);
}

els.sidebarToggle?.addEventListener('click', toggleSidebar);
els.showSidebarBtn?.addEventListener('click', () => {
  if (state.sidebarCollapsed) toggleSidebar();
});

/* ===== 控制栏展开/收起 ===== */
function expandControl() {
  state.controlExpanded = true;
  els.controlCollapsed.classList.add('hidden');
  els.controlExpanded.classList.remove('hidden');
}

function collapseControl() {
  state.controlExpanded = false;
  els.controlExpanded.classList.add('hidden');
  els.controlCollapsed.classList.remove('hidden');
}

// 点击模板 chip 展开
els.templateChip?.addEventListener('click', expandControl);
// 点击提示词输入框展开
els.promptInline?.addEventListener('focus', expandControl);
// 关闭按钮
els.expandCloseBtn?.addEventListener('click', collapseControl);

// 同步两个输入框内容
els.promptInline?.addEventListener('input', () => {
  if (els.promptInput) els.promptInput.value = els.promptInline.value;
});
els.promptInput?.addEventListener('input', () => {
  if (els.promptInline) els.promptInline.value = els.promptInput.value;
});

/* ===== 模板列表 ===== */
async function loadTemplates() {
  try {
    setStatus('加载中...');
    const data = await api('/api/templates');
    state.templates = data.items || [];
    renderCategoryFilter();
    renderQuickFilters();
    await renderTemplateList();
    setStatus(`${state.templates.length} 个模板`);
    if (!state.selectedId && state.templates.length > 0) {
      selectTemplate(state.templates[0].template_id);
    }
  } catch (err) {
    setStatus('加载失败', true);
    if (els.templateList) {
      els.templateList.innerHTML = `<div class="template-empty">加载失败: ${escapeHtml(err.message)}</div>`;
    }
  }
}

function renderCategoryFilter() {
  if (!els.categoryFilter) return;
  const categories = ['全部', ...new Set(state.templates.map((t) => t.category))];
  els.categoryFilter.innerHTML = '';
  for (const cat of categories) {
    const btn = document.createElement('button');
    btn.className = 'filter-chip' + (cat === state.activeCategory ? ' active' : '');
    btn.textContent = cat;
    btn.addEventListener('click', async () => {
      state.activeCategory = cat;
      state.quickFilter = null;
      renderQuickFilters();
      renderCategoryFilter();
      await renderTemplateList();
    });
    els.categoryFilter.appendChild(btn);
  }
}

function renderQuickFilters() {
  if (!els.quickFilters) return;
  els.quickFilters.querySelectorAll('.qf-btn').forEach((btn) => {
    const mode = btn.dataset.qf;
    btn.classList.toggle('active', state.quickFilter === mode);
    btn.onclick = async () => {
      state.quickFilter = state.quickFilter === mode ? null : mode;
      state.searchQuery = '';
      if (els.templateSearch) els.templateSearch.value = '';
      if (els.clearSearchBtn) els.clearSearchBtn.classList.add('hidden');
      state.activeCategory = '全部';
      renderCategoryFilter();
      renderQuickFilters();
      await renderTemplateList();
    };
  });
}

async function renderTemplateList() {
  if (!els.templateList) return;
  els.templateList.innerHTML = '';
  let filtered;

  if (state.quickFilter === 'recommended') {
    try {
      const data = await api('/api/templates/recommended?limit=12');
      filtered = data.items || [];
    } catch { filtered = []; }
  } else if (state.quickFilter === 'favorites') {
    filtered = state.templates.filter((t) => state.favorites.includes(t.template_id));
  } else if (state.quickFilter === 'recent') {
    try {
      const data = await api('/api/templates/recent?limit=12');
      filtered = data.items || [];
    } catch { filtered = []; }
  } else if (state.searchQuery || state.activeCategory !== '全部') {
    try {
      const params = new URLSearchParams();
      if (state.searchQuery) params.append('q', state.searchQuery);
      if (state.activeCategory !== '全部') params.append('category', state.activeCategory);
      params.append('page', '1');
      params.append('limit', '100');
      const data = await api(`/templates/search?${params.toString()}`);
      filtered = data.items || [];
    } catch { filtered = []; }
  } else {
    filtered = state.templates;
  }

  if (filtered.length === 0) {
    const msg = state.quickFilter === 'favorites' ? '暂无收藏'
      : state.searchQuery ? `未找到「${escapeHtml(state.searchQuery)}」`
      : '暂无模板';
    els.templateList.innerHTML = `<div class="template-empty">${msg}</div>`;
    renderBatchBar();
    return;
  }

  for (const t of filtered) {
    const btn = document.createElement('button');
    const isFav = state.favorites.includes(t.template_id);
    const isBatch = state.batchSelected.has(t.template_id);
    btn.className = 'template-card' + (t.template_id === state.selectedId ? ' active' : '');
    btn.dataset.id = t.template_id;
    btn.innerHTML = `
      <span class="batch-check${isBatch ? ' checked' : ''}" data-batch-id="${escapeHtml(t.template_id)}"></span>
      <span class="cat">${escapeHtml(t.category)}</span>
      <span class="ttl">${escapeHtml(t.title)}</span>
      <span class="sub">${escapeHtml(t.style || '')} · ${escapeHtml(t.ratio || '')}</span>
      <span class="fav-btn${isFav ? ' active' : ''}" data-fav-id="${escapeHtml(t.template_id)}" title="${isFav ? '取消收藏' : '收藏'}">★</span>
    `;
    btn.addEventListener('click', (e) => {
      if (e.target.closest('.fav-btn')) { e.stopPropagation(); toggleFavorite(t.template_id); return; }
      if (e.target.closest('.batch-check')) { e.stopPropagation(); toggleBatch(t.template_id); return; }
      selectTemplate(t.template_id);
    });
    els.templateList.appendChild(btn);
  }
  renderBatchBar();
}

function toggleFavorite(templateId) {
  const idx = state.favorites.indexOf(templateId);
  if (idx >= 0) state.favorites.splice(idx, 1);
  else { state.favorites.push(templateId); trackEvent('favorite', { template_id: templateId }); }
  saveFavorites(state.favorites);
  renderTemplateList();
}

function toggleBatch(templateId) {
  if (state.batchSelected.has(templateId)) state.batchSelected.delete(templateId);
  else state.batchSelected.add(templateId);
  renderTemplateList();
}

function renderBatchBar() {
  const count = state.batchSelected.size;
  if (!els.batchBar) return;
  els.batchBar.classList.toggle('hidden', count === 0);
  if (els.batchCount) els.batchCount.textContent = `已选 ${count} 个`;
}

async function selectTemplate(id) {
  state.selectedId = id;
  await renderTemplateList();
  trackEvent('click', { template_id: id });

  const t = state.templates.find((x) => x.template_id === id);
  if (!t) return;

  // 更新控制栏 chip
  if (els.templateChipLabel) {
    els.templateChipLabel.textContent = t.title;
    els.templateChip?.classList.add('has-template');
  }

  // 更新展开面板
  if (els.expCategory) els.expCategory.textContent = t.category;
  if (els.expTitle) els.expTitle.textContent = t.title;
  if (els.expMeta) {
    els.expMeta.innerHTML = [
      t.ratio && `<span class="meta-chip">画幅 ${escapeHtml(t.ratio)}</span>`,
      t.style && `<span class="meta-chip">${escapeHtml(t.style)}</span>`,
      t.face_lock != null && `<span class="meta-chip">脸部保真: ${t.face_lock ? '开启' : '关闭'}</span>`,
    ].filter(Boolean).join('');
  }
  if (els.expScene) {
    els.expScene.textContent = [t.scene, t.clothing].filter(Boolean).join(' · ');
  }

  // 注入 AI 助手上下文
  if (window.chatContext) {
    window.chatContext.templateTitle = t.title;
    window.chatContext.templateCategory = t.category;
    window.chatContext.templateScene = [t.scene, t.clothing].filter(Boolean).join(' · ');
  }

  // 自动展开控制栏
  expandControl();
}

/* ===== 生成图片 ===== */
function getPrompt() {
  // 组合:提示词库已选词 + 自定义提示词
  const tags = state.selectedTags.map((t) => t.label);
  const custom = (els.promptInput?.value || els.promptInline?.value || '').trim();
  return [...tags, custom].filter(Boolean).join('，');
}

async function generateFromTemplate(templateId) {
  const _hasPrompt = getPrompt();
  // DIY Prompt OS:生成只来自用户输入(标签+自定义)/模特身份/参考图,不再注入模板
  if (!_hasPrompt && !state.refImage) {
    els.promptInput?.focus();
    setStatus('请先选择提示词、输入描述，或上传参考图', true);
    return;
  }

  // 重置舞台
  els.stagePlaceholder?.classList.add('hidden');
  els.resultImage?.classList.add('hidden');
  els.imageActions?.classList.add('hidden');
  els.stageLoading?.classList.remove('hidden');
  els.stepIndicator?.classList.remove('hidden');
  if (els.loadingText) els.loadingText.textContent = '提交任务...';
  if (els.loadingProgressWrap) els.loadingProgressWrap.style.display = 'none';

  setStepActive('submit');

  // 禁用按钮
  if (els.generateBtn) { els.generateBtn.disabled = true; }
  if (els.generateTemplateBtn) { els.generateTemplateBtn.disabled = true; els.generateTemplateBtn.textContent = '生成中...'; }

  try {
    // 模拟排队
    await wait(800);
    setStepActive('generate');
    if (els.loadingText) els.loadingText.textContent = '生成中...';
    if (els.loadingProgressWrap) els.loadingProgressWrap.style.display = 'block';

    // 进度条动画
    simulateProgress(2000, (pct) => {
      if (els.loadingProgressBar) els.loadingProgressBar.style.width = pct + '%';
    });

    const provider = getSelectedProvider();
    const size = document.getElementById('sizeSelect')?.value || '';
    const background = document.getElementById('backgroundInput')?.value.trim() || '';
    let prompt = getPrompt();
    let negative = document.getElementById('negativeInput')?.value.trim() || '';
    // 严格分层:用户输入(最高) > 模特身份 > 负面词(见 identity.js)
    ({ prompt, negative } = applyModelIdentity({ basePrompt: prompt, baseNegative: negative, activeModel: state.activeModel }));
    const body = {};
    // DIY Prompt OS:不再发送 template_id(杜绝古风/貂蝉等模板自动注入)
    if (prompt) body.prompt = prompt;
    if (background) body.background = background;
    if (negative) body.negative_prompt = negative;
    if (state.refImage) body.image = state.refImage;   // 图生图/模特参考脸(后端自动用 Agnes)
    if (provider && provider !== 'mock' && !state.refImage) body.provider = provider;
    if (size) body.size = size;

    const result = await api('/generate', { method: 'POST', body: JSON.stringify(body) });
    state.currentResult = result;

    if (result.status === 'failed') throw new Error(result.error || '生成失败');

    trackEvent('generate', { template_id: templateId });
    setStepActive('finish');

    const raw = result.image_response?.raw || {};
    const imageUrls = result.image_response?.image_urls || [];
    const realUrl = imageUrls.find((u) => u && u !== '/placeholder.svg');
    if (raw.mode === 'real' && realUrl) {
      state.currentImageUrl = realUrl;
      showResultImage(realUrl);
      addVariation(realUrl);
    } else {
      // 非真实结果：明确告知原因，不再用占位图假装成功
      state.currentImageUrl = null;
      els.stageLoading?.classList.add('hidden');
      els.resultImage?.classList.add('hidden');
      els.stagePlaceholder?.classList.remove('hidden');
      const reason = raw.reason || '';
      let msg;
      if (/content_policy|Unable to generate|policy/i.test(reason)) {
        msg = '⚠️ 该描述被生图模型的内容策略拒绝，请调整提示词后重试。';
      } else if (reason) {
        msg = '生成失败（已回退占位图）：' + reason.slice(0, 160);
      } else if (raw.fallback) {
        msg = '当前为模拟模式：未开启真实生成或额度不足。';
      } else {
        msg = '当前为模拟结果。';
      }
      const hintEl = els.stagePlaceholder?.querySelector('.placeholder-hint');
      if (hintEl) hintEl.textContent = msg;
      setStatus(msg, true);
    }

    // 显示操作按钮
    els.imageActions?.classList.remove('hidden');

    // 加载优化提示词
    if (result.task_id) loadTaskPrompt(result.task_id);

    // 收起控制栏，让图片更完整
    collapseControl();

  } catch (err) {
    setStepActive('finish');
    els.stageLoading?.classList.add('hidden');
    els.stagePlaceholder?.classList.remove('hidden');
    if (els.stagePlaceholder) {
      els.stagePlaceholder.querySelector('.placeholder-hint').textContent = `生成失败: ${err.message}`;
    }
  } finally {
    if (els.generateBtn) els.generateBtn.disabled = false;
    if (els.generateTemplateBtn) {
      els.generateTemplateBtn.disabled = false;
      els.generateTemplateBtn.textContent = '生成写真';
    }
  }
}

function showResultImage(url) {
  if (!els.resultImage) return;
  els.resultImage.src = url;
  els.resultImage.onload = () => {
    els.stageLoading?.classList.add('hidden');
    els.resultImage.classList.remove('hidden');
  };
  els.resultImage.onerror = () => {
    els.stageLoading?.classList.add('hidden');
    els.stagePlaceholder?.classList.remove('hidden');
  };
  // 超时保护
  setTimeout(() => {
    if (els.stageLoading && !els.stageLoading.classList.contains('hidden')) {
      els.stageLoading.classList.add('hidden');
      els.resultImage.classList.remove('hidden');
    }
  }, 5000);
}

function setStepActive(step) {
  if (!els.stepIndicator) return;
  els.stepIndicator.querySelectorAll('.step-dot').forEach((dot) => {
    const name = dot.dataset.step;
    dot.classList.remove('active', 'done');
    if (name === step) dot.classList.add('active');
    else if (
      (step === 'generate' && name === 'submit') ||
      (step === 'finish' && (name === 'submit' || name === 'generate'))
    ) dot.classList.add('done');
  });
}

function wait(ms) { return new Promise((r) => setTimeout(r, ms)); }

async function simulateProgress(totalMs, onUpdate) {
  const interval = 150;
  const steps = totalMs / interval;
  for (let i = 0; i <= steps; i++) {
    onUpdate(Math.round((i / steps) * 90)); // 最多到90%，等真实结果
    if (i < steps) await wait(interval);
  }
}

async function loadTaskPrompt(taskId) {
  try {
    const data = await api(`/images/${encodeURIComponent(taskId)}`);
    if (data.revised_prompt && els.copyPromptBtn) {
      els.copyPromptBtn.dataset.prompt = data.revised_prompt;
    }
  } catch {}
}

/* ===== 图片操作按钮 ===== */
els.generateBtn?.addEventListener('click', () => {
  if (state.selectedId) generateFromTemplate(state.selectedId);
  else expandControl(); // 提示选择模板
});

els.generateTemplateBtn?.addEventListener('click', () => { smartGenerate(); });

els.regenBtn?.addEventListener('click', () => {
  generateFromTemplate(null);
});

els.downloadBtn?.addEventListener('click', () => {
  if (!state.currentImageUrl) return;
  const a = document.createElement('a');
  a.href = state.currentImageUrl;
  a.download = `ai-photo-${Date.now()}.png`;
  a.click();
});

els.copyPromptBtn?.addEventListener('click', async () => {
  const prompt = els.copyPromptBtn.dataset.prompt;
  if (!prompt) return;
  try {
    await navigator.clipboard.writeText(prompt);
    els.copyPromptBtn.title = '已复制 ✓';
    setTimeout(() => { els.copyPromptBtn.title = '复制提示词'; }, 2000);
  } catch {}
});

els.zoomBtn?.addEventListener('click', () => {
  if (state.currentImageUrl) openLightbox(state.currentImageUrl, '生成结果');
});

/* ===== 批量生成 ===== */
els.batchClearBtn?.addEventListener('click', () => {
  state.batchSelected.clear();
  renderTemplateList();
});

els.batchGenerateBtn?.addEventListener('click', runBatchGenerate);

/* ===== Studio 布局新增交互 ===== */
// 提示词字数统计
const promptCountEl = document.getElementById('promptCount');
els.promptInput?.addEventListener('input', () => {
  if (promptCountEl) promptCountEl.textContent = String(els.promptInput.value.length);
});

// 随机生图 → Surprise：协调随机草稿后直接生成
document.getElementById('randomGenBtn')?.addEventListener('click', () => { surpriseGenerate(); });

// 点击上传区打开文件选择
els.uploadDropzone?.addEventListener('click', (e) => {
  if (e.target.closest('input')) return;
  els.fileInput?.click();
});

// 助手快捷动作：把意图填入聊天输入框并聚焦
document.getElementById('assistantQuick')?.addEventListener('click', (e) => {
  const btn = e.target.closest('.quick-act');
  if (!btn) return;
  const chatInput = document.getElementById('chatInput');
  if (!chatInput) return;
  const base = btn.dataset.quick || btn.textContent.trim();
  const cur = getPrompt();
  chatInput.value = cur ? `${base}：${cur}` : base;
  chatInput.focus();
});

// 背景预设快选 -> 填入背景输入框
document.getElementById('bgPresets')?.addEventListener('click', (e) => {
  const chip = e.target.closest('.bg-chip');
  if (!chip) return;
  const input = document.getElementById('backgroundInput');
  if (input) { input.value = chip.dataset.bg || chip.textContent.trim(); input.focus(); }
});

/* ===== 提示词库(标签式选词) ===== */
const PROMPT_LIBRARY = [
  { name: '场景', en: 'Scene', tags: ['专业影棚', '城市夜景', '海边沙滩', '都市街拍', '室内书房', '咖啡馆', '森林自然', '庭院花园', '落日余晖', '雪后初晴', '图书馆', '楼顶天台'] },
  { name: '人物', en: 'Character', tags: ['清新少女', '知性女性', '商务精英', '文艺青年', '运动活力', '优雅御姐', '元气甜美', '高冷气质'] },
  { name: '服装', en: 'Outfit', tags: ['商务正装', '休闲日常', '汉服古风', '晚礼服', '针织毛衣', '牛仔风', '职业套装', '风衣大衣', '学院风', '运动装'] },
  { name: '姿态', en: 'Pose', tags: ['自然站姿', '优雅坐姿', '侧身回眸', '倚靠', '行走抓拍', '托腮', '双手插袋', '回头浅笑'] },
  { name: '光影', en: 'Lighting', tags: ['柔和自然光', '逆光剪影', '伦勃朗光', '影棚柔光', '黄金时刻', '窗边光', '高调亮光', '低调暗调'] },
  { name: '镜头', en: 'Camera', tags: ['面部特写', '半身像', '全身像', '中近景', '广角环境', '浅景深虚化', '电影宽幅'] },
  { name: '风格', en: 'Style', tags: ['写实摄影', '电影质感', '日系清新', '胶片颗粒', '时尚大片', '复古港风', '黑白影像', '杂志封面'] },
];

function renderLibrary(filter = '') {
  const box = document.getElementById('promptLibrary');
  if (!box) return;
  const f = (filter || '').trim();
  box.innerHTML = '';
  PROMPT_LIBRARY.forEach((cat, ci) => {
    const matched = f ? cat.tags.filter((t) => t.includes(f)) : cat.tags;
    if (f && matched.length === 0) return;
    const open = f ? true : ci === 0;
    const el = document.createElement('div');
    el.className = 'lib-cat' + (open ? ' open' : '');
    el.innerHTML = `
      <div class="lib-cat-head">
        <span class="cat-name">${cat.name}</span><span class="cat-en">${cat.en}</span>
        <span class="cat-count">${cat.tags.length}</span>
        <svg class="chev" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
      </div>
      <div class="lib-cat-body">
        ${matched.map((t) => `<button type="button" class="lib-tag${state.selectedTags.some((s) => s.label === t) ? ' selected' : ''}" data-tag="${escapeHtml(t)}">${escapeHtml(t)}</button>`).join('')}
      </div>`;
    box.appendChild(el);
  });
}

function renderSelectedTags() {
  const box = document.getElementById('selectedTags');
  const cnt = document.getElementById('selectedCount');
  if (cnt) cnt.textContent = String(state.selectedTags.length);
  if (!box) return;
  if (state.selectedTags.length === 0) {
    box.innerHTML = '<span class="selected-empty">点上方词条添加，或在“生成设置”里自定义</span>';
    return;
  }
  box.innerHTML = state.selectedTags.map((s) => `<span class="sel-chip">${escapeHtml(s.label)}<span class="x" data-rm="${escapeHtml(s.label)}">×</span></span>`).join('');
  box.querySelectorAll('.x').forEach((x) => x.addEventListener('click', () => toggleTag(x.dataset.rm)));
}

function toggleTag(label) {
  const i = state.selectedTags.findIndex((s) => s.label === label);
  if (i >= 0) state.selectedTags.splice(i, 1);
  else state.selectedTags.push({ label });
  renderSelectedTags();
  document.querySelectorAll('#promptLibrary .lib-tag').forEach((b) => {
    b.classList.toggle('selected', state.selectedTags.some((s) => s.label === b.dataset.tag));
  });
}

document.getElementById('promptLibrary')?.addEventListener('click', (e) => {
  const head = e.target.closest('.lib-cat-head');
  if (head) { head.parentElement.classList.toggle('open'); return; }
  const tag = e.target.closest('.lib-tag');
  if (tag) toggleTag(tag.dataset.tag);
});
document.getElementById('librarySearch')?.addEventListener('input', (e) => renderLibrary(e.target.value));
document.getElementById('addCustomTagBtn')?.addEventListener('click', () => {
  const inp = document.getElementById('librarySearch');
  const v = (inp?.value || '').trim();
  if (!v) return;
  if (!state.selectedTags.some((s) => s.label === v)) state.selectedTags.push({ label: v });
  renderSelectedTags();
  if (inp) inp.value = '';
  renderLibrary('');
});
document.getElementById('clearTagsBtn')?.addEventListener('click', () => {
  state.selectedTags = [];
  renderSelectedTags();
  renderLibrary(document.getElementById('librarySearch')?.value || '');
});
document.getElementById('historyFooterBtn')?.addEventListener('click', () => switchTab('gallery'));
document.getElementById('favFooterBtn')?.addEventListener('click', () => {
  document.getElementById('sidebar')?.classList.add('open');
  state.quickFilter = 'favorites';
  renderQuickFilters();
  renderTemplateList();
});

/* ===== 模特库(本地存储,无 LoRA,靠参考脸图+一致性提示词) ===== */
const MODELS_KEY = 'apt_models';
// 身份一致性常量与注入逻辑见 ./identity.js（纯函数，可测）

async function fetchModels() {
  try { const d = await api('/api/models'); state.models = d.models || []; }
  catch { state.models = []; }
}
async function migrateLocalModels() {
  // 一次性:把旧的本地 localStorage 模特迁移到后端,迁移后清除本地副本
  try {
    const raw = localStorage.getItem(MODELS_KEY);
    if (!raw) return;
    const local = JSON.parse(raw);
    if (Array.isArray(local) && local.length && state.models.length === 0) {
      for (const m of local) {
        await api('/api/models', { method: 'POST', body: JSON.stringify({
          name: m.name, reference_image: m.reference_image, identity_prompt: m.identity_prompt,
          negative_prompt: m.negative_prompt, tags: m.tags || [],
        }) });
      }
      await fetchModels();
    }
    localStorage.removeItem(MODELS_KEY);
  } catch { /* ignore */ }
}

function updateActiveModelBar() {
  const bar = document.getElementById('activeModelBar');
  const nameEl = document.getElementById('activeModelName');
  const lockEl = document.getElementById('activeModelLock');
  const clearBtn = document.getElementById('clearModelBtn');
  const m = state.activeModel;
  if (nameEl) nameEl.textContent = m ? m.name : '未选择';
  if (lockEl) lockEl.textContent = m ? '🔒 已锁定脸' : '未锁定';
  bar?.classList.toggle('locked', !!m);
  if (clearBtn) clearBtn.hidden = !m;
}

async function useModel(id) {
  const m = state.models.find((x) => x.id === id);
  if (!m) return;
  state.activeModel = m;
  if (m.reference_image) { state.refImage = m.reference_image; state.refImageName = m.name + ' · 参考脸'; renderRefImage(); }
  updateActiveModelBar();
  switchTab('generate');
  setStatus(`已调用模特「${m.name}」,生成将保持同一张脸`);
  conceptsOf('model', m).forEach((c) => state.context.concepts.add(c));  // CRE v2: 模特进入会话上下文
  cpRunAsync(() => renderSmartRecommend('model', m));   // CRE 后台渲染,不阻塞
  // 用量计数:fire-and-forget,不进关键路径
  api('/api/models/' + id + '/use', { method: 'POST' }).then((u) => { m.usage_count = u.usage_count; }).catch(() => { /* ignore */ });
}

document.getElementById('clearModelBtn')?.addEventListener('click', () => {
  if (state.activeModel && state.refImageName === state.activeModel.name + ' · 参考脸') {
    state.refImage = null; state.refImageName = ''; renderRefImage();
  }
  state.activeModel = null;
  updateActiveModelBar();
  setStatus('已取消当前模特');
});
document.getElementById('pickModelBtn')?.addEventListener('click', () => switchTab('models'));

function renderModelsView(filter = '') {
  const grid = document.getElementById('modelsGrid');
  if (!grid) return;
  const f = (filter || '').trim().toLowerCase();
  let list = state.models;
  if (f) list = list.filter((m) => (m.name || '').toLowerCase().includes(f) || (m.tags || []).some((t) => t.toLowerCase().includes(f)));
  const cards = list.map((m) => {
    const active = state.activeModel && state.activeModel.id === m.id;
    const img = m.reference_image ? `<img src="${escapeHtml(m.reference_image)}" alt="${escapeHtml(m.name)}" />` : '<div class="no-face">无参考脸</div>';
    const tags = (m.tags || []).slice(0, 3).map((t) => `<span class="mt">${escapeHtml(t)}</span>`).join('');
    return `
      <div class="model-card${active ? ' active-model' : ''}" data-id="${escapeHtml(m.id)}">
        <div class="model-card-img">${img}</div>
        <div class="model-card-body">
          <div class="model-card-name">${escapeHtml(m.name)}</div>
          <div class="model-card-tags">${tags}</div>
          <div class="model-card-meta"><span>使用 ${m.usage_count || 0} 次</span></div>
          <div class="model-card-actions">
            <button class="use-btn" data-act="use">调用</button>
            <button data-act="variant">生成变体</button>
          </div>
          <div class="model-card-actions">
            <button data-act="edit">编辑</button>
            <button data-act="del">删除</button>
          </div>
        </div>
      </div>`;
  }).join('');
  const newCard = `<button class="model-new-card" id="gridNewModel">＋ 新建模特</button>`;
  grid.innerHTML = (list.length === 0 && !f ? '<div class="models-empty">还没有模特，点「＋ 新建模特」创建你的专属模特</div>' : cards) + newCard;

  grid.querySelectorAll('.model-card').forEach((card) => {
    card.querySelectorAll('button[data-act]').forEach((b) => {
      b.addEventListener('click', (e) => {
        e.stopPropagation();
        const id = card.dataset.id;
        if (b.dataset.act === 'use') useModel(id);
        else if (b.dataset.act === 'variant') useModel(id).then(() => generateFromTemplate(state.selectedId));
        else if (b.dataset.act === 'edit') openModelModal(id);
        else if (b.dataset.act === 'del') {
          if (confirm('确定删除该模特？')) {
            api('/api/models/' + id, { method: 'DELETE' }).then(async () => {
              if (state.activeModel?.id === id) { state.activeModel = null; updateActiveModelBar(); }
              await fetchModels();
              renderModelsView(filter);
            }).catch(() => setStatus('删除失败', true));
          }
        }
      });
    });
  });
  document.getElementById('gridNewModel')?.addEventListener('click', () => openModelModal());
}

/* ----- 新建/编辑弹窗 ----- */
function openModelModal(id = null) {
  state.editingModelId = id;
  const m = id ? state.models.find((x) => x.id === id) : null;
  document.getElementById('modelModalTitle').textContent = m ? '编辑模特' : '新建模特';
  document.getElementById('modelName').value = m ? m.name : '';
  document.getElementById('modelTags').value = m ? (m.tags || []).join(', ') : '';
  document.getElementById('modelIdentityPrompt').value = m ? m.identity_prompt : DEFAULT_IDENTITY_PROMPT;
  document.getElementById('modelNegativePrompt').value = m ? m.negative_prompt : DEFAULT_MODEL_NEGATIVE;
  state.modelRefImage = m ? (m.reference_image || null) : null;
  const prev = document.getElementById('modelRefPreview');
  const ph = document.getElementById('modelRefPlaceholder');
  if (state.modelRefImage) { prev.src = state.modelRefImage; prev.classList.remove('hidden'); ph.classList.add('hidden'); }
  else { prev.classList.add('hidden'); ph.classList.remove('hidden'); }
  document.getElementById('modelModal').classList.remove('hidden');
}
function closeModelModal() { document.getElementById('modelModal')?.classList.add('hidden'); }

document.getElementById('newModelBtn')?.addEventListener('click', () => openModelModal());
document.getElementById('modelModalClose')?.addEventListener('click', closeModelModal);
document.getElementById('modelModalCancel')?.addEventListener('click', closeModelModal);
document.getElementById('modelRefDrop')?.addEventListener('click', () => document.getElementById('modelRefInput')?.click());
document.getElementById('modelRefInput')?.addEventListener('change', async (e) => {
  const file = e.target.files?.[0];
  if (!file || !file.type.startsWith('image/')) return;
  if (file.size > 10 * 1024 * 1024) { setStatus('参考图需小于 10MB', true); return; }
  state.modelRefImage = await fileToDataURL(file);
  const prev = document.getElementById('modelRefPreview');
  prev.src = state.modelRefImage; prev.classList.remove('hidden');
  document.getElementById('modelRefPlaceholder').classList.add('hidden');
});
document.getElementById('modelModalSave')?.addEventListener('click', async () => {
  const name = document.getElementById('modelName').value.trim();
  if (!name) { setStatus('请填写模特名称', true); return; }
  if (!state.modelRefImage) { setStatus('请上传参考脸图(一致性核心)', true); return; }
  const tags = document.getElementById('modelTags').value.split(/[,，]/).map((s) => s.trim()).filter(Boolean);
  const identity_prompt = document.getElementById('modelIdentityPrompt').value.trim() || DEFAULT_IDENTITY_PROMPT;
  const negative_prompt = document.getElementById('modelNegativePrompt').value.trim() || DEFAULT_MODEL_NEGATIVE;
  const payload = { name, reference_image: state.modelRefImage, identity_prompt, negative_prompt, tags };
  const saveBtn = document.getElementById('modelModalSave');
  saveBtn.disabled = true;
  try {
    if (state.editingModelId) {
      await api('/api/models/' + state.editingModelId, { method: 'PUT', body: JSON.stringify(payload) });
    } else {
      await api('/api/models', { method: 'POST', body: JSON.stringify(payload) });
    }
    await fetchModels();
    // 若编辑的是当前模特,刷新引用
    if (state.activeModel) state.activeModel = state.models.find((x) => x.id === state.activeModel.id) || state.activeModel;
    closeModelModal();
    renderModelsView();
    setStatus('模特已保存 ✓');
  } catch (e) {
    setStatus('保存失败：' + (e?.message || ''), true);
  } finally {
    saveBtn.disabled = false;
  }
});

/* ----- 随机模特生成(加权偏好高频模特) ----- */
function weightedRandomModel() {
  if (state.models.length === 0) return null;
  const weights = state.models.map((m) => (m.usage_count || 0) + 1);
  const total = weights.reduce((a, b) => a + b, 0);
  let r = Math.random() * total;
  for (let i = 0; i < state.models.length; i++) { r -= weights[i]; if (r <= 0) return state.models[i]; }
  return state.models[0];
}
function pickRandom(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
document.getElementById('randomModelBtn')?.addEventListener('click', () => {
  const m = weightedRandomModel();
  if (!m) { setStatus('模特库为空,先新建一个模特', true); openModelModal(); return; }
  const scene = PROMPT_LIBRARY.find((c) => c.name === '场景');
  const outfit = PROMPT_LIBRARY.find((c) => c.name === '服装');
  const pose = PROMPT_LIBRARY.find((c) => c.name === '姿态');
  state.selectedTags = [scene && { label: pickRandom(scene.tags) }, outfit && { label: pickRandom(outfit.tags) }, pose && { label: pickRandom(pose.tags) }].filter(Boolean);
  renderSelectedTags();
  renderLibrary('');
  useModel(m.id);          // 设为当前模特(含参考脸+身份词)并切到工作区
  generateFromTemplate(state.selectedId);
});

/* ===== 背景库 / 服装库（DIY：只填入可编辑 Prompt 草稿，绝不直接生图） ===== */
async function loadAssetLibs() {
  if (state.assetsLoaded) return;
  try {
    const [bg, of] = await Promise.all([
      fetch('/data/backgrounds.json').then((r) => r.json()),
      fetch('/data/outfits.json').then((r) => r.json()),
    ]);
    state.backgrounds = Array.isArray(bg) ? bg : [];
    state.outfits = Array.isArray(of) ? of : [];
    state.assetsLoaded = true;
  } catch (e) {
    setStatus('素材库加载失败', true);
  }
}

function assetCfg(kind) {
  return kind === 'bg'
    ? { data: () => state.backgrounds, kwField: 'prompt_keywords', filterFields: ['category'], label: 'Background', listId: 'bgList', filtersId: 'bgFilters', countId: 'bgCount' }
    : { data: () => state.outfits, kwField: 'fashion_keywords', filterFields: ['category', 'style_tags'], label: 'Outfit', listId: 'outfitList', filtersId: 'outfitFilters', countId: 'outfitCount' };
}
function itemTags(kind, it) {
  return kind === 'bg'
    ? [].concat(it.category || [], it.space || [], it.atmosphere || [], it.lighting || [], it.perspective || [])
    : [].concat(it.category || [], it.style_tags || [], it.fabric_tags || []);
}
function itemKeywords(kind, it) { return (kind === 'bg' ? it.prompt_keywords : it.fashion_keywords) || []; }

async function openAssetLib(kind) {
  await loadAssetLibs();
  renderAssetFilters(kind);
  renderAssetList(kind);
}

function renderAssetFilters(kind) {
  const cfg = assetCfg(kind);
  const box = document.getElementById(cfg.filtersId);
  if (!box) return;
  const universe = [];
  cfg.data().forEach((it) => cfg.filterFields.forEach((f) => (it[f] || []).forEach((v) => { if (!universe.includes(v)) universe.push(v); })));
  const active = state.assetTags[kind];
  box.innerHTML = universe.map((t) => `<button class="filter-chip${active.has(t) ? ' active' : ''}" data-tag="${escapeHtml(t)}">${escapeHtml(t)}</button>`).join('');
  box.querySelectorAll('.filter-chip').forEach((c) => c.addEventListener('click', () => {
    const t = c.dataset.tag;
    if (active.has(t)) active.delete(t); else active.add(t);
    renderAssetFilters(kind);
    renderAssetList(kind);
  }));
}

function renderAssetList(kind) {
  const cfg = assetCfg(kind);
  const list = document.getElementById(cfg.listId);
  if (!list) return;
  const q = (state.assetSearch[kind] || '').trim().toLowerCase();
  const active = state.assetTags[kind];
  let items = cfg.data();
  if (active.size) items = items.filter((it) => { const tg = itemTags(kind, it); return [...active].every((a) => tg.includes(a)); });
  if (q) items = items.filter((it) => it.name.toLowerCase().includes(q) || itemTags(kind, it).some((t) => t.toLowerCase().includes(q)) || itemKeywords(kind, it).some((k) => k.toLowerCase().includes(q)));
  const cnt = document.getElementById(cfg.countId);
  if (cnt) cnt.textContent = `${items.length} 项`;
  if (items.length === 0) { list.innerHTML = '<div class="asset-empty">没有匹配项，调整筛选或搜索</div>'; return; }
  const shown = items.slice(0, 200);
  list.innerHTML = shown.map((it) => `
    <button class="asset-item" data-id="${escapeHtml(it.id)}">
      <div class="asset-item-name">${escapeHtml(it.name)}<span class="asset-item-add">＋加入草稿</span></div>
      <div class="asset-item-tags">${itemTags(kind, it).slice(0, 4).map((t) => `<span class="at">${escapeHtml(t)}</span>`).join('')}</div>
      <div class="asset-item-kw">${escapeHtml(itemKeywords(kind, it).join(', '))}</div>
    </button>`).join('') + (items.length > 200 ? '<div class="asset-empty">仅显示前 200 项，请用搜索/筛选缩小范围</div>' : '');
  list.querySelectorAll('.asset-item').forEach((el) => el.addEventListener('click', () => {
    const it = cfg.data().find((x) => x.id === el.dataset.id);
    if (it) addToPromptDraft(kind, it);
  }));
}

// 核心：库资源只追加到可编辑 Prompt 草稿，用户改完再生成（不自动生图）
function addToPromptDraft(kind, it) {
  const label = kind === 'bg' ? 'Background' : 'Outfit';
  const kws = itemKeywords(kind, it).join(', ');
  const line = `[${label}]: ${kws}`;
  const ta = els.promptInput;
  if (ta) {
    ta.value = (ta.value.trim() ? ta.value.trim() + '\n' : '') + line;
    ta.dispatchEvent(new Event('input'));
  }
  switchTab('generate');
  document.getElementById('genSettings')?.setAttribute('open', '');
  ta?.focus();
  setStatus(`已加入 Prompt 草稿：${it.name}（可编辑后再生成）`);
  noteSelection(kind, it);          // CRE v2: 累积会话上下文 + 用量
  cpRunAsync(() => renderSmartRecommend(kind, it));   // 推荐后台渲染,不阻塞草稿写入
}

// 随机灵感：随机 模特+背景+服装 → 只填草稿，绝不自动生成
async function randomInspiration() {
  await loadAssetLibs();
  if (state.backgrounds.length) addToPromptDraft('bg', pickRandom(state.backgrounds));
  if (state.outfits.length) addToPromptDraft('outfit', pickRandom(state.outfits));
  if (state.models.length) {
    // 已锁定模特优先;没有才随机
    const m = state.activeModel || weightedRandomModel();
    if (m && (!state.activeModel || state.activeModel.id !== m.id)) await useModel(m.id);
  }
  setStatus('已生成随机灵感草稿（模特+背景+服装），可编辑后再生成');
}

document.getElementById('bgSearch')?.addEventListener('input', (e) => { state.assetSearch.bg = e.target.value; renderAssetList('bg'); });
document.getElementById('outfitSearch')?.addEventListener('input', (e) => { state.assetSearch.outfit = e.target.value; renderAssetList('outfit'); });
document.getElementById('bgRandomBtn')?.addEventListener('click', randomInspiration);
document.getElementById('outfitRandomBtn')?.addEventListener('click', randomInspiration);

/* ===== 跨库智能推荐引擎 CRE v2 —— 纯逻辑见 ./cre.js，此处仅为会话状态胶水 ===== */
function creMode() { return localStorage.getItem('apt_cre_mode') || 'v2'; }
const usageOf = (it) => state.assetUsage[it.id] || it.usage_count || 0;

// 会话上下文 + 用量计数(选中即累积)
function noteSelection(kind, it) {
  conceptsOf(kind, it).forEach((c) => state.context.concepts.add(c));
  state.assetUsage[it.id] = (state.assetUsage[it.id] || 0) + 1;
  try { localStorage.setItem('apt_asset_usage', JSON.stringify(state.assetUsage)); } catch { /* ignore */ }
}

function renderSmartRecommend(kind, item) {
  const panel = document.getElementById('smartRecommend');
  const body = document.getElementById('srBody');
  const hint = document.getElementById('srHint');
  if (!panel || !body || !item) return;
  if (!state.assetsLoaded) { loadAssetLibs().then(() => renderSmartRecommend(kind, item)); return; }
  state.lastRec = { kind, item };
  const t0 = performance.now();
  const rec = recommend({
    kind, item,
    models: state.models, backgrounds: state.backgrounds, outfits: state.outfits,
    activeModel: state.activeModel, contextConcepts: state.context.concepts,
    mode: creMode(), usageOf,
  });
  const ms = (performance.now() - t0).toFixed(1);
  if (hint) hint.textContent = `· ${creMode().toUpperCase()} · 基于「${item.name}」· ${ms}ms`;
  const groups = [];
  if (rec.models) groups.push(['model', '推荐模特', rec.models]);
  if (rec.backgrounds) groups.push(['bg', '推荐背景', rec.backgrounds]);
  if (rec.outfits) groups.push(['outfit', '推荐服装', rec.outfits]);
  body.innerHTML = groups.map(([k, title, arr]) => `
    <div class="sr-group">
      <div class="sr-group-title">${title}</div>
      <div class="sr-items">
        ${arr.length ? arr.map((r) => `
          <button class="sr-item" data-k="${k}" data-id="${escapeHtml(r.it.id)}">
            <div class="sr-item-name"><span class="sr-trend ${r.trend === '↑' ? 'up' : r.trend === '↗' ? 'mid' : ''}">${r.trend}</span>${escapeHtml(r.it.name)}<span class="sr-item-score">${r.score.toFixed(2)}</span></div>
            <div class="sr-item-reason">${escapeHtml(r.reason)}</div>
          </button>`).join('') : '<div class="sr-empty">暂无匹配（库为空或无重叠标签）</div>'}
      </div>
    </div>`).join('');
  body.querySelectorAll('.sr-item').forEach((el) => el.addEventListener('click', () => {
    const k = el.dataset.k;
    const id = el.dataset.id;
    if (k === 'model') useModel(id);
    else { const it = (k === 'bg' ? state.backgrounds : state.outfits).find((x) => x.id === id); if (it) addToPromptDraft(k, it); }
  }));
  panel.hidden = false;
  panel.open = true;
}

// CRE v1/v2 模式切换
document.getElementById('creModeToggle')?.addEventListener('click', (e) => {
  e.preventDefault();
  e.stopPropagation();
  const next = creMode() === 'v2' ? 'v1' : 'v2';
  localStorage.setItem('apt_cre_mode', next);
  e.target.textContent = next.toUpperCase();
  if (state.lastRec) renderSmartRecommend(state.lastRec.kind, state.lastRec.item);
});
/* ===== Prompt Copilot Agent v1 —— 纯逻辑见 ./copilot.js，此处仅 DOM/流式胶水 ===== */
function cpWriteDraft(text) {
  const ta = els.promptInput;
  if (ta) { ta.value = text; ta.dispatchEvent(new Event('input')); }
  switchTab('generate');
  document.getElementById('genSettings')?.setAttribute('open', '');
  document.getElementById('copilot')?.setAttribute('open', '');
  ta?.focus();
}
function cpOut(html) { const o = document.getElementById('copilotOut'); if (o) o.innerHTML = html; }

// 1. 自动补全：流式分阶段 + 乐观即时渲染（不阻塞 UI）
function cpRunAsync(fn) { (window.requestIdleCallback || ((cb) => setTimeout(cb, 0)))(fn); }
function cpNextFrame() { return new Promise((r) => (window.requestAnimationFrame || ((c) => setTimeout(c, 16)))(r)); }
function cpStreamInit() { const o = document.getElementById('copilotOut'); if (o) o.innerHTML = '<div class="cp-stream" id="cpStream"></div>'; }
function cpStreamPush(msg, done) {
  const s = document.getElementById('cpStream'); if (!s) return;
  const d = document.createElement('div');
  d.className = 'cp-stage' + (done ? ' done' : '');
  d.innerHTML = `<span class="cp-stage-dot"></span>${escapeHtml(msg)}`;
  s.appendChild(d);
}

async function cpAutoComplete() {
  const text = document.getElementById('copilotInput')?.value || '';
  // 阶段1：乐观即时反馈（同步，<200ms）
  document.getElementById('copilot')?.setAttribute('open', '');
  cpStreamInit();
  cpStreamPush('分析用户意图…');
  setStatus('Copilot 分析中…');
  await cpNextFrame();                 // 让骨架先绘制
  await loadAssetLibs();
  const tokens = cpTokens(text);
  const concepts = cpConcepts(tokens);
  // 阶段2：模特（网络用量为 fire-and-forget，不阻塞）
  const model = cpBestModel(state.models, tokens, concepts) || state.activeModel;
  if (model && (!state.activeModel || state.activeModel.id !== model.id)) useModel(model.id);
  cpStreamPush(model ? `模特：${model.name}（锁定身份/脸）` : '模特：未指定（可留空）', true);
  await cpNextFrame();
  // 阶段3：背景
  const bg = cpBestLib('bg', state.backgrounds, tokens, concepts);
  cpStreamPush(`背景：${bg ? bg.name : '按概念推断'}`, true);
  await cpNextFrame();
  // 阶段4：服装
  const outfit = cpBestLib('outfit', state.outfits, tokens, concepts);
  cpStreamPush(`服装：${outfit ? outfit.name : '按概念推断'}`, true);
  await cpNextFrame();
  // 阶段5：草稿就绪
  const f = composeDraft({ model, bg, outfit, concepts });
  cpWriteDraft(cpRenderDraft(f));
  cpStreamPush('结构化草稿已就绪 ✓ — 可直接编辑后生成', true);
  setStatus('Copilot 已补全结构化草稿（流式）');
}

// 2. 增强：只改 Lighting/Camera/Style，不动 Model/Background/Outfit（一致性保障）
function cpEnhance() {
  const ta = els.promptInput; if (!ta) return;
  const { fields, structured } = cpParseDraft(ta.value);
  if (structured) {
    fields['Lighting'] = (fields['Lighting'] ? fields['Lighting'] + ', ' : '') + 'volumetric soft light, balanced highlights';
    fields['Camera'] = (fields['Camera'] || CP_CAMERA[0]) + ', rule-of-thirds composition, shallow depth of field';
    fields['Style Keywords'] = (fields['Style Keywords'] || CP_STYLE_BASE) + ', fine fabric detail, realistic skin texture, sharp focus';
    cpWriteDraft(cpRenderDraft(fields));
  } else {
    ta.value = ta.value.trim() + '\n[Enhance]: volumetric soft light, rule-of-thirds composition, shallow depth of field, fine fabric detail, realistic skin texture';
    ta.dispatchEvent(new Event('input'));
  }
  cpOut('<div class="cp-note">已增强光影/构图/材质（场景·服装·模特保持不变）。</div>');
  setStatus('Copilot 已增强提示词');
}

// 3. 变体 A/B/C：保持 Model + Background + Outfit，仅变 Pose/Lighting/Camera
function cpVariations() {
  const ta = els.promptInput; if (!ta) return;
  let { fields, structured } = cpParseDraft(ta.value);
  if (!structured) {
    const c = state.context.concepts;
    fields = {
      'Model': state.activeModel ? `${state.activeModel.name}（锁定身份/脸）` : '(未选择)',
      'Background': cpInferBg(c), 'Outfit': cpInferOutfit(c),
      'Pose': CP_POSE[0], 'Lighting': CP_LIGHT[0], 'Camera': CP_CAMERA[0], 'Style Keywords': CP_STYLE_BASE,
    };
  }
  const variants = ['A', 'B', 'C'].map((label, i) => {
    const f = Object.assign({}, fields);
    f['Pose'] = CP_POSE[(i * 2 + 1) % CP_POSE.length];
    f['Lighting'] = CP_LIGHT[(i * 2 + 1) % CP_LIGHT.length];
    f['Camera'] = CP_CAMERA[(i * 2 + 1) % CP_CAMERA.length];
    return { label, text: cpRenderDraft(f) };
  });
  cpOut(variants.map((v, i) => `
    <div class="cp-variant">
      <div class="cp-variant-head">Variant ${v.label}<button class="cp-variant-apply" data-i="${i}">应用到草稿</button></div>
      <pre>${escapeHtml(v.text)}</pre>
    </div>`).join(''));
  document.getElementById('copilotOut').querySelectorAll('.cp-variant-apply').forEach((b) => b.addEventListener('click', () => cpWriteDraft(variants[Number(b.dataset.i)].text)));
  setStatus('Copilot 生成 3 个变体（模特/场景/服装保持一致）');
}

// 4. 随机：风格协调（随机服装 → CRE 取协调背景 → 加权模特）
async function cpRandom() {
  await loadAssetLibs();
  const outfit = state.outfits.length ? pickRandom(state.outfits) : null;
  let bg = null;
  if (outfit && state.backgrounds.length) {
    const m = topMatches('bg', state.backgrounds, conceptsOf('outfit', outfit), new Set(), state.context.concepts, creMode(), usageOf);
    bg = m.length ? m[0].it : pickRandom(state.backgrounds);
  } else if (state.backgrounds.length) { bg = pickRandom(state.backgrounds); }
  // 模特：已锁定的优先(尊重用户选择)；没有才加权随机
  const model = state.activeModel || (state.models.length ? weightedRandomModel() : null);
  if (model && (!state.activeModel || state.activeModel.id !== model.id)) useModel(model.id);
  const c = outfit ? conceptsOf('outfit', outfit) : new Set();
  const f = composeDraft({ model, bg, outfit, concepts: c, pose: pickRandom(CP_POSE), camera: pickRandom(CP_CAMERA) });
  cpWriteDraft(cpRenderDraft(f));
  cpOut('<div class="cp-note">已随机生成风格协调的草稿，可编辑后生成。</div>');
  setStatus('Copilot 随机草稿已生成');
}

document.getElementById('copilotComplete')?.addEventListener('click', cpAutoComplete);
document.getElementById('copilotEnhance')?.addEventListener('click', cpEnhance);
document.getElementById('copilotVariations')?.addEventListener('click', cpVariations);
document.getElementById('copilotRandom')?.addEventListener('click', cpRandom);

/* ===== 一键生成工作流（CRE v2 隐式自动补全；用户输入永远优先；草稿仍可编辑） ===== */
const SCENE_CONCEPTS = new Set(['hotel', 'bedroom', 'studio', 'city', 'street', 'neon', 'nature', 'indoor', 'luxury']);
const OUTFIT_CONCEPTS = new Set(['silk', 'streetwear', 'sexy', 'cute', 'elegant', 'sport', 'editorial', 'party', 'vintage']);

function defaultModel() {
  if (state.activeModel) return state.activeModel;
  if (!state.models.length) return null;
  return [...state.models].sort((a, b) => (b.usage_count || 0) - (a.usage_count || 0))[0];  // 最常用 = 默认
}
function crePick(kind, seed) {
  const pool = kind === 'bg' ? state.backgrounds : state.outfits;
  if (!pool.length) return null;
  const aff = state.activeModel ? conceptsOf('model', state.activeModel) : new Set();
  const ctx = state.context.concepts;
  const src = seed && seed.size ? seed : (aff.size ? aff : ctx);
  const top = topMatches(kind, pool, src, aff, ctx, creMode(), usageOf);
  if (top.length) return top[0].it;
  return pool.find((it) => conceptsOf(kind, it).has(kind === 'bg' ? 'studio' : 'editorial')) || pool[0];
}

// 主按钮：空着→全自动；部分→只补缺失；用户已写内容一律保留(优先)
async function smartGenerate() {
  setStatus('正在组织提示词草稿…');   // 乐观:即时反馈,不等库加载
  await loadAssetLibs();
  const ta = els.promptInput;
  const current = (ta?.value || '').trim();
  const tagText = state.selectedTags.map((t) => t.label).join(', ');
  const userText = [tagText, current].filter(Boolean).join(', ');
  if (!state.activeModel && state.models.length) { const dm = defaultModel(); if (dm) await useModel(dm.id); }  // 默认模特(可清除)
  const userConcepts = cpConcepts(cpTokens(userText));
  const seed = new Set(userConcepts);
  if (state.activeModel) conceptsOf('model', state.activeModel).forEach((c) => seed.add(c));

  if (!userText) {
    // 全空：CRE 全自动 → 结构化 7 段草稿
    const bg = crePick('bg', seed);
    const outfit = crePick('outfit', seed);
    const c = new Set(seed);
    if (bg) conceptsOf('bg', bg).forEach((x) => c.add(x));
    if (outfit) conceptsOf('outfit', outfit).forEach((x) => c.add(x));
    const f = composeDraft({ model: state.activeModel, bg, outfit, concepts: c });
    if (ta) { ta.value = cpRenderDraft(f); ta.dispatchEvent(new Event('input')); }
  } else {
    // 部分输入：保留用户文本，只补缺失的 背景/服装 + 标准 光线/镜头
    const lines = [];
    const hasScene = [...userConcepts].some((c) => SCENE_CONCEPTS.has(c));
    const hasOutfit = [...userConcepts].some((c) => OUTFIT_CONCEPTS.has(c));
    if (!hasScene) { const bg = crePick('bg', seed); if (bg) lines.push(`[Background]: ${bg.prompt_keywords.join(', ')}`); }
    if (!hasOutfit) { const o = crePick('outfit', seed); if (o) lines.push(`[Outfit]: ${o.fashion_keywords.join(', ')}`); }
    if (!/\[lighting\]/i.test(current)) lines.push(`[Lighting]: ${cpLightFor(seed, 0)}`);
    if (!/\[camera\]/i.test(current)) lines.push(`[Camera]: ${CP_CAMERA[0]}`);
    if (lines.length && ta) { ta.value = (current ? current + '\n' : '') + lines.join('\n'); ta.dispatchEvent(new Event('input')); }
  }
  document.getElementById('genSettings')?.setAttribute('open', '');  // 让草稿可见可编辑
  await generateFromTemplate(null);
}

// Surprise：协调随机草稿(已含模特/背景/服装) → 直接生成
async function surpriseGenerate() {
  await cpRandom();
  await generateFromTemplate(null);
}

/* ===== 结果变体缩略图 ===== */
function addVariation(url) {
  if (!url || url === '/placeholder.svg') return;
  state.variations.unshift(url);
  state.variations = state.variations.slice(0, 12);
  renderVariations();
}
function renderVariations() {
  const strip = document.getElementById('variationStrip');
  if (!strip) return;
  if (state.variations.length === 0) { strip.classList.add('hidden'); strip.innerHTML = ''; return; }
  strip.classList.remove('hidden');
  strip.innerHTML = state.variations.map((u, i) => `<img class="variation-thumb${u === state.currentImageUrl ? ' active' : ''}" src="${escapeHtml(u)}" data-url="${escapeHtml(u)}" alt="变体${i + 1}" loading="lazy" />`).join('');
  strip.querySelectorAll('.variation-thumb').forEach((t) => t.addEventListener('click', () => {
    state.currentImageUrl = t.dataset.url;
    showResultImage(t.dataset.url);
    renderVariations();
  }));
}

/* ===== 知识库抽屉（默认隐藏，点导航轨“提示词库”弹出） ===== */
const knowledgePanel = document.getElementById('sidebar');
const closeKnowledge = () => knowledgePanel?.classList.remove('open');
document.getElementById('railPromptLib')?.addEventListener('click', () => knowledgePanel?.classList.toggle('open'));
document.getElementById('knowledgeCloseBtn')?.addEventListener('click', closeKnowledge);
// 选中模板后自动收起抽屉，让生图主区完整
document.getElementById('templateList')?.addEventListener('click', (e) => {
  const card = e.target.closest('.template-card');
  if (card && !e.target.closest('.fav-btn') && !e.target.closest('.batch-check')) closeKnowledge();
});
// 导航轨“随机生图”复用设置面板的随机按钮
document.getElementById('railRandom')?.addEventListener('click', () => document.getElementById('randomGenBtn')?.click());

/* ===== 助手：快捷指令折叠 + 对话开始后问候语消失 ===== */
const quickWrap = document.getElementById('assistantQuickWrap');
const quickToggle = document.getElementById('quickToggle');
quickToggle?.addEventListener('click', () => {
  const collapsed = quickWrap?.classList.toggle('collapsed');
  quickToggle.setAttribute('aria-expanded', String(!collapsed));
});
const chatMessagesEl = document.getElementById('chatMessages');

/* 把比例/尺寸提示解析到尺寸下拉 */
function setSizeByHint(hint) {
  const sel = document.getElementById('sizeSelect');
  if (!sel || !hint) return;
  const norm = hint.replace('×', 'x').toLowerCase();
  let opt = [...sel.options].find((o) => o.value.toLowerCase() === norm);
  if (!opt) opt = [...sel.options].find((o) => o.textContent.includes(hint)); // 比例匹配,如 "3:4"
  if (opt) sel.value = opt.value;
}

/* 解析助手回复中的动作标记并执行 */
function applyAssistantActions(text) {
  const applied = [];
  let m = text.match(/【提示词[:：]?\s*([\s\S]+?)】/);
  if (m && els.promptInput) { els.promptInput.value = m[1].trim(); els.promptInput.dispatchEvent(new Event('input')); applied.push('提示词'); }
  m = text.match(/【背景[:：]?\s*([\s\S]+?)】/);
  const bg = document.getElementById('backgroundInput');
  if (m && bg) { bg.value = m[1].trim(); applied.push('背景'); }
  m = text.match(/【负面[:：]?\s*([\s\S]+?)】/);
  const neg = document.getElementById('negativeInput');
  if (m && neg) { neg.value = m[1].trim(); applied.push('负面词'); }
  m = text.match(/【模型[:：]?\s*(agnes|sensenova|mock)】/i);
  if (m && modelSelect) { modelSelect.value = m[1].toLowerCase(); renderSizeOptions(getSelectedProvider()); applied.push('模型'); }
  m = text.match(/【尺寸[:：]?\s*([0-9]+[x×][0-9]+|\d+:\d+)】/);
  if (m) { setSizeByHint(m[1]); applied.push('尺寸'); }
  const wantGen = /【生成】/.test(text);
  return { applied, wantGen };
}

if (chatMessagesEl) {
  let settleTimer = null;
  const obs = new MutationObserver(() => {
    // 对话开始:问候语消失 + 快捷指令折叠
    if (chatMessagesEl.querySelector('.chat-msg.user')) {
      document.getElementById('assistantGreeting')?.classList.add('gone');
      quickWrap?.classList.add('collapsed');
      quickToggle?.setAttribute('aria-expanded', 'false');
    }
    // 助手消息流式结束(停止变动 ~900ms)后解析动作标记
    clearTimeout(settleTimer);
    settleTimer = setTimeout(() => {
      if (!chatMessagesEl.querySelector('.chat-msg.user')) return; // 跳过初始问候
      const bubbles = chatMessagesEl.querySelectorAll('.chat-msg.assistant .msg-bubble');
      const last = bubbles[bubbles.length - 1];
      if (!last || last.dataset.actionsApplied) return;
      last.dataset.actionsApplied = '1';
      const { applied, wantGen } = applyAssistantActions(last.textContent || '');
      if (applied.length) setStatus('已按助手建议设置：' + applied.join('、'));
      if (wantGen && (getPrompt() || state.selectedId || state.refImage)) {
        generateFromTemplate(state.selectedId);
      }
    }, 900);
  });
  obs.observe(chatMessagesEl, { childList: true, subtree: true });
}

/* ===== 续改:把当前结果设为下一轮参考图(链式图生图) ===== */
async function urlToDataURL(url) {
  const resp = await fetch(url);
  const blob = await resp.blob();
  return await new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(r.result);
    r.onerror = reject;
    r.readAsDataURL(blob);
  });
}
document.getElementById('continueEditBtn')?.addEventListener('click', async () => {
  if (!state.currentImageUrl || state.currentImageUrl === '/placeholder.svg') {
    setStatus('还没有可继续修改的结果图', true);
    return;
  }
  try {
    state.refImage = await urlToDataURL(state.currentImageUrl);
    state.refImageName = '上一轮生成结果';
    renderRefImage();
    els.promptInput?.focus();
    setStatus('已将结果设为参考图，输入修改要求后点“生成图片”继续改');
  } catch {
    setStatus('无法读取结果图用于续改', true);
  }
});

// 一键：按助手最新建议改这张图(填提示词 + 图生图)
document.getElementById('applyToImageBtn')?.addEventListener('click', () => {
  if (!document.querySelector('#chatMessages .chat-msg.user')) {
    setStatus('先和助手聊出一个修改建议，再点这里', true);
    return;
  }
  const bubbles = document.querySelectorAll('#chatMessages .chat-msg.assistant .msg-bubble');
  const last = bubbles[bubbles.length - 1];
  const text = last ? last.textContent.trim() : '';
  if (!text) { setStatus('助手还没有给出建议', true); return; }
  // 优先提取【提示词：...】标记内容，否则用整段
  const m = text.match(/【提示词[:：]?\s*([\s\S]+?)】/);
  const promptText = (m ? m[1] : text).trim();
  if (els.promptInput) {
    els.promptInput.value = promptText;
    els.promptInput.dispatchEvent(new Event('input'));
  }
  if (!state.refImage) {
    setStatus('已填入提示词；请先上传要修改的图片再生成', true);
    els.uploadDropzone?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    return;
  }
  generateFromTemplate(state.selectedId);
});

// 助手收起/重开浮钮联动
const chatPanelEl = document.getElementById('chatPanel');
const assistantReopen = document.getElementById('assistantReopen');
function syncAssistantFab() {
  if (!assistantReopen || !chatPanelEl) return;
  const collapsed = chatPanelEl.classList.contains('hidden');
  assistantReopen.classList.toggle('hidden', !collapsed);
  document.getElementById('tab-generate')?.classList.toggle('assistant-collapsed', collapsed);
}
document.getElementById('chatCloseBtn')?.addEventListener('click', () => setTimeout(syncAssistantFab, 0));
assistantReopen?.addEventListener('click', () => {
  chatPanelEl?.classList.remove('hidden');
  syncAssistantFab();
});
syncAssistantFab();

async function runBatchGenerate() {
  const ids = Array.from(state.batchSelected);
  if (ids.length === 0) return;
  state.batchSelected.clear();
  renderTemplateList();

  state.queue = ids.map((id, i) => ({ id, index: i, status: 'pending', result: null, error: null }));
  state.queueRunning = true;
  renderQueuePanel();
  switchTab('generate');

  for (const item of state.queue) {
    item.status = 'running';
    renderQueuePanel();
    try {
      const result = await api('/generate', { method: 'POST', body: JSON.stringify({ template_id: item.id }) });
      item.status = result.status === 'failed' ? 'failed' : 'completed';
      item.result = result;
    } catch (err) {
      item.status = 'failed';
      item.error = err.message;
    }
    renderQueuePanel();
  }
  state.queueRunning = false;
  renderQueuePanel();
  loadGallery();
}

function renderQueuePanel() {
  let panel = document.getElementById('queuePanel');
  const total = state.queue.length;
  const done = state.queue.filter((q) => q.status !== 'pending' && q.status !== 'running').length;
  const completed = state.queue.filter((q) => q.status === 'completed').length;

  if (total === 0) { if (panel) panel.remove(); return; }

  if (!panel) {
    panel = document.createElement('div');
    panel.id = 'queuePanel';
    panel.className = 'queue-panel';
    els.imageStage?.appendChild(panel);
  }

  const percent = total > 0 ? Math.round((done / total) * 100) : 0;
  const templateMap = new Map(state.templates.map((t) => [t.template_id, t]));

  panel.innerHTML = `
    <div class="queue-header">
      <span class="queue-title">生成队列</span>
      <span class="queue-count">${completed}/${total} 完成</span>
    </div>
    <div class="queue-progress-wrap"><div class="queue-progress-bar" style="width:${percent}%"></div></div>
    <div class="queue-list">
      ${state.queue.map((item) => {
        const t = templateMap.get(item.id);
        const title = t ? t.title : item.id;
        const icon = item.status === 'completed' ? '✓' : item.status === 'failed' ? '✗' : item.status === 'running' ? '⏳' : '○';
        return `<div class="queue-item ${item.status}"><span class="queue-icon">${icon}</span><span>${escapeHtml(title)}</span></div>`;
      }).join('')}
    </div>
    ${!state.queueRunning && done >= total ? `<div class="queue-done">✓ 全部完成！<button class="btn-text" id="queueClose">关闭</button></div>` : ''}
  `;

  panel.querySelector('#queueClose')?.addEventListener('click', () => {
    state.queue = [];
    panel.remove();
  });
}

/* ===== 作品集 ===== */
els.refreshGalleryBtn?.addEventListener('click', loadGallery);

async function loadGallery() {
  if (!els.galleryGrid) return;
  try {
    const data = await api('/images/recent');
    const items = data.items || [];
    if (items.length === 0) {
      els.galleryGrid.innerHTML = '<div class="gallery-empty"><p>还没有生成任何图片</p></div>';
      return;
    }
    els.galleryGrid.innerHTML = items.map((item) => {
      const imgSrc = item.thumbnail_url || item.image_url || '';
      const title = item.title || '未命名';
      const date = item.created_at ? new Date(item.created_at).toLocaleString('zh-CN') : '';
      const taskId = escapeHtml(item.id || '');
      const sel = state.gallerySelect;
      const selected = sel.ids.has(String(item.id));
      return `
        <div class="gallery-card${sel.active ? ' selectable' : ''}${selected ? ' selected' : ''}" data-task-id="${taskId}">
          <div class="gallery-card-image">
            ${imgSrc
              ? `<img src="${escapeHtml(imgSrc)}" alt="${escapeHtml(title)}" loading="lazy" onerror="this.src='/placeholder.svg';this.classList.add('img-fallback');" />`
              : '<div class="gallery-card-placeholder"><span>无图片</span></div>'}
            <button class="gallery-delete-btn" data-delete-id="${taskId}" title="删除">🗑</button>
            <span class="gallery-check" aria-hidden="true">✓</span>
          </div>
          <div class="card-body">
            <div class="card-title">${escapeHtml(title)}</div>
            <div class="card-meta">${escapeHtml(date)}</div>
          </div>
        </div>
      `;
    }).join('');

    els.galleryGrid.querySelectorAll('.gallery-delete-btn').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const id = btn.dataset.deleteId;
        if (id && confirm('确定要删除这条记录吗？')) deleteImage(id);
      });
    });

    // 多选模式：点卡片切换选中；非多选：点图开灯箱
    els.galleryGrid.querySelectorAll('.gallery-card').forEach((card) => {
      card.addEventListener('click', () => {
        if (!state.gallerySelect.active) return;
        const id = card.dataset.taskId;
        if (state.gallerySelect.ids.has(id)) state.gallerySelect.ids.delete(id);
        else state.gallerySelect.ids.add(id);
        card.classList.toggle('selected');
        updateGalleryDeleteBtn();
      });
    });
    els.galleryGrid.querySelectorAll('.gallery-card-image img').forEach((img) => {
      img.addEventListener('click', (e) => {
        if (state.gallerySelect.active) return;
        e.stopPropagation();
        openLightbox(img.src, img.alt);
      });
    });
  } catch (err) {
    els.galleryGrid.innerHTML = `<div class="gallery-empty"><p>加载失败: ${escapeHtml(err.message)}</p></div>`;
  }
}

async function deleteImage(id) {
  try {
    const resp = await api(`/images/${encodeURIComponent(id)}`, { method: 'DELETE' });
    if (resp.deleted) loadGallery();
  } catch {}
}

/* ===== 精品库多选管理 ===== */
function updateGalleryDeleteBtn() {
  const b = document.getElementById('galleryDeleteSelBtn');
  if (b) b.textContent = `删除选中 (${state.gallerySelect.ids.size})`;
}
function setGalleryMode(active) {
  state.gallerySelect.active = active;
  state.gallerySelect.ids.clear();
  document.getElementById('gallerySelectBtn')?.toggleAttribute('hidden', active);
  document.getElementById('gallerySelectAllBtn')?.toggleAttribute('hidden', !active);
  document.getElementById('galleryDeleteSelBtn')?.toggleAttribute('hidden', !active);
  document.getElementById('galleryCancelSelBtn')?.toggleAttribute('hidden', !active);
  updateGalleryDeleteBtn();
  loadGallery();
}
document.getElementById('gallerySelectBtn')?.addEventListener('click', () => setGalleryMode(true));
document.getElementById('galleryCancelSelBtn')?.addEventListener('click', () => setGalleryMode(false));
document.getElementById('gallerySelectAllBtn')?.addEventListener('click', () => {
  const cards = [...els.galleryGrid.querySelectorAll('.gallery-card')];
  const allSelected = cards.length > 0 && state.gallerySelect.ids.size === cards.length;
  state.gallerySelect.ids.clear();
  if (!allSelected) cards.forEach((c) => state.gallerySelect.ids.add(c.dataset.taskId));
  cards.forEach((c) => c.classList.toggle('selected', state.gallerySelect.ids.has(c.dataset.taskId)));
  updateGalleryDeleteBtn();
});
document.getElementById('galleryDeleteSelBtn')?.addEventListener('click', async () => {
  const ids = [...state.gallerySelect.ids];
  if (!ids.length) { setStatus('未选择任何项', true); return; }
  if (!confirm(`确定删除选中的 ${ids.length} 项？此操作不可恢复。`)) return;
  try {
    const resp = await api('/images/bulk-delete', { method: 'POST', body: JSON.stringify({ ids: ids.map(Number) }) });
    setStatus(`已删除 ${resp.deleted ?? ids.length} 项`);
    setGalleryMode(false);
  } catch (e) {
    setStatus('批量删除失败：' + (e?.message || ''), true);
  }
});

/* ===== 搜索 ===== */
let searchDebounceTimer = null;
els.templateSearch?.addEventListener('input', () => {
  state.searchQuery = els.templateSearch.value.trim();
  els.clearSearchBtn?.classList.toggle('hidden', !state.searchQuery);
  if (state.searchQuery) { state.quickFilter = null; renderQuickFilters(); }
  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(async () => {
    await renderTemplateList();
    if (state.searchQuery) trackEvent('search', { query: state.searchQuery });
  }, 400);
});

els.clearSearchBtn?.addEventListener('click', async () => {
  if (els.templateSearch) els.templateSearch.value = '';
  state.searchQuery = '';
  state.quickFilter = null;
  renderQuickFilters();
  await renderTemplateList();
  els.clearSearchBtn?.classList.add('hidden');
});

/* ===== 上传 ===== */
const uploadState = { pendingFiles: [] };

els.selectFilesBtn?.addEventListener('click', () => els.fileInput?.click());
els.fileInput?.addEventListener('change', () => {
  if (els.fileInput.files.length > 0) handleUploadFiles(els.fileInput.files);
  els.fileInput.value = '';
});
els.uploadDropzone?.addEventListener('dragover', (e) => { e.preventDefault(); els.uploadDropzone.classList.add('dragover'); });
els.uploadDropzone?.addEventListener('dragleave', () => els.uploadDropzone.classList.remove('dragover'));
els.uploadDropzone?.addEventListener('drop', (e) => {
  e.preventDefault();
  els.uploadDropzone.classList.remove('dragover');
  if (e.dataTransfer.files.length > 0) handleUploadFiles(e.dataTransfer.files);
});

async function handleUploadFiles(files) {
  // 取第一张图作为图生图参考图，读成 Data URI 供 /generate 的 image 字段使用。
  const file = [...files].find((f) => f.type.startsWith('image/'));
  if (!file) return;
  if (file.size > 10 * 1024 * 1024) { setStatus('参考图需小于 10MB', true); return; }
  try {
    state.refImage = await fileToDataURL(file);
    state.refImageName = file.name;
    renderRefImage();
    setStatus('参考图已就绪，写好提示词后点“生成图片”即可在图上修改');
  } catch {
    setStatus('读取图片失败', true);
  }
}

function fileToDataURL(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(r.result);
    r.onerror = reject;
    r.readAsDataURL(file);
  });
}

function renderRefImage() {
  if (!els.uploadProgress) return;
  if (!state.refImage) {
    els.uploadProgress.classList.add('hidden');
    els.uploadProgress.innerHTML = '';
    return;
  }
  els.uploadProgress.classList.remove('hidden');
  els.uploadProgress.innerHTML = `
    <div class="ref-image">
      <img src="${state.refImage}" class="ref-thumb" alt="参考图" />
      <div class="ref-info">
        <b>参考图已就绪</b>
        <span>${escapeHtml(state.refImageName || '')}</span>
        <small>生成时将用 Agnes 图生图，在此图上按提示词修改</small>
      </div>
      <button class="ref-remove" id="refRemoveBtn" title="移除参考图">×</button>
    </div>`;
  els.uploadProgress.querySelector('#refRemoveBtn')?.addEventListener('click', () => {
    state.refImage = null;
    state.refImageName = '';
    renderRefImage();
  });
  els.uploadProgress.querySelector('.ref-thumb')?.addEventListener('click', () => openLightbox(state.refImage, '参考图'));
}

function renderUploadPreviewGrid() {
  if (!els.uploadProgress) return;
  els.uploadProgress.classList.remove('hidden');
  els.uploadProgress.innerHTML = '';
  if (uploadState.pendingFiles.length === 0) { els.uploadProgress.classList.add('hidden'); return; }

  const grid = document.createElement('div');
  grid.className = 'upload-preview-grid';

  for (const { file, id } of uploadState.pendingFiles) {
    const item = document.createElement('div');
    item.className = 'upload-preview-item';
    item.dataset.previewId = id;
    const objectUrl = URL.createObjectURL(file);
    item.innerHTML = `
      <div class="upload-preview-thumb-wrap">
        <img src="${objectUrl}" class="upload-preview-thumb" alt="${escapeHtml(file.name)}" data-preview-src="${objectUrl}" />
        <button class="upload-preview-remove" data-rm-id="${id}" title="移除">×</button>
      </div>
      <span class="upload-preview-name">${escapeHtml(file.name)}</span>
      <span class="upload-preview-size" data-res-id="${id}">${(file.size / 1024).toFixed(1)} KB</span>
    `;
    grid.appendChild(item);
  }

  els.uploadProgress.appendChild(grid);

  grid.querySelectorAll('.upload-preview-thumb').forEach((thumb) => {
    thumb.addEventListener('click', () => openLightbox(thumb.dataset.previewSrc, thumb.alt));
  });
  grid.querySelectorAll('.upload-preview-remove').forEach((btn) => {
    btn.addEventListener('click', () => {
      uploadState.pendingFiles = uploadState.pendingFiles.filter((f) => f.id !== btn.dataset.rmId);
      renderUploadPreviewGrid();
    });
  });

  const actionBar = document.createElement('div');
  actionBar.className = 'upload-action-bar';
  const clearBtn = document.createElement('button');
  clearBtn.className = 'btn-outline';
  clearBtn.textContent = '清空';
  clearBtn.addEventListener('click', () => { uploadState.pendingFiles = []; renderUploadPreviewGrid(); });
  const uploadBtn = document.createElement('button');
  uploadBtn.className = 'ctrl-generate-btn';
  uploadBtn.textContent = `上传 (${uploadState.pendingFiles.length})`;
  uploadBtn.addEventListener('click', doUploadFiles);
  actionBar.appendChild(clearBtn);
  actionBar.appendChild(uploadBtn);
  els.uploadProgress.appendChild(actionBar);
}

async function doUploadFiles() {
  const files = uploadState.pendingFiles.map((p) => p.file);
  if (files.length === 0) return;
  try {
    const cosData = await api('/cos/credentials');
    for (const file of files) {
      if (file.size > 10 * 1024 * 1024) continue;
      try {
        await uploadToCos(file, cosData.credentials, cosData.bucket || 'ai-fashion-ref-shanghai-1427746697', cosData.region || 'ap-shanghai');
      } catch {}
    }
  } catch {}
}

async function uploadToCos(file, stsCreds, bucket, region) {
  const { tmpSecretId, tmpSecretKey, sessionToken } = stsCreds;
  const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const key = `ref/upload/${today}/${Date.now()}_${encodeURIComponent(file.name)}`;
  const endpoint = `https://${bucket}.cos.${region}.myqcloud.com/${key}`;
  const auth = await buildCosAuth('PUT', endpoint, tmpSecretId, tmpSecretKey, sessionToken);
  const resp = await fetch(endpoint, {
    method: 'PUT',
    headers: { 'Authorization': auth, 'x-cos-security-token': sessionToken, 'Content-Type': file.type || 'application/octet-stream' },
    body: file,
  });
  if (!resp.ok) throw new Error(`COS upload failed: ${resp.status}`);
  return { key, url: `/cos/image/${key}` };
}

async function buildCosAuth(method, url, secretId, secretKey, token) {
  const encoder = new TextEncoder();
  const u = new URL(url);
  const keyTime = Math.floor(Date.now() / 1000) - 60;
  const signTime = keyTime + 1800;
  const httpString = `${method}\n${u.pathname}\n\nhost=${u.host}\n`;
  const signKey = await crypto.subtle.importKey('raw', encoder.encode(secretKey), { name: 'HMAC', hash: 'SHA-1' }, false, ['sign']);
  const signKeyBytes = await crypto.subtle.sign('HMAC', signKey, encoder.encode(keyTime + '.' + signTime));
  const stringToSign = `sha1\n${keyTime}.${signTime}\n${await sha1Hex(encoder.encode(httpString))}\n`;
  const signature = await crypto.subtle.sign('HMAC',
    await crypto.subtle.importKey('raw', signKeyBytes, { name: 'HMAC', hash: 'SHA-1' }, false, ['sign']),
    encoder.encode(stringToSign));
  const sigHex = Array.from(new Uint8Array(signature)).map(b => b.toString(16).padStart(2, '0')).join('');
  return `q-sign-algorithm=sha1&q-ak=${secretId}&q-sign-time=${keyTime}.${signTime}&q-key-time=${keyTime}.${signTime}&q-header-list=host&q-url-param-list=&q-signature=${sigHex}`;
}

async function sha1Hex(data) {
  const hash = await crypto.subtle.digest('SHA-1', data);
  return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, '0')).join('');
}

/* ===== 灯箱 ===== */
function openLightbox(src, alt) {
  if (!els.lightbox) return;
  els.lightboxImg.src = src;
  els.lightboxImg.alt = alt || '';
  els.lightbox.classList.remove('hidden');
}
function closeLightbox() {
  els.lightbox?.classList.add('hidden');
}
els.lightboxBackdrop?.addEventListener('click', closeLightbox);
els.lightboxClose?.addEventListener('click', closeLightbox);
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeLightbox(); });

/* ===== Demo 模式 ===== */
els.demoBtn?.addEventListener('click', () => {
  state.demoMode ? stopDemoMode() : startDemoMode();
});

function startDemoMode() {
  if (state.demoMode) return;
  state.demoMode = true;
  demoTemplateIndex = 0;
  demoStepIndex = 0;

  const watermark = document.createElement('div');
  watermark.className = 'demo-watermark';
  watermark.id = 'demoWatermark';
  watermark.innerHTML = '<span>🎬 Demo Mode</span><div class="demo-hint">按 ESC 退出</div>';
  document.body.appendChild(watermark);

  const progress = document.createElement('div');
  progress.className = 'demo-progress';
  progress.id = 'demoProgress';
  document.body.appendChild(progress);

  runDemoStep();
}

function stopDemoMode() {
  state.demoMode = false;
  clearTimeout(demoTimer);
  document.getElementById('demoWatermark')?.remove();
  document.getElementById('demoProgress')?.remove();
  document.querySelectorAll('.demo-highlight').forEach((el) => el.classList.remove('demo-highlight'));
}

function runDemoStep() {
  if (!state.demoMode) return;
  const demoIds = state.templates.length > 0 ? state.templates.map((t) => t.template_id) : DEMO_TEMPLATES;
  const templateId = demoIds[demoTemplateIndex % demoIds.length];
  const step = DEMO_STEPS[demoStepIndex % DEMO_STEPS.length];

  const progress = document.getElementById('demoProgress');
  if (progress) progress.style.width = `${(demoStepIndex / DEMO_STEPS.length) * 100}%`;

  document.querySelectorAll('.demo-highlight').forEach((el) => el.classList.remove('demo-highlight'));

  if (step.action === 'select') {
    selectTemplate(templateId);
    const card = els.templateList?.querySelector(`[data-id="${templateId}"]`);
    card?.classList.add('demo-highlight');
  } else if (step.action === 'generate') {
    generateFromTemplate(templateId);
  } else if (step.action === 'result') {
    demoTemplateIndex++;
  }

  demoStepIndex++;
  demoTimer = setTimeout(runDemoStep, step.delay);
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && state.demoMode) stopDemoMode();
});

/* ===== 初始化 ===== */
async function init() {
  try { state.assetUsage = JSON.parse(localStorage.getItem('apt_asset_usage') || '{}'); } catch { state.assetUsage = {}; }
  const cmt = document.getElementById('creModeToggle'); if (cmt) cmt.textContent = creMode().toUpperCase();
  await fetchModels();
  await migrateLocalModels();
  updateActiveModelBar();
  await loadProviders();
  renderSizeOptions(getSelectedProvider());
  renderLibrary();
  renderSelectedTags();
  await loadTemplates();
  state.quickFilter = 'recommended';
  renderQuickFilters();
  await renderTemplateList();
}

init().catch((err) => {
  setStatus('初始化失败', true);
});
