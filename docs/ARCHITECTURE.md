# Architecture

## 系统概览 / System Overview

```
[Browser] ←→ [Node.js API :3000] ←→ [templates/*.json]
                ↓
           [FastAPI :8000] ←→ [SQLite Gallery DB]
```

## 数据流 / Data Flow

1. **模板加载 / Template Loading**: `src/templates/templateRepository.ts` reads JSON from `templates/`
2. **提示词构建 / Prompt Building**: `src/services/promptBuilder.ts` concatenates prompt_blocks
3. **图片生成 / Generation**: `src/services/aiImageService.ts` sends to configured API (mock by default)
4. **结果存储 / Storage**: Results saved to `output/` and optionally gallery database

## 模块映射 / Module Map

| 模块 / Module | 文件 / File | 职责 / Responsibility |
|--------|------|---------------|
| Config | `src/config/appConfig.ts` | Environment and path configuration |
| Template Types | `src/types/template.ts` | TypeScript interfaces for templates |
| Task Types | `src/types/task.ts` | Generation task structure |
| Schema Validation | `src/templates/templateSchema.ts` | Runtime template validation |
| Template Loader | `src/templates/templateRepository.ts` | File I/O and caching |
| Prompt Builder | `src/services/promptBuilder.ts` | Final prompt assembly |
| Image Service | `src/services/aiImageService.ts` | API client (mock/HTTP) |
| Generate Workflow | `src/workflows/generatePromptWorkflow.ts` | End-to-end prompt generation |
