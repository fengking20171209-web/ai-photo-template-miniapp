import { loadConfig } from "../src/config/appConfig.js";
import { listTemplatesWorkflow } from "../src/workflows/listTemplatesWorkflow.js";

const templates = await listTemplatesWorkflow(loadConfig());

console.log(`Available templates: ${templates.length}`);
console.table(templates);
