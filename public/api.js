/* ===== API Client ===== */
const API_BASE = window.API_BASE || '';

export async function apiGet(path, params = {}) {
  const search = new URLSearchParams(params).toString();
  return api(`${path}${search ? '?' + search : ''}`);
}

export async function api(path, options = {}) {
  const isForm = options.body instanceof URLSearchParams;
  const resp = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(isForm ? {} : { 'Content-Type': 'application/json' }),
      ...options.headers,
    },
  });
  const text = await resp.text();
  let data;
  try { data = JSON.parse(text); } catch { data = { error: text.slice(0, 300) }; }
  if (!resp.ok) {
    console.warn(`[API Error] ${path}: ${data.detail || data.error || resp.status}`);
    throw new Error(data.detail || data.error || `Request failed: ${resp.status}`);
  }
  return data;
}

export function trackEvent(eventType, payload = {}) {
  try {
    const body = new URLSearchParams();
    body.append('event_type', eventType);
    if (payload.template_id) body.append('template_id', payload.template_id);
    if (payload.query) body.append('query', payload.query);
    if (payload.category) body.append('category', payload.category);
    const sid = localStorage.getItem('apt_session_id') || (() => { const id = Math.random().toString(36).slice(2); localStorage.setItem('apt_session_id', id); return id; })();
    body.append('session_id', sid);
    api('/analytics/event', { method: 'POST', body }).catch(() => {});
  } catch {}
}

export async function postEvent(event) {
  const body = new URLSearchParams();
  body.append('event_type', event.eventType);
  if (event.templateId) body.append('template_id', event.templateId);
  if (event.query) body.append('query', event.query);
  if (event.category) body.append('category', event.category);
  if (event.sessionId) body.append('session_id', event.sessionId);
  return api('/analytics/event', { method: 'POST', body });
}

export async function searchTemplates(filters = {}) {
  const params = new URLSearchParams();
  if (filters.q) params.append('q', filters.q);
  if (filters.category) params.append('category', filters.category);
  if (filters.isFree != null) params.append('is_free', String(filters.isFree));
  if (filters.page) params.append('page', String(filters.page));
  if (filters.limit) params.append('limit', String(filters.limit));
  if (filters.sort) params.append('sort', filters.sort);
  return apiGet('/templates/search', params);
}

export async function getRecommendedTemplates(limit = 12) {
  return apiGet('/templates/recommended', { limit });
}

export async function getRecentlyUsedTemplates(limit = 12) {
  return apiGet('/templates/recently-used', { limit });
}

export async function getRecentTemplates(limit = 12) {
  return getRecentlyUsedTemplates(limit);
}

export const apiClient = {
  templates: {
    list: () => api('/api/templates'),
    get: (id) => api(`/api/templates/${encodeURIComponent(id)}`),
    search: searchTemplates,
    recommended: getRecommendedTemplates,
    recentlyUsed: getRecentlyUsedTemplates,
  },
  images: {
    recent: (limit = 20) => apiGet('/images/recent', { limit }),
    get: (id) => api(`/images/${encodeURIComponent(id)}`),
    delete: (id) => api(`/images/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  },
  generate: (body) => api('/generate', { method: 'POST', body: JSON.stringify(body) }),
  analytics: {
    track: (body) => api('/analytics/event', { method: 'POST', body }),
    popular: () => api('/analytics/popular'),
  },
  cos: {
    credentials: () => api('/cos/credentials'),
  },
};
