import fs from "node:fs";
import path from "node:path";
import type { ImageTemplate } from "../types/template.js";
import { buildNegativePrompt } from "./promptBuilder.js";

export interface ReservedImageRequest {
  prompt: string;
  negative_prompt: string;
  ratio: string;
  quality: string;
  face_strength: number;
  output_count: number;
}

export function createReservedImageRequest(template: ImageTemplate, prompt: string): ReservedImageRequest {
  return {
    prompt,
    negative_prompt: buildNegativePrompt(template),
    ratio: template.ratio,
    quality: template.options.quality,
    face_strength: template.options.face_strength,
    output_count: template.options.output_count
  };
}

export interface ImageGenerationResult {
  provider_task_id?: string;
  image_urls: string[];
  raw?: unknown;
}

export interface ImageGenerationProvider {
  generate(request: ReservedImageRequest): Promise<ImageGenerationResult>;
}

function createPlaceholderDataUri(width: number, height: number): string {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">`
    + `<rect width="100%" height="100%" fill="#f0f0f0"/>`
    + `<rect x="10%" y="10%" width="80%" height="80%" fill="none" stroke="#ccc" stroke-width="2" stroke-dasharray="10,5"/>`
    + `<text x="50%" y="45%" dominant-baseline="middle" text-anchor="middle" font-family="system-ui,sans-serif" font-size="20" fill="#888">Mock Image</text>`
    + `<text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle" font-family="system-ui,sans-serif" font-size="14" fill="#aaa">${width} \u00d7 ${height}</text>`
    + `</svg>`;
  const base64 = Buffer.from(svg).toString("base64");
  return `data:image/svg+xml;base64,${base64}`;
}

function resolvePlaceholderUrl(ratio: string): string {
  const isPortrait = ratio === "9:16";
  const filename = isPortrait ? "placeholder-portrait.svg" : "placeholder.svg";
  const filepath = path.resolve(process.cwd(), "public", filename);

  if (fs.existsSync(filepath)) {
    return `/${filename}`;
  }

  const width = isPortrait ? 512 : 768;
  const height = isPortrait ? 768 : 512;
  return createPlaceholderDataUri(width, height);
}

export class MockImageGenerationProvider implements ImageGenerationProvider {
  async generate(request: ReservedImageRequest): Promise<ImageGenerationResult> {
    return {
      provider_task_id: `mock_${Date.now()}`,
      image_urls: [resolvePlaceholderUrl(request.ratio)],
      raw: {
        mode: "mock",
        message: "No real image API was called.",
        request
      }
    };
  }
}

export class HttpImageGenerationProvider implements ImageGenerationProvider {
  private readonly timeoutMs = 30_000;

  constructor(
    private readonly apiUrl: string,
    private readonly apiKey?: string
  ) {}

  async generate(request: ReservedImageRequest): Promise<ImageGenerationResult> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(this.apiUrl, {
        method: "POST",
        headers: {
          "content-type": "application/json",
          ...(this.apiKey ? { authorization: `Bearer ${this.apiKey}` } : {})
        },
        body: JSON.stringify(request),
        signal: controller.signal
      });

      const raw = await readJsonResponse(response, this.timeoutMs);

      if (!response.ok) {
        throw new Error(`Image API request failed: ${response.status} ${response.statusText}`);
      }

      return normalizeImageResponse(raw);
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error(`Image API request timed out after ${this.timeoutMs}ms`);
      }
      throw error;
    } finally {
      clearTimeout(timeout);
    }
  }
}

async function readJsonResponse(response: Response, timeoutMs: number): Promise<unknown> {
  const text = await readResponseText(response, timeoutMs);
  if (!text) {
    return {};
  }

  try {
    return JSON.parse(text);
  } catch {
    return { text };
  }
}

async function readResponseText(response: Response, timeoutMs: number): Promise<string> {
  let timeout: ReturnType<typeof setTimeout> | undefined;
  try {
    return await Promise.race([
      response.text(),
      new Promise<string>((_resolve, reject) => {
        timeout = setTimeout(() => reject(new Error(`Image API response body timed out after ${timeoutMs}ms`)), timeoutMs);
      })
    ]);
  } finally {
    if (timeout) {
      clearTimeout(timeout);
    }
  }
}

function normalizeImageResponse(raw: unknown): ImageGenerationResult {
  const record = isRecord(raw) ? raw : {};
  const imageUrls = collectImageUrls(record);

  return {
    provider_task_id: readOptionalString(record, "task_id") || readOptionalString(record, "id"),
    image_urls: imageUrls,
    raw
  };
}

function collectImageUrls(record: Record<string, unknown>): string[] {
  const urls = new Set<string>();

  for (const key of ["url", "image_url", "output_url"]) {
    const value = record[key];
    if (typeof value === "string") {
      urls.add(value);
    }
  }

  for (const key of ["urls", "image_urls", "images", "data", "outputs"]) {
    const value = record[key];
    if (Array.isArray(value)) {
      for (const item of value) {
        if (typeof item === "string") {
          urls.add(item);
        } else if (isRecord(item)) {
          for (const nestedKey of ["url", "image_url", "output_url"]) {
            const nestedValue = item[nestedKey];
            if (typeof nestedValue === "string") {
              urls.add(nestedValue);
            }
          }
        }
      }
    }
  }

  return [...urls];
}

function readOptionalString(record: Record<string, unknown>, key: string): string | undefined {
  const value = record[key];
  return typeof value === "string" ? value : undefined;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
