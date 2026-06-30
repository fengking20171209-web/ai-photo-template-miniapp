# 前端交接文档（给 Codex GPT-5.5 接续 UI）

> 接替 Claude Sonnet 继续 `public/` 前端开发。后端 API 已就绪稳定,本文档是与后端协作的唯一契约。

## 1. 运行架构

- **单端口 8000**:FastAPI(`backend/main.py`)同时提供 API 和静态前端(`public/` 挂载在 `/`)。
- 访问 `http://127.0.0.1:8000` 即整个应用。前端调用的 API 与页面同源,无需跨域/代理。
- 启动:`python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`
- 数据库:SQLite(`aigallery.db`),WAL 模式。
- 前端为原生 JS(`public/`):`index.html` / `app.js` / `chat.js` / `api.js` / `styles.css` / `utils.js`。

## 2. 后端 API 契约

### 2.1 模型发现（构建模型选择器）
`GET /generate/providers` →
```json
{ "providers": [
    { "id":"sensenova","name":"SenseNova U1","capabilities":["text2img"],"configured":true },
    { "id":"agnes","name":"Agnes Image 2.1 Flash","capabilities":["text2img","img2img"],"configured":true } ],
  "default":"sensenova","real_enabled":true }
```
（`app.js` 的 `loadProviders()` 已在用。）

### 2.2 生成图片（文生图 / 图生图）
`POST /generate`，body：
- `template_id` 或 `prompt`（二选一）
- `provider`：`sensenova` | `agnes`（可选）
- `image`：图生图输入,公网 URL 或 **Data URI Base64**（`data:image/...;base64,...`）。传了就自动用 Agnes。
- `size`、`n`（可选）

响应：`image_response.image_urls[0]` 即图片地址；`raw.provider` / `raw.mode`(`real`|`mock`)。

耗时：文生图 ~13–30s，图生图 ~30–50s。前端超时建议 ≥ 360s。

### 2.3 作品集（持久化）
- `GET /images/recent?limit=20` → `{ items:[{ id,title,thumbnail_url,image_url,created_at,source,... }] }`
- `GET /images/{id}`、`DELETE /images/{id}`
- 生成图已**本地持久化**:后端把图下载到 `output/generated/`,以 `/generated/...` 提供,**永久有效**(不再是过期直链)。前端直接用 `thumbnail_url`/`image_url` 即可。

### 2.4 写真助手对话（⚠️ 重要安全改动）
**`public/chat.js` 当前把 Agnes 聊天 API key 硬编码在浏览器里并直连 Agnes —— 这会向每个访问者泄露密钥,必须改掉。**

后端已提供代理端点:
- `POST /chat`，body 为 OpenAI 风格 `{ messages:[...], stream:true }`（`model`/密钥由服务端注入,无需前端传）。
- 支持 **SSE 流式**（`text/event-stream`）和非流式（`stream:false`）。

**Codex 待办**:把 `chat.js` 改为:
- 删除 `CHAT_API_URL`、`CHAT_API_KEY`、`CHAT_MODEL` 常量
- 请求地址改为同源 `'/chat'`，去掉 `Authorization` 头
- body 去掉 `model`，保留 `messages`/`stream`（system prompt 可继续在前端拼,或后端拼——目前后端原样透传 messages）
- SSE 解析逻辑不变（后端透传上游 SSE 格式）

## 3. 模板相关
- `GET /api/templates` → `{ items:[...] }`（54 个模板）
- `GET /api/templates/{id}`、`/api/templates/recommended`、`/api/templates/recent`

## 4. 约束与约定
- **只改 `public/`**;后端(`backend/`、`src/`)由另一负责人维护,改后端 API 前先沟通。
- 不要在前端硬编码任何密钥;需要密钥的能力一律走后端端点。
- 详细生图字段见 `docs/api/image-generation.md`。

## 5. 当前前端状态（Sonnet 完成的）
- 三栏布局 + 右侧"写真助手"对话面板,模板列表(54)、生成流程、作品集、模型选择器(`/generate/providers`)均已接通。
- 真实出图正常(商汤/Agnes)。
- 唯一已知安全债:`chat.js` 客户端密钥(见 2.4)。
