import { loadConfig } from "../src/config/appConfig.js";

const config = loadConfig();

console.log("=== Node.js HTTP API Path Test ===");
console.log("AI_IMAGE_PROVIDER:", config.aiImageProvider);
console.log("AI_IMAGE_DRY_RUN:", config.aiImageDryRun);
console.log("AI_IMAGE_API_URL:", config.aiImageApiUrl || "(not set)");
console.log("AI_IMAGE_API_KEY:", config.aiImageApiKey ? "(set, length=" + config.aiImageApiKey.length + ")" : "(not set)");

if (!config.aiImageApiUrl) {
  console.log("\n❌ AI_IMAGE_API_URL not configured. Cannot test HTTP path.");
  process.exit(1);
}

if (!config.aiImageApiKey) {
  console.log("\n⚠️ AI_IMAGE_API_KEY not set. Testing without auth (may fail).");
}

// Try a lightweight ping/health check if the URL is set
async function testConnection() {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    const response = await fetch(config.aiImageApiUrl!, {
      method: "GET",
      signal: controller.signal,
    });
    clearTimeout(timeout);
    console.log("\nHTTP Status:", response.status, response.statusText);
    const text = await response.text();
    console.log("Response preview:", text.slice(0, 200));
  } catch (error) {
    console.log("\n❌ Connection failed:", error instanceof Error ? error.message : String(error));
  }
}

testConnection();
