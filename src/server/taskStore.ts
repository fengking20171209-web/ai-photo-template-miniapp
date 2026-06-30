import fs from "node:fs";
import path from "node:path";
import type { AppConfig } from "../config/appConfig.js";
import type { ImageTask } from "../types/task.js";

export function saveTask(config: AppConfig, task: ImageTask): string {
  const taskDir = getTaskDir(config);
  fs.mkdirSync(taskDir, { recursive: true });

  const taskFile = path.join(taskDir, `${safeTaskId(task.task_id)}.json`);
  fs.writeFileSync(taskFile, `${JSON.stringify(task, null, 2)}\n`, "utf-8");
  return taskFile;
}

export function loadTask(config: AppConfig, taskId: string): ImageTask {
  const taskFile = path.join(getTaskDir(config), `${safeTaskId(taskId)}.json`);

  if (!fs.existsSync(taskFile)) {
    throw new Error(`Task not found: ${taskId}`);
  }

  return JSON.parse(fs.readFileSync(taskFile, "utf-8")) as ImageTask;
}

function getTaskDir(config: AppConfig): string {
  return path.join(config.outputDir, "tasks");
}

function safeTaskId(taskId: string): string {
  return path.basename(taskId).replace(/[^a-zA-Z0-9_-]/g, "_");
}
