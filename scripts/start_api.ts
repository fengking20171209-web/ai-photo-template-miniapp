import { loadConfig } from "../src/config/appConfig.js";
import { createApiServer } from "../src/server/httpServer.js";

const config = loadConfig();
const port = Number(process.env.PORT) || 3000;
const host = process.env.HOST || "127.0.0.1";

const server = createApiServer(config);

server.listen(port, host, () => {
  console.log(`AI photo template API listening on http://${host}:${port}`);
  console.log(`Image provider: ${config.aiImageDryRun ? "mock" : config.aiImageProvider}`);
});
