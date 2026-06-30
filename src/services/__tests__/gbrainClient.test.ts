/**
 * GBrain 客户端集成测试
 *
 * 使用 mock GBrain API 响应验证客户端功能
 * 覆盖：health, stats, search, get, put, timeline, sync
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { GBrainClient, type GBrainClientConfig } from "../gbrainClient.js";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch as unknown as typeof fetch;

describe("GBrainClient", () => {
  let client: GBrainClient;
  const config: GBrainClientConfig = {
    baseUrl: "http://100.92.38.117:8081",
    timeoutMs: 30000
  };

  beforeEach(() => {
    mockFetch.mockReset();
    client = new GBrainClient(config);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe("health", () => {
    it("应返回健康检查响应", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ ok: true, version: "1.0.0" })
      });

      const result = await client.health();
      expect(result.ok).toBe(true);
      expect(result.version).toBe("1.0.0");
      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(mockFetch).toHaveBeenCalledWith(
        "http://100.92.38.117:8081/api/v1/health",
        expect.objectContaining({ method: "GET" })
      );
    });

    it("应处理健康检查失败", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 503,
        statusText: "Service Unavailable",
        text: async () => "Service Unavailable"
      });

      await expect(client.health()).rejects.toThrow("GBrain GET /api/v1/health failed: 503");
    });
  });

  describe("stats", () => {
    it("应返回统计信息", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({
          total_pages: 150,
          categories: { template: 50, prompt: 80, task: 20 }
        })
      });

      const result = await client.stats();
      expect(result.total_pages).toBe(150);
      expect(result.categories.template).toBe(50);
    });
  });

  describe("search", () => {
    it("应搜索模板并返回结果", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          total: 3,
          items: [
            { slug: "template_ancient_diaochan", category: "template", content: "古装貂蝉模板" },
            { slug: "prompt_diaochan_v1", category: "prompt", content: "prompt: 古装女子，貂蝉风格" },
            { slug: "task_ancient_diaochan_20260601", category: "task", content: "历史任务记录" }
          ]
        })
      });

      const result = await client.search("template:ancient_diaochan");
      expect(result.total).toBe(3);
      expect(result.items).toHaveLength(3);
      expect(result.items[0].slug).toBe("template_ancient_diaochan");
      expect(mockFetch).toHaveBeenCalledWith(
        "http://100.92.38.117:8081/api/v1/search?q=template%3Aancient_diaochan",
        expect.any(Object)
      );
    });

    it("应处理搜索无结果", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ total: 0, items: [] })
      });

      const result = await client.search("nonexistent_template");
      expect(result.total).toBe(0);
      expect(result.items).toHaveLength(0);
    });
  });

  describe("getPage", () => {
    it("应获取页面内容", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          slug: "template_ancient_diaochan",
          category: "template",
          content: "古装貂蝉模板内容",
          created_at: "2026-06-01T00:00:00Z"
        })
      });

      const result = await client.getPage("template_ancient_diaochan");
      expect(result.slug).toBe("template_ancient_diaochan");
      expect(result.category).toBe("template");
    });
  });

  describe("putPage", () => {
    it("应写入页面内容", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => ({ success: true })
      });

      await expect(client.putPage("test_page", "test content")).resolves.not.toThrow();
      expect(mockFetch).toHaveBeenCalledWith(
        "http://100.92.38.117:8081/api/v1/put",
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ slug: "test_page", content: "test content" })
        })
      );
    });
  });

  describe("addTimeline", () => {
    it("应添加时间线条目", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => ({ success: true })
      });

      await expect(client.addTimeline("task/test_task", "prompt_generated")).resolves.not.toThrow();
      expect(mockFetch).toHaveBeenCalledWith(
        "http://100.92.38.117:8081/api/v1/timeline/task%2Ftest_task",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ summary: "prompt_generated" })
        })
      );
    });
  });

  describe("sync", () => {
    it("应触发索引同步", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ synced: true })
      });

      await expect(client.sync()).resolves.not.toThrow();
      expect(mockFetch).toHaveBeenCalledWith(
        "http://100.92.38.117:8081/api/v1/sync",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({})
        })
      );
    });
  });

  describe("timeout", () => {
    it("应在超时后抛出错误", async () => {
      const shortClient = new GBrainClient({ baseUrl: config.baseUrl, timeoutMs: 100 });

      // 模拟长时间响应
      mockFetch.mockImplementation(
        (url, options) => new Promise((resolve, reject) => {
          const timer = setTimeout(() => resolve({ ok: true }), 200);
          if (options?.signal) {
            options.signal.addEventListener('abort', () => {
              clearTimeout(timer);
              const err = new Error("The operation was aborted");
              err.name = "AbortError";
              reject(err);
            });
          }
        })
      );

      await expect(shortClient.health()).rejects.toThrow("timed out after 100ms");
    });
  });

  describe("error handling", () => {
    it("应处理网络错误", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      await expect(client.health()).rejects.toThrow("Network error");
    });

    it("应处理非 JSON 响应", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => "not json"
      });

      const result = await client.health();
      expect(result).toEqual({ text: "not json" });
    });
  });
});