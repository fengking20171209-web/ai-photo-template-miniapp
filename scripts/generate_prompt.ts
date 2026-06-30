import { loadConfig } from "../src/config/appConfig.js";
import { generatePromptWorkflow } from "../src/workflows/generatePromptWorkflow.js";

const templateId = process.argv[2] || "ancient_diaochan";

try {
  const result = await generatePromptWorkflow(loadConfig(), templateId);

  console.log("Prompt generated");
  console.log(`Template: ${result.task.template.title} (${result.task.template.template_id})`);
  console.log(`Prompt file: ${result.promptFile}`);
  console.log(`Task file: ${result.taskFile}`);
  console.log("\n--- PROMPT ---\n");
  console.log(result.prompt);
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  console.error(message);
  process.exit(1);
}
