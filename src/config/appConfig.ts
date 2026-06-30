import fs from "node:fs";
import path from "node:path";

export interface AppConfig {
  rootDir: string;
  templatesDir: string;
  outputDir: string;
  aiImageProvider: "mock" | "http";
  aiImageDryRun: boolean;
  aiImageApiUrl?: string;
  aiImageApiKey?: string;
  // GBrain 客户端配置
  gbrainApiUrl?: string;
  gbrainTimeoutMs: number;
  gbrainEnabled: boolean;
}

export function loadConfig(): AppConfig {
  loadDotEnvFile();

  const rootDir = process.cwd();
  const outputDir = path.resolve(rootDir, process.env.OUTPUT_DIR || "output");

  const gbrainApiUrl = process.env.GBRAIN_API_URL || undefined;
  const gbrainEnabled = !!gbrainApiUrl;
  const gbrainTimeoutMs = parseInt(process.env.GBRAIN_TIMEOUT_MS || "30000", 10);

  return {
    rootDir,
    templatesDir: path.resolve(rootDir, "templates"),
    outputDir,
    aiImageProvider: readProvider(process.env.AI_IMAGE_PROVIDER),
    aiImageDryRun: readBoolean(process.env.AI_IMAGE_DRY_RUN, true),
    aiImageApiUrl: process.env.AI_IMAGE_API_URL || undefined,
    aiImageApiKey: process.env.AI_IMAGE_API_KEY || undefined,
    gbrainApiUrl,
    gbrainTimeoutMs,
    gbrainEnabled
  };
}

function readProvider(value: string | undefined): "mock" | "http" {
  if (value === "http" || value === "sensetime") {
    return "http";
  }

  return "mock";
}

function readBoolean(value: string | undefined, fallback: boolean): boolean {
  if (value === undefined) {
    return fallback;
  }

  return ["1", "true", "yes", "on"].includes(value.toLowerCase());
}

function loadDotEnvFile(): void {
  const envPath = path.resolve(process.cwd(), ".env");

  if (!fs.existsSync(envPath)) {
    return;
  }

  const lines = fs.readFileSync(envPath, "utf-8").split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) {
      continue;
    }

    const separatorIndex = trimmed.indexOf("=");
    if (separatorIndex === -1) {
      continue;
    }

    const key = trimmed.slice(0, separatorIndex).trim();
    const value = trimmed.slice(separatorIndex + 1).trim().replace(/^["']|["']$/g, "");

    if (key && process.env[key] === undefined) {
      process.env[key] = value;
    }
  }
}
