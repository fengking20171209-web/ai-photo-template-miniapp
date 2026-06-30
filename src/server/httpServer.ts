import fs from "node:fs";
import http, { type IncomingMessage, type ServerResponse } from "node:http";
import path from "node:path";
import type { AppConfig } from "../config/appConfig.js";
import { TemplateRepository } from "../templates/templateRepository.js";
import { listTemplatesWorkflow } from "../workflows/listTemplatesWorkflow.js";
import { runImageTaskWorkflow } from "../workflows/runImageTaskWorkflow.js";
import { loadTask, saveTask } from "./taskStore.js";

const MAX_JSON_BODY_BYTES = 1_048_576;
const GENERATE_LIMIT_WINDOW_MS = 60_000;
const GENERATE_LIMIT_MAX_REQUESTS = 10;
const generateRateLimits = new Map<string, number[]>();

class HttpError extends Error {
  constructor(
    readonly statusCode: number,
    message: string
  ) {
    super(message);
  }
}

export function createApiServer(config: AppConfig): http.Server {
  return http.createServer((request, response) => {
    handleRequest(config, request, response).catch((error) => {
      const statusCode = error instanceof HttpError ? error.statusCode : 500;
      sendError(response, statusCode, error instanceof Error ? error.message : String(error));
    });
  });
}

async function handleRequest(config: AppConfig, request: IncomingMessage, response: ServerResponse): Promise<void> {
  const url = new URL(request.url || "/", "http://localhost");
  const method = request.method === "HEAD" ? "GET" : request.method;

  if (request.method === "OPTIONS") {
    sendEmpty(response, 204);
    return;
  }

  if (method === "GET" && url.pathname === "/") {
    sendPublicFile(config, response, "index.html");
    return;
  }

  if (method === "GET" && isPublicAssetPath(url.pathname)) {
    sendPublicFile(config, response, decodeURIComponent(url.pathname.slice(1)));
    return;
  }

  if (method === "GET" && url.pathname === "/health") {
    sendJson(response, 200, {
      ok: true,
      provider: config.aiImageDryRun ? "mock" : config.aiImageProvider,
      dry_run: config.aiImageDryRun
    });
    return;
  }

  if (method === "GET" && url.pathname === "/templates") {
    const templates = await listTemplatesWorkflow(config);
    sendJson(response, 200, { items: templates });
    return;
  }

  const reservedTemplateSubRoutes = ["search", "recommended", "recent", "recently-used"];
  const templateMatch = url.pathname.match(/^\/templates\/([^/]+)$/);
  if (method === "GET" && templateMatch) {
    const templateId = decodeURIComponent(templateMatch[1]);
    if (!reservedTemplateSubRoutes.includes(templateId)) {
      const repository = new TemplateRepository(config.templatesDir);
      sendJson(response, 200, repository.load(templateId));
      return;
    }
  }

  // Note: POST /generate is proxied to FastAPI backend below

  const promptMatch = url.pathname.match(/^\/tasks\/([^/]+)\/prompt$/);
  if (method === "GET" && promptMatch) {
    const task = loadTask(config, decodeURIComponent(promptMatch[1]));
    const prompt = fs.readFileSync(task.prompt_file, "utf-8");
    sendJson(response, 200, { task_id: task.task_id, prompt });
    return;
  }

  const taskMatch = url.pathname.match(/^\/tasks\/([^/]+)$/);
  if (method === "GET" && taskMatch) {
    sendJson(response, 200, loadTask(config, decodeURIComponent(taskMatch[1])));
    return;
  }
  if (method === "DELETE" && taskMatch) {
    const taskId = decodeURIComponent(taskMatch[1]);
    const taskDir = path.join(config.outputDir, "tasks");
    const taskFile = path.join(taskDir, `${taskId}.json`);
    const taskFolder = path.join(taskDir, taskId);

    let deleted = false;
    if (fs.existsSync(taskFile)) {
      fs.unlinkSync(taskFile);
      deleted = true;
    }
    if (fs.existsSync(taskFolder)) {
      fs.rmSync(taskFolder, { recursive: true, force: true });
      deleted = true;
    }

    if (!deleted) {
      sendError(response, 404, `Task not found: ${taskId}`);
      return;
    }
    sendJson(response, 200, { id: taskId, deleted: true });
    return;
  }

  // Proxy specific routes to FastAPI backend
  const fastapiProxyMap: Record<string, { path: string; methods: string[] }> = {
    "/api/templates": { path: "/api/templates", methods: ["GET"] },
    "/templates/search": { path: "/api/templates/search", methods: ["GET"] },
    "/templates/recommended": { path: "/api/templates/recommended", methods: ["GET"] },
    "/templates/recent": { path: "/api/templates/recent", methods: ["GET"] },
    "/templates/recently-used": { path: "/api/templates/recently-used", methods: ["GET"] },
    "/analytics/event": { path: "/api/analytics/event", methods: ["POST"] },
    "/analytics/popular": { path: "/api/analytics/popular", methods: ["GET"] },
    "/cos/credentials": { path: "/cos/credentials", methods: ["GET"] },
    "/images/recent": { path: "/images/recent", methods: ["GET"] },
    "/generate": { path: "/generate", methods: ["POST"] },
    "/generate/providers": { path: "/generate/providers", methods: ["GET"] },
  };

  // Proxy /api/templates/{id} to FastAPI
  const apiTemplateMatch = url.pathname.match(/^\/api\/templates\/([^/]+)$/);
  if (method === "GET" && apiTemplateMatch) {
    const templateId = encodeURIComponent(decodeURIComponent(apiTemplateMatch[1]));
    await proxyToFastAPI(request, response, method, `/api/templates/${templateId}`, url.search || "");
    return;
  }

  // Proxy /images/{id} to FastAPI (GET + DELETE)
  const imagesIdMatch = url.pathname.match(/^\/images\/(\d+)$/);
  if (imagesIdMatch && ["GET", "DELETE"].includes(method)) {
    const imageId = imagesIdMatch[1];
    await proxyToFastAPI(request, response, method, `/images/${imageId}`, url.search || "");
    return;
  }

  const proxyConfig = fastapiProxyMap[url.pathname];
  if (proxyConfig && method && proxyConfig.methods.includes(method)) {
    await proxyToFastAPI(request, response, method, proxyConfig.path, url.search || "");
    return;
  }

  sendError(response, 404, `Route not found: ${request.method || "GET"} ${url.pathname}`);
}

async function proxyToFastAPI(
  request: IncomingMessage,
  response: ServerResponse,
  method: string,
  targetPath: string,
  search: string
): Promise<void> {
  try {
    const fastapiPort = process.env.FASTAPI_PORT || "8000";
    const fastapiUrl = `http://127.0.0.1:${fastapiPort}${targetPath}${search}`;
    console.log(`[PROXY] ${method} ${request.url} -> ${fastapiUrl}`);
    const proxyHeaders: Record<string, string> = {
      "content-type": request.headers["content-type"] ?? "application/json",
    };
    if (request.headers["authorization"]) {
      proxyHeaders["authorization"] = request.headers["authorization"];
    }

    let body: Uint8Array | undefined;
    if (method !== "GET" && method !== "HEAD") {
      const chunks: Buffer[] = [];
      for await (const chunk of request) {
        chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
      }
      const buf = Buffer.concat(chunks);
      body = new Uint8Array(buf.buffer, buf.byteOffset, buf.byteLength);
    }

    const proxyResp = await fetch(fastapiUrl, {
      method,
      headers: proxyHeaders,
      body: body as unknown as BodyInit,
    });

    const proxyBody = await proxyResp.text();
    response.writeHead(proxyResp.status, {
      ...corsHeaders(),
      "content-type": proxyResp.headers.get("content-type") || "application/json",
    });
    response.end(proxyBody);
  } catch (e) {
    sendError(response, 503, `FastAPI unavailable: ${e instanceof Error ? e.message : String(e)}`);
  }
}

const PUBLIC_ASSET_EXTENSIONS = new Set([
  ".js", ".mjs", ".css", ".map", ".ico", ".svg", ".html",
  ".png", ".jpg", ".jpeg", ".gif", ".webp",
  ".woff", ".woff2", ".ttf", ".json"
]);

function isPublicAssetPath(pathname: string): boolean {
  // Only allow single-segment asset paths (no nested dirs / traversal),
  // restricted to known static file extensions. sendPublicFile() additionally
  // enforces that the resolved path stays inside the public/ directory.
  if (pathname.includes("..") || pathname.lastIndexOf("/") !== 0) {
    return false;
  }
  const extension = path.extname(pathname).toLowerCase();
  return PUBLIC_ASSET_EXTENSIONS.has(extension);
}

function sendPublicFile(config: AppConfig, response: ServerResponse, relativePath: string): void {
  const publicDir = path.join(config.rootDir, "public");
  const filePath = path.resolve(publicDir, relativePath);

  if (!filePath.startsWith(publicDir) || !fs.existsSync(filePath)) {
    sendError(response, 404, `Static file not found: ${relativePath}`);
    return;
  }

  response.writeHead(200, {
    ...corsHeaders(),
    "content-type": readContentType(filePath)
  });
  fs.createReadStream(filePath)
    .on("error", (error) => {
      if (!response.headersSent) {
        sendError(response, 500, error.message);
      } else {
        response.destroy(error);
      }
    })
    .pipe(response);
}

function readContentType(filePath: string): string {
  const extension = path.extname(filePath).toLowerCase();
  if (extension === ".html") return "text/html; charset=utf-8";
  if (extension === ".js" || extension === ".mjs") return "text/javascript; charset=utf-8";
  if (extension === ".css") return "text/css; charset=utf-8";
  if (extension === ".json" || extension === ".map") return "application/json; charset=utf-8";
  if (extension === ".ico") return "image/x-icon";
  if (extension === ".svg") return "image/svg+xml; charset=utf-8";
  if (extension === ".png") return "image/png";
  if (extension === ".jpg" || extension === ".jpeg") return "image/jpeg";
  if (extension === ".gif") return "image/gif";
  if (extension === ".webp") return "image/webp";
  if (extension === ".woff") return "font/woff";
  if (extension === ".woff2") return "font/woff2";
  if (extension === ".ttf") return "font/ttf";
  return "application/octet-stream";
}

async function readJsonBody(request: IncomingMessage): Promise<Record<string, unknown>> {
  const chunks: Buffer[] = [];
  let totalBytes = 0;
  for await (const chunk of request) {
    const buffer = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
    totalBytes += buffer.byteLength;
    if (totalBytes > MAX_JSON_BODY_BYTES) {
      throw new HttpError(413, "JSON body is too large");
    }
    chunks.push(buffer);
  }

  const raw = Buffer.concat(chunks).toString("utf-8").trim();
  if (!raw) {
    return {};
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    throw new HttpError(400, "Invalid JSON body");
  }

  if (!isRecord(parsed)) {
    throw new HttpError(400, "JSON body must be an object");
  }

  return parsed;
}

function readRequiredString(body: Record<string, unknown>, key: string): string {
  const value = body[key];
  if (typeof value !== "string" || !value.trim()) {
    throw new HttpError(400, `Missing required string field: ${key}`);
  }

  return value.trim();
}

function enforceGenerateRateLimit(request: IncomingMessage): void {
  const key = request.socket.remoteAddress || "unknown";
  const now = Date.now();

  // Prevent memory leak: purge stale keys when map grows large
  if (generateRateLimits.size > 100) {
    for (const [k, stamps] of generateRateLimits.entries()) {
      const valid = stamps.filter((stamp) => now - stamp < GENERATE_LIMIT_WINDOW_MS);
      if (valid.length === 0) {
        generateRateLimits.delete(k);
      } else {
        generateRateLimits.set(k, valid);
      }
    }
  }

  const recent = (generateRateLimits.get(key) || []).filter((stamp) => now - stamp < GENERATE_LIMIT_WINDOW_MS);

  if (recent.length >= GENERATE_LIMIT_MAX_REQUESTS) {
    throw new HttpError(429, "Too many generate requests. Please try again later.");
  }

  recent.push(now);
  generateRateLimits.set(key, recent);
}

function sanitizeImageResponse(config: AppConfig, response: unknown): unknown {
  if (config.aiImageDryRun) {
    return response;
  }

  if (!isRecord(response)) {
    return response;
  }

  const { raw: _raw, ...safeResponse } = response;
  return safeResponse;
}

function sendJson(response: ServerResponse, statusCode: number, body: unknown): void {
  response.writeHead(statusCode, {
    ...corsHeaders(),
    "content-type": "application/json; charset=utf-8"
  });
  response.end(`${JSON.stringify(body, null, 2)}\n`);
}

function sendError(response: ServerResponse, statusCode: number, message: string): void {
  sendJson(response, statusCode, { error: message });
}

function sendEmpty(response: ServerResponse, statusCode: number): void {
  response.writeHead(statusCode, corsHeaders());
  response.end();
}

function loadRecentTasks(config: AppConfig): Array<Record<string, unknown>> {
  const taskDir = path.join(config.outputDir, "tasks");
  if (!fs.existsSync(taskDir)) {
    return [];
  }

  const files = fs.readdirSync(taskDir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => {
      const filepath = path.join(taskDir, f);
      const stat = fs.statSync(filepath);
      return { name: f, filepath, mtime: stat.mtimeMs };
    })
    .sort((a, b) => b.mtime - a.mtime)
    .slice(0, 20);

  const items: Array<Record<string, unknown>> = [];
  for (const file of files) {
    try {
      const data = JSON.parse(fs.readFileSync(file.filepath, "utf-8")) as Record<string, unknown>;
      const template = (data.template || {}) as Record<string, unknown>;
      const imageResponse = (data.image_response || {}) as Record<string, unknown>;
      const imageUrls = (imageResponse.image_urls || []) as string[];
      items.push({
        id: data.task_id || file.name.replace(".json", ""),
        title: template.title || "未命名",
        category: template.category || "",
        template_id: template.template_id || "",
        image_url: imageUrls[0] || "",
        thumbnail_url: imageUrls[0] || "",
        status: data.status || "unknown",
        created_at: data.created_at || new Date(file.mtime).toISOString(),
        source: "mock",
      });
    } catch {
      // Skip malformed task files
    }
  }
  return items;
}

function corsHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    "access-control-allow-methods": "GET,POST,OPTIONS",
    "access-control-allow-headers": "content-type",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "strict-origin-when-cross-origin"
  };

  const allowedOrigin = process.env.CORS_ALLOW_ORIGIN;
  if (allowedOrigin) {
    headers["access-control-allow-origin"] = allowedOrigin;
  }

  return headers;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
