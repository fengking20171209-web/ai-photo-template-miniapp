import { loadConfig } from "../src/config/appConfig.js";
import { runImageTaskWorkflow } from "../src/workflows/runImageTaskWorkflow.js";

const templateId = process.argv[2] || "ancient_diaochan";

try {
  const result = await runImageTaskWorkflow(loadConfig(), templateId);

  console.log("Image task finished");
  console.log(`Template: ${result.task.template.title} (${result.task.template.template_id})`);
  console.log(`Status: ${result.task.status}`);
  console.log(`Prompt file: ${result.promptFile}`);
  console.log(`Task file: ${result.resultFile}`);

  if (result.task.image_response?.image_urls.length) {
    console.log("Image URLs:");
    for (const url of result.task.image_response.image_urls) {
      console.log(`- ${url}`);
    }
  }

  if (result.task.error) {
    console.error(result.task.error);
    process.exit(1);
  }
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  console.error(message);
  process.exit(1);
}
