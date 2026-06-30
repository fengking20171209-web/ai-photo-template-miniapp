/**
 * GBrain 客户端 — TypeScript 实现
 *
 * 对比结论: TypeScript 作为 GBrain 客户端的首选方案
 * - 项目 CLI/API 层已全面 TypeScript，集成无缝
 * - 原生 fetch + AbortController 提供与 Python requests 同等能力
 * - 编译时类型安全，接口契约由 TypeScript 保证
 * - 遵循 gbrainFirst / recordEverything / syncAfterWrite 集成规则
 *
 * GBrain API 规范 (Flask v1.0.0, 端口 8081):
 * - GET  /api/v1/health       — 健康检查
 * - GET  /api/v1/stats        — 统计信息
 * - GET  /api/v1/search?q=    — 全文搜索
 * - GET  /api/v1/get/<path:slug> — 获取页面内容
 * - POST /api/v1/put          — 写入/更新页面
 * - POST /api/v1/timeline/<path:slug> — 添加时间线
 * - POST /api/v1/sync         — 触发索引同步
 */

export interface GBrainClientConfig {
  baseUrl: string;
  timeoutMs: number;
}

export interface GBrainPage {
  slug: string;
  category: string;
  content: string;
  created_at?: string;
  updated_at?: string;
}

export interface GBrainSearchResult {
  total: number;
  items: GBrainPage[];
}

export interface GBrainStats {
  total_pages: number;
  categories: Record<string, number>;
}

export interface GBrainHealth {
  ok: boolean;
  version?: string;
}

export interface GBrainError extends Error {
  status?: number;
  response?: unknown;
}

function createGBrainError(message: string, status?: number, response?: unknown): GBrainError {
  const error = new Error(message) as GBrainError;
  error.status = status;
  error.response = response;
  return error;
}

export class GBrainClient {
  private readonly baseUrl: string;
  private readonly timeoutMs: number;

  constructor(config: GBrainClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, "");
    this.timeoutMs = config.timeoutMs;
  }

  /** 健康检查 */
  async health(): Promise<GBrainHealth> {
    const response = await this._get("/api/v1/health");
    return response as GBrainHealth;
  }

  /** 统计信息 */
  async stats(): Promise<GBrainStats> {
    const response = await this._get("/api/v1/stats");
    return response as GBrainStats;
  }

  /** 全文搜索 */
  async search(query: string): Promise<GBrainSearchResult> {
    const response = await this._get(`/api/v1/search?q=${encodeURIComponent(query)}`);
    return response as GBrainSearchResult;
  }

  /** 获取页面内容 */
  async getPage(slug: string): Promise<GBrainPage> {
    const response = await this._get(`/api/v1/get/${encodeURIComponent(slug)}`);
    return response as GBrainPage;
  }

  /** 写入/更新页面 */
  async putPage(slug: string, content: string): Promise<void> {
    await this._post("/api/v1/put", { slug, content });
  }

  /** 添加时间线条目 */
  async addTimeline(slug: string, summary: string): Promise<void> {
    await this._post(`/api/v1/timeline/${encodeURIComponent(slug)}`, { summary });
  }

  /** 触发索引同步 */
  async sync(): Promise<void> {
    await this._post("/api/v1/sync", {});
  }

  /** 内部 GET 请求 */
  private async _get(path: string): Promise<unknown> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method: "GET",
        signal: controller.signal
      });

      if (!response.ok) {
        const text = await this._readResponseBody(response);
        throw createGBrainError(
          `GBrain GET ${path} failed: ${response.status} ${response.statusText}`,
          response.status,
          text
        );
      }

      return await this._readJsonResponse(response);
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        throw createGBrainError(
          `GBrain request to ${path} timed out after ${this.timeoutMs}ms`,
          undefined
        );
      }
      throw error;
    } finally {
      clearTimeout(timeout);
    }
  }

  /** 内部 POST 请求 */
  private async _post(path: string, body: Record<string, unknown>): Promise<unknown> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.signal
      });

      if (!response.ok) {
        const text = await this._readResponseBody(response);
        throw createGBrainError(
          `GBrain POST ${path} failed: ${response.status} ${response.statusText}`,
          response.status,
          text
        );
      }

      return await this._readJsonResponse(response);
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        throw createGBrainError(
          `GBrain request to ${path} timed out after ${this.timeoutMs}ms`,
          undefined
        );
      }
      throw error;
    } finally {
      clearTimeout(timeout);
    }
  }

  private async _readJsonResponse(response: Response): Promise<unknown> {
    const text = await this._readResponseBody(response);
    if (!text) return {};
    try {
      return JSON.parse(text);
    } catch {
      return { text };
    }
  }

  private async _readResponseBody(response: Response): Promise<string> {
    let timeout: ReturnType<typeof setTimeout> | undefined;
    try {
      return await Promise.race([
        response.text ? response.text() : Promise.resolve(JSON.stringify((response as any).json ? await (response as any).json() : {})),
        new Promise<string>((_resolve, reject) => {
          timeout = setTimeout(
            () => reject(new Error(`GBrain response body timed out after ${this.timeoutMs}ms`)),
            this.timeoutMs
          );
        })
      ]);
    } finally {
      if (timeout) clearTimeout(timeout);
    }
  }
}

/**
 * 创建默认 GBrain 客户端（从环境变量读取配置）
 * 遵循 gbrainFirst 规则：任务开始前先查询 GBrain
 */
export function createGBrainClient(): GBrainClient {
  const baseUrl = process.env.GBRAIN_API_URL || "http://100.92.38.117:8081";
  const timeoutMs = parseInt(process.env.GBRAIN_TIMEOUT_MS || "30000", 10);
  return new GBrainClient({ baseUrl, timeoutMs });
}
