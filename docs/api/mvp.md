# AI 生图网站 MVP API

Base URL:

```text
http://localhost:3000
```

## 健康检查

```http
GET /health
```

响应：

```json
{
  "ok": true,
  "provider": "mock",
  "dry_run": true
}
```

## 模板列表

```http
GET /templates
```

响应：

```json
{
  "items": [
    {
      "template_id": "ancient_diaochan",
      "category": "古风美女",
      "title": "三国貂蝉",
      "ratio": "4:5",
      "style": "真人古风写真",
      "quality": "high",
      "face_strength": 0.78
    }
  ]
}
```

## 模板详情

```http
GET /templates/ancient_diaochan
```

返回完整模板 JSON。

## 创建生图任务

```http
POST /generate
Content-Type: application/json

{
  "template_id": "ancient_diaochan"
}
```

响应：

```json
{
  "task_id": "image_ancient_diaochan_20260527103000",
  "status": "completed",
  "template": {
    "template_id": "ancient_diaochan",
    "category": "古风美女",
    "title": "三国貂蝉",
    "ratio": "4:5",
    "style": "真人古风写真"
  },
  "prompt_file": "D:\\Projects\\ai-photo-template-miniapp\\output\\prompt.txt",
  "task_file": "D:\\Projects\\ai-photo-template-miniapp\\output\\tasks\\image_ancient_diaochan_20260527103000.json",
  "result_file": "D:\\Projects\\ai-photo-template-miniapp\\output\\image_task.json",
  "image_response": {
    "provider_task_id": "mock_...",
    "image_urls": []
  }
}
```

## 查询任务

```http
GET /tasks/{task_id}
```

返回任务 JSON。

## 查询任务 Prompt

```http
GET /tasks/{task_id}/prompt
```

响应：

```json
{
  "task_id": "image_ancient_diaochan_20260527103000",
  "prompt": "..."
}
```

## 说明

当前接口用于 MVP 演示和腾讯云部署骨架验证。真实头像上传、COS 存储、数据库任务表、支付解锁和真实生图 API 会在后续阶段接入。
