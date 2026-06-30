import type { ImageTemplate } from "./template.js";

export type GenerateTaskStatus = "created" | "api_reserved" | "completed" | "failed";
export type ImageProviderName = "mock" | "http" | "reserved";

export interface GenerateTask {
  task_id: string;
  created_at: string;
  status: GenerateTaskStatus;
  template: Pick<ImageTemplate, "template_id" | "category" | "title" | "ratio" | "style">;
  prompt_file: string;
  image_request: {
    provider: "reserved";
    api_url?: string;
    will_call_api: false;
    request_body: {
      prompt: string;
      negative_prompt: string;
      ratio: string;
      quality: string;
      face_strength: number;
      output_count: number;
    };
  };
}

export interface ImageTask {
  task_id: string;
  created_at: string;
  updated_at: string;
  status: GenerateTaskStatus;
  template: Pick<ImageTemplate, "template_id" | "category" | "title" | "ratio" | "style">;
  prompt_file: string;
  result_file: string;
  image_request: {
    provider: ImageProviderName;
    api_url?: string;
    dry_run: boolean;
    request_body: {
      prompt: string;
      negative_prompt: string;
      ratio: string;
      quality: string;
      face_strength: number;
      output_count: number;
    };
  };
  image_response?: {
    provider_task_id?: string;
    image_urls: string[];
    raw?: unknown;
  };
  error?: string;
}
