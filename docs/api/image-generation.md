# 生图 API 契约（前端集成用）

> 给前端 UI（含模型选择器、图生图）集成的接口说明。所有请求经 Node 服务（端口 3000）代理到 FastAPI（端口 8000）。

## 1. 列出可用模型（构建模型选择器）

```
GET /generate/providers
```

响应：

```json
{
  "providers": [
    { "id": "sensenova", "name": "SenseNova U1", "model": "sensenova-u1-fast",
      "capabilities": ["text2img"], "configured": true },
    { "id": "agnes", "name": "Agnes Image 2.1 Flash", "model": "agnes-image-2.1-flash",
      "capabilities": ["text2img", "img2img"], "configured": true }
  ],
  "default": "sensenova",
  "real_enabled": true
}
```

- `configured`: 该模型是否已配置可用密钥。建议选择器只展示 `configured: true` 的项。
- `capabilities`: 是否支持 `img2img`（图生图）。只有 `agnes` 支持。
- `real_enabled`: 若为 false，后端处于 mock 模式（出占位图）。

## 2. 生成图片（文生图 / 图生图）

```
POST /generate
Content-Type: application/json
```

请求体：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `template_id` | string | 二选一 | 模板 ID，用模板提示词生成 |
| `prompt` | string | 二选一 | 自定义文本提示词（与 template_id 二选一，同时给时模板优先）|
| `provider` | string | 否 | `sensenova` \| `agnes`，缺省用服务端默认 |
| `image` | string \| string[] | 否 | **图生图输入**：公网 HTTPS 图片 URL 或 Data URI（`data:image/png;base64,...`）。传了就自动走 Agnes |
| `size` | string | 否 | 输出尺寸或比例（如 `1024x1280` 或 `4:5`），缺省按模板比例 |
| `n` | int | 否 | 数量，默认 1 |

响应：

```json
{
  "status": "completed",
  "task_id": "123",
  "template": { "template_id": "...", "ratio": "4:5", "...": "..." },
  "image_response": {
    "image_urls": ["https://.../output.png"],
    "raw": { "mode": "real", "provider": "agnes" }
  },
  "error": null
}
```

- 图片地址取 `image_response.image_urls[0]`。
- `raw.mode`：`real`（真实出图）或 `mock`（占位图，未配置/调用失败时回退）。
- `raw.provider`：实际使用的模型。

## 3. 图生图用法（上传照片 → 套风格）

前端把用户上传的照片读成 **Data URI Base64**（`FileReader.readAsDataURL`），随生成请求传入 `image`：

```js
const body = {
  template_id: selectedTemplateId,   // 或 prompt: "自定义转换指令"
  provider: "agnes",                 // 可省略，传 image 时后端自动用 agnes
  image: dataUri                      // "data:image/png;base64,...."
};
const res = await fetch("/generate", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body)
});
```

注意：
- 图生图仅 `agnes` 支持；传了 `image`，后端会忽略 `provider` 强制用 agnes。
- 输入图若用 URL，必须公网可访问（无需登录/cookie）。本地上传建议用 Data URI，避免依赖 COS。
- 生成耗时：文生图约 13–28s，图生图约 30–50s。客户端超时建议 ≥ 360s。

## 4. 时序与状态

- 接口是**同步**的：请求返回即代表完成（`status: completed`）或失败回退 mock。
- 失败永不报 5xx 给前端，而是回退 mock 出占位图，保证 UX 不中断。
