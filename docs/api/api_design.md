# API Design

本文档描述当前本地生图任务接口设计。现阶段没有启动 HTTP 服务端，而是通过 CLI 模拟完整任务链路。

## CLI Entrypoints

生成 Prompt：

```bash
npm run generate <template_id>
```

运行生图任务：

```bash
npm run image <template_id>
```

## Environment

默认安全配置：

```text
AI_IMAGE_PROVIDER=mock
AI_IMAGE_DRY_RUN=true
OUTPUT_DIR=output
```

真实 HTTP API 配置：

```text
AI_IMAGE_PROVIDER=http
AI_IMAGE_DRY_RUN=false
AI_IMAGE_API_URL=https://your-image-api.example.com/generate
AI_IMAGE_API_KEY=your_api_key
OUTPUT_DIR=output
```

## Local Task Flow

```text
template_id
↓
load template JSON
↓
build prompt
↓
build image API request body
↓
mock or HTTP provider
↓
write output/image_task.json
```

## Image Request Body

```json
{
  "prompt": "最终拼接后的完整 Prompt",
  "negative_prompt": "负面提示词",
  "ratio": "4:5",
  "quality": "high",
  "face_strength": 0.78,
  "output_count": 1
}
```

## Mock Response

mock 模式不会请求真实接口。

```json
{
  "provider_task_id": "mock_1770000000000",
  "image_urls": [],
  "raw": {
    "mode": "mock",
    "message": "No real image API was called."
  }
}
```

## HTTP Response Normalization

HTTP 模式会读取供应商返回，并尝试从以下字段提取图片地址：

```text
url
image_url
output_url
urls
image_urls
images
data
outputs
```

如果供应商返回格式不同，需要扩展：

```text
src/services/aiImageService.ts
```

## Future Miniapp API Draft

后续做服务端时，可以把当前 CLI 工作流包装成接口。

### Create Image Task

```text
POST /api/image-tasks
```

Request:

```json
{
  "user_id": "user_001",
  "template_id": "ancient_diaochan",
  "image_url": "https://example.com/avatar.jpg",
  "options": {
    "ratio": "4:5",
    "quality": "high",
    "face_strength": 0.75
  }
}
```

Response:

```json
{
  "task_id": "image_ancient_diaochan_20260526090000",
  "status": "created"
}
```

### Get Image Task

```text
GET /api/image-tasks/:task_id
```

Response:

```json
{
  "task_id": "image_ancient_diaochan_20260526090000",
  "status": "completed",
  "image_urls": ["https://example.com/output.png"]
}
```
