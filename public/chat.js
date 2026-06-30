/**
 * chat.js — AI 写真助手对话逻辑
 * 通过同源后端代理调用 Agnes OpenAI 兼容接口，流式输出
 */

const DEFAULT_SYSTEM_PROMPT = `你是一个专业的 AI 写真创作助手，服务于"AI 写真工坊 Studio"平台（DIY 提示词模式）。

核心原则：纯用户驱动创作。提示词只来自用户的场景/人物/服装/姿态/光线描述，绝不预设古风、历史美人、古典偶像等任何风格档案，也不自动套用默认审美。现代电影感写实、保持主体一致性。

你的能力：
1. 帮助用户描述想要的写真风格、场景、服装、光线等
2. 围绕用户给出的方向，纯按其意图细化（不主动替换或偏移成某种固定风格）
3. 优化和扩展用户的提示词，使其更适合 AI 生图
4. 解答关于写真风格、摄影美学的问题

回复规范：
- 语言简洁，不要过度解释
- 当你给出具体的提示词建议时，用【提示词】标记包裹，例如：【提示词：一位女性，城市天台夜景，霓虹光，电影感写实...】
- 中文回复为主
- 每次回复控制在200字以内

可执行动作标记（前端会自动解析并执行，请在合适时机使用）：
- 【提示词：...】填入生成提示词
- 【负面：...】填入负面提示词（不希望出现的内容，如：多余手指、模糊、变形、低质量）
- 【背景：...】设置画面背景（如：海边日落）
- 【模型：agnes】或【模型：sensenova】切换生图模型（修图/图生图用 agnes）
- 【尺寸：3:4】或【尺寸：1024x1365】设置尺寸（可用比例 1:1/3:4/4:3/9:16/16:9）
- 【生成】当信息齐全、用户希望直接出图时，附上此标记触发生成
当用户要"在上传的图上修改"时，给出【提示词：具体修改描述】并附【模型：agnes】【生成】。不要滥用【生成】，仅在用户明确想直接出图时使用。`

// 当前模板上下文（由 app.js 注入）
window.chatContext = {
  templateTitle: window.chatContext?.templateTitle || '',
  templateCategory: window.chatContext?.templateCategory || '',
  templateScene: window.chatContext?.templateScene || '',
};

const CHAT_SETTINGS_KEY = 'apt_chat_settings';
const CHAT_SETTINGS_BACKUP_KEY = 'apt_chat_settings_backup';
const CHAT_SETTINGS_VERSION = 2;
const DEFAULT_CHAT_SETTINGS = {
  version: CHAT_SETTINGS_VERSION,
  profile: 'creative',
  systemPrompt: DEFAULT_SYSTEM_PROMPT,
  injectTemplateContext: true,
  temperature: 0.55,
  maxTokens: 1200,
  stream: true,
  returnPromptMarker: true,
  shortReply: true,
};

function loadChatSettings() {
  try {
    const raw = localStorage.getItem(CHAT_SETTINGS_KEY);
    const saved = raw ? JSON.parse(raw) : {};
    if (!saved || typeof saved !== 'object' || Array.isArray(saved)) {
      return { ...DEFAULT_CHAT_SETTINGS };
    }
    return normalizeChatSettings(saved);
  } catch {
    return { ...DEFAULT_CHAT_SETTINGS };
  }
}

function normalizeChatSettings(saved) {
  const merged = { ...DEFAULT_CHAT_SETTINGS, ...saved, version: CHAT_SETTINGS_VERSION };
  if (!merged.systemPrompt || typeof merged.systemPrompt !== 'string') {
    merged.systemPrompt = DEFAULT_SYSTEM_PROMPT;
  }
  if (!['creative', 'prompt-engineer', 'strict'].includes(merged.profile)) {
    merged.profile = DEFAULT_CHAT_SETTINGS.profile;
  }
  merged.temperature = clampNumber(merged.temperature, 0, 1, DEFAULT_CHAT_SETTINGS.temperature);
  merged.maxTokens = clampNumber(merged.maxTokens, 256, 4096, DEFAULT_CHAT_SETTINGS.maxTokens);
  merged.injectTemplateContext = merged.injectTemplateContext !== false;
  merged.stream = merged.stream !== false;
  merged.returnPromptMarker = merged.returnPromptMarker !== false;
  merged.shortReply = merged.shortReply !== false;
  return merged;
}

function clampNumber(value, min, max, fallback) {
  const number = Number(value);
  if (!Number.isFinite(number)) return fallback;
  return Math.min(max, Math.max(min, number));
}

function backupChatSettings(reason = 'auto') {
  try {
    const raw = localStorage.getItem(CHAT_SETTINGS_KEY);
    if (!raw) return;
    localStorage.setItem(CHAT_SETTINGS_BACKUP_KEY, JSON.stringify({ reason, saved_at: new Date().toISOString(), value: JSON.parse(raw) }));
  } catch {
    // Backup is best-effort only.
  }
}

function saveChatSettings({ backup = false, reason = 'save' } = {}) {
  try {
    if (backup) backupChatSettings(reason);
    localStorage.setItem(CHAT_SETTINGS_KEY, JSON.stringify(chatSettings));
  } catch {
    // Settings remain usable for the current session when storage is unavailable.
  }
}

let chatSettings = loadChatSettings();

// 对话历史
const chatHistory = [];

/* ===== DOM ===== */
const chatPanel = document.getElementById('chatPanel');
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const chatSendBtn = document.getElementById('chatSendBtn');
const chatCloseBtn = document.getElementById('chatCloseBtn');
const chatToggleBtn = document.getElementById('chatToggleBtn');
const chatToggleBtn2 = document.getElementById('chatToggleBtn2');
const chatSettingsBtn = document.getElementById('chatSettingsBtn');
const chatSettingsPanel = document.getElementById('chatSettingsPanel');
const chatProfileSelect = document.getElementById('chatProfileSelect');
const chatSystemPromptInput = document.getElementById('chatSystemPromptInput');
const chatInjectTemplateContext = document.getElementById('chatInjectTemplateContext');
const chatTemperatureInput = document.getElementById('chatTemperatureInput');
const chatTemperatureValue = document.getElementById('chatTemperatureValue');
const chatMaxTokensInput = document.getElementById('chatMaxTokensInput');
const chatStreamInput = document.getElementById('chatStreamInput');
const chatReturnPromptMarker = document.getElementById('chatReturnPromptMarker');
const chatShortReply = document.getElementById('chatShortReply');
const chatSettingsResetBtn = document.getElementById('chatSettingsResetBtn');

/* ===== 开关面板 ===== */
function openChat() {
  chatPanel.classList.remove('hidden');
  document.body.classList.add('chat-open');
  chatToggleBtn?.classList.add('active');
  chatToggleBtn2?.classList.add('active');
  chatInput.focus();
}

function closeChat() {
  chatPanel.classList.add('hidden');
  document.body.classList.remove('chat-open');
  chatToggleBtn?.classList.remove('active');
  chatToggleBtn2?.classList.remove('active');
}

function toggleChatSettings(forceOpen) {
  const shouldOpen = forceOpen ?? !chatPanel.classList.contains('settings-open');
  chatPanel.classList.toggle('settings-open', shouldOpen);
  chatSettingsPanel?.classList.toggle('hidden', !shouldOpen);
  chatSettingsBtn?.classList.toggle('active', shouldOpen);
  if (shouldOpen) syncChatSettingsForm();
}

function syncChatSettingsForm() {
  if (chatProfileSelect) chatProfileSelect.value = chatSettings.profile;
  if (chatSystemPromptInput) chatSystemPromptInput.value = chatSettings.systemPrompt;
  if (chatInjectTemplateContext) chatInjectTemplateContext.checked = chatSettings.injectTemplateContext;
  if (chatTemperatureInput) chatTemperatureInput.value = String(chatSettings.temperature);
  if (chatTemperatureValue) chatTemperatureValue.textContent = Number(chatSettings.temperature).toFixed(2);
  if (chatMaxTokensInput) chatMaxTokensInput.value = String(chatSettings.maxTokens);
  if (chatStreamInput) chatStreamInput.checked = chatSettings.stream;
  if (chatReturnPromptMarker) chatReturnPromptMarker.checked = chatSettings.returnPromptMarker;
  if (chatShortReply) chatShortReply.checked = chatSettings.shortReply;
}

function updateChatSetting(key, value) {
  chatSettings = { ...chatSettings, [key]: value };
  saveChatSettings();
  syncChatSettingsForm();
}

chatToggleBtn?.addEventListener('click', () => {
  chatPanel.classList.contains('hidden') ? openChat() : closeChat();
});
chatToggleBtn2?.addEventListener('click', () => {
  chatPanel.classList.contains('hidden') ? openChat() : closeChat();
});
chatCloseBtn?.addEventListener('click', closeChat);
chatSettingsBtn?.addEventListener('click', () => toggleChatSettings());

document.querySelectorAll('.chat-settings-tab').forEach((tab) => {
  tab.addEventListener('click', () => {
    const name = tab.dataset.chatSettingsTab;
    document.querySelectorAll('.chat-settings-tab').forEach((item) => item.classList.toggle('active', item === tab));
    document.querySelectorAll('.chat-settings-page').forEach((page) => {
      page.classList.toggle('active', page.dataset.chatSettingsPage === name);
    });
  });
});

document.querySelectorAll('.chat-settings-collapse').forEach((button) => {
  button.addEventListener('click', () => {
    const body = document.getElementById(button.dataset.collapseTarget);
    const open = !body?.classList.contains('open');
    button.classList.toggle('open', open);
    body?.classList.toggle('open', open);
  });
});

chatProfileSelect?.addEventListener('change', () => updateChatSetting('profile', chatProfileSelect.value));
chatSystemPromptInput?.addEventListener('input', () => updateChatSetting('systemPrompt', chatSystemPromptInput.value));
chatInjectTemplateContext?.addEventListener('change', () => updateChatSetting('injectTemplateContext', chatInjectTemplateContext.checked));
chatTemperatureInput?.addEventListener('input', () => updateChatSetting('temperature', Number(chatTemperatureInput.value)));
chatMaxTokensInput?.addEventListener('input', () => updateChatSetting('maxTokens', Number(chatMaxTokensInput.value)));
chatStreamInput?.addEventListener('change', () => updateChatSetting('stream', chatStreamInput.checked));
chatReturnPromptMarker?.addEventListener('change', () => updateChatSetting('returnPromptMarker', chatReturnPromptMarker.checked));
chatShortReply?.addEventListener('change', () => updateChatSetting('shortReply', chatShortReply.checked));
chatSettingsResetBtn?.addEventListener('click', () => {
  chatSettings = { ...DEFAULT_CHAT_SETTINGS };
  saveChatSettings({ backup: true, reason: 'reset' });
  syncChatSettingsForm();
});

syncChatSettingsForm();

function buildConfiguredSystemPrompt() {
  let systemContent = (chatSettings.systemPrompt || DEFAULT_SYSTEM_PROMPT).trim();
  const profileRules = {
    creative: '当前配置档：Creative Brainstormer。优先提供有审美张力的写真创意和可执行提示词。',
    'prompt-engineer': '当前配置档：Photo Prompt Engineer。优先输出结构清晰、适合直接生图的提示词。',
    strict: '当前配置档：Concise Studio Assistant。回复克制、准确、少发散。',
  };
  systemContent += `\n\n${profileRules[chatSettings.profile] || profileRules.creative}`;
  if (chatSettings.returnPromptMarker) {
    systemContent += '\n当给出可应用的生图提示词时，必须使用【提示词：...】格式。';
  }
  if (chatSettings.shortReply) {
    systemContent += '\n每次回复控制在 200 字以内。';
  }
  if (chatSettings.injectTemplateContext && window.chatContext.templateTitle) {
    const title = window.chatContext.templateTitle || '';
    const category = window.chatContext.templateCategory || '';
    const scene = window.chatContext.templateScene || '';
    systemContent += `\n\n当前用户选择的模板：\n- 名称：${title}\n- 分类：${category}\n- 场景描述：${scene}`;
  }
  return systemContent;
}

/* ===== 发送消息 ===== */
async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text) return;

  chatInput.value = '';
  chatInput.style.height = 'auto';
  chatSendBtn.disabled = true;

  // 添加用户消息
  appendMessage('user', text);
  chatHistory.push({ role: 'user', content: text });

  // 构建系统消息（注入当前模型设置与模板上下文）
  let systemContent = buildConfiguredSystemPrompt();

  // 创建 AI 回复气泡（流式填充）
  const { bubble, cursor } = appendStreamingMessage();

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        stream: chatSettings.stream,
        temperature: chatSettings.temperature,
        max_tokens: chatSettings.maxTokens,
        messages: [
          { role: 'system', content: systemContent },
          ...chatHistory.slice(-10), // 保留最近10条历史
        ],
      }),
    });

    if (!response.ok) {
      throw new Error(`API 错误: ${response.status}`);
    }

    let fullText = '';

    if (!chatSettings.stream) {
      const data = await response.json();
      fullText = data.choices?.[0]?.message?.content || data.content || '';
      cursor.remove();
      bubble.innerHTML = renderMessageContent(fullText || '已完成，但没有返回内容。');
      bindApplyPromptButtons(bubble);
      chatHistory.push({ role: 'assistant', content: fullText });
      chatSendBtn.disabled = false;
      scrollToBottom();
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let streamBuffer = '';
    let streamDone = false;

    while (!streamDone) {
      const { done, value } = await reader.read();
      streamBuffer += done ? decoder.decode() : decoder.decode(value, { stream: true });
      const lines = streamBuffer.split(/\r?\n/);
      streamBuffer = done ? '' : lines.pop() || '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const data = line.slice(6).trim();
        if (data === '[DONE]') {
          streamDone = true;
          break;
        }

        try {
          const json = JSON.parse(data);
          const delta = json.choices?.[0]?.delta?.content || '';
          if (delta) {
            fullText += delta;
            // 渲染文本（处理提示词标记）
            bubble.innerHTML = renderMessageContent(fullText);
            bubble.appendChild(cursor);
            scrollToBottom();
          }
        } catch {
          // Ignore malformed SSE events while preserving chunk boundaries above.
        }
      }

      if (done) break;
    }

    // 流式结束，移除光标，渲染最终内容
    cursor.remove();
    bubble.innerHTML = renderMessageContent(fullText);

    bindApplyPromptButtons(bubble);

    chatHistory.push({ role: 'assistant', content: fullText });

  } catch (err) {
    cursor.remove();
    bubble.innerHTML = `<span style="color:#f87171">连接失败：${err.message}</span>`;
  }

  chatSendBtn.disabled = false;
  scrollToBottom();
}

/* ===== 渲染消息内容（处理【提示词:...】标记） ===== */
function renderMessageContent(text) {
  // 转义 HTML
  let escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>');

  // 处理【提示词：...】或【提示词:...】标记
  escaped = escaped.replace(
    /【提示词[：:]([^】]+)】/g,
    (_, prompt) => {
      const safePrompt = prompt.trim().replace(/"/g, '&quot;');
      return `<span style="color:#a78bfa;font-style:italic">「${prompt.trim()}」</span>
        <br><button class="apply-prompt-btn" data-prompt="${safePrompt}">✨ 应用到提示词</button>`;
    }
  );

  return escaped;
}

function bindApplyPromptButtons(root) {
  root.querySelectorAll('.apply-prompt-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const promptText = btn.dataset.prompt;
      applyPromptToInput(promptText);
      btn.textContent = '已应用';
      btn.disabled = true;
      setTimeout(() => {
        btn.textContent = '应用到提示词';
        btn.disabled = false;
      }, 2000);
    });
  });
}

/* ===== 将提示词应用到输入框 ===== */
function applyPromptToInput(promptText) {
  // 优先填入展开状态的 textarea
  const expandedInput = document.getElementById('promptInput');
  const inlineInput = document.getElementById('promptInline');

  const controlExpanded = document.getElementById('controlExpanded');
  const isExpanded = !controlExpanded.classList.contains('hidden');

  if (isExpanded && expandedInput) {
    expandedInput.value = promptText;
    expandedInput.focus();
  } else if (inlineInput) {
    inlineInput.value = promptText;
    inlineInput.focus();
  }
}

/* ===== 追加用户消息 ===== */
function appendMessage(role, text) {
  const div = document.createElement('div');
  div.className = `chat-msg ${role}`;
  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.innerHTML = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>');
  div.appendChild(bubble);
  chatMessages.appendChild(div);
  scrollToBottom();
}

/* ===== 追加流式 AI 消息（返回 bubble 和 cursor 引用） ===== */
function appendStreamingMessage() {
  const div = document.createElement('div');
  div.className = 'chat-msg assistant';
  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  const cursor = document.createElement('span');
  cursor.className = 'typing-cursor';
  bubble.appendChild(cursor);
  div.appendChild(bubble);
  chatMessages.appendChild(div);
  scrollToBottom();
  return { bubble, cursor };
}

function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

/* ===== 输入框自动高度 ===== */
chatInput?.addEventListener('input', () => {
  chatInput.style.height = 'auto';
  chatInput.style.height = Math.min(chatInput.scrollHeight, 100) + 'px';
});

/* ===== 回车发送（Shift+Enter 换行） ===== */
chatInput?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

chatSendBtn?.addEventListener('click', sendMessage);
