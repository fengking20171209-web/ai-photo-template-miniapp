# 后端 API 合约（Round 6 确认版）

> 生成时间：2026-06-02  
> 后端服务：FastAPI @ localhost:8001  
> 前端代理：Node.js @ localhost:3000

---

## 一、路由注册表（`backend/main.py`）

| Router 文件 | Prefix | Tag |
|---|---|---|
| `templates.py` | `/api` | templates |
| `image_gen.py` | `/generate` | generate |
| `cos_serve.py` | *(无)* | cos-serve |
| `cos_sts.py` | `/cos` | cos |
| `images.py` | `/images` | images |

---

## 二、完整端点清单

### 2.1 模板服务（`templates.py`，前缀 `/api`）

#### `GET /api/templates`
**功能**：列出所有模板摘要  
**参数**：无  
**响应**：
```json
{
  "total": 54,
  "items": [
    {
      "template_id": "ancient_diaochan",
      "category": "古风",
      "title": "貂蝉",
      "style": "古典美",
      "ratio": "9:16",
      "face_lock": true,
      "scene": "月下庭院",
      "clothing": "汉服",
      "price": 0.0,
      "is_free": true
    }
  ]
}
```

---

#### `GET /api/templates/search`
**功能**：搜索/筛选/分页模板  
**参数**：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `q` | string | 否 | 关键词（搜索 title/template_id/style/scene/clothing/tags） |
| `category` | string | 否 | 分类过滤 |
| `is_free` | bool | 否 | 免费/付费过滤 |
| `page` | int | 否 | 页码，默认 1 |
| `limit` | int | 否 | 每页条数，默认 20 |
| `sort` | string | 否 | 排序字段：`title`（默认）、`template_id`、`category` |

**响应**：
```json
{
  "total": 12,
  "page": 1,
  "pages": 2,
  "items": [
    {
      "template_id": "...",
      "category": "...",
      "title": "...",
      "style": "...",
      "ratio": "...",
      "face_lock": false,
      "scene": "...",
      "clothing": "...",
      "tags": [...],
      "description": "...",
      "price": 0.0,
      "is_free": true
    }
  ]
}
```

---

#### `GET /api/templates/recommended`
**功能**：推荐模板（优先免费 + 分类多样性）  
**参数**：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `limit` | int | 否 | 返回数量，默认 8 |

**响应**：同 `GET /api/templates` 的 `items` 格式

---

#### `GET /api/templates/recently-used`
**功能**：最近使用模板（基于埋点事件）  
**参数**：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `days` | int | 否 | 统计天数，默认 30 |
| `limit` | int | 否 | 返回数量，默认 8 |

**响应**：
```json
{
  "total": 3,
  "items": [
    {
      "template_id": "...",
      "category": "...",
      "title": "...",
      "style": "...",
      "ratio": "...",
      "face_lock": false,
      "scene": "...",
      "clothing": "...",
      "price": 0.0,
      "is_free": true,
      "last_used": "2026-06-01T12:00:00"
    }
  ]
}
```

---

#### `GET /api/templates/{template_id}`
**功能**：单个模板完整详情  
**参数**：路径参数 `template_id`  
**响应**：完整模板 JSON（含 `prompt_blocks`、`options`、`negative_prompt` 等全部字段）

**错误**：
- `404`：模板不存在

---

#### `POST /api/analytics/event`
**功能**：埋点上报  
**Content-Type**：`application/x-www-form-urlencoded`（Form）  
**参数**：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `event_type` | string | 是 | 事件类型：`click`、`generate`、`batch_generate`、`favorite` |
| `template_id` | string | 否 | 关联模板 ID |
| `query` | string | 否 | 搜索关键词 |
| `category` | string | 否 | 分类 |
| `session_id` | string | 否 | 会话 ID |

**响应**：
```json
{"ok": true}
```

---

#### `GET /api/analytics/popular`
**功能**：热门模板排行  
**参数**：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `days` | int | 否 | 统计天数，默认 7 |
| `limit` | int | 否 | 返回数量，默认 10 |

**响应**：
```json
{
  "days": 7,
  "items": [
    {"template_id": "...", "score": 15}
  ]
}
```

---

### 2.2 图片生成（`image_gen.py`，前缀 `/generate`）

#### `POST /generate`
**功能**：生成图片（模板驱动或自由 prompt）  
**Content-Type**：`application/json`  
**请求体**：
```json
{
  "template_id": "ancient_diaochan",
  "prompt": null,
  "size": null,
  "n": 1
}
```

**响应**：
```json
{
  "status": "completed",
  "task_id": "123",
  "template": {
    "template_id": "ancient_diaochan",
    "category": "古风",
    "title": "貂蝉",
    "style": "古典美",
    "ratio": "9:16",
    "face_lock": true,
    "price": 0.0,
    "is_free": true
  },
  "image_response": {
    "image_urls": ["/placeholder.svg"],
    "raw": {
      "mode": "mock",
      "fallback": true
    }
  },
  "error": null
}
```

**说明**：
- `mode: "mock"` 表示未调用付费 API（默认行为）
- `mode: "real"` 表示 SenseTime API 真实生成（需 `ENABLE_REAL_IMAGE_API=true`）
- `task_id` 实为 `Image` 表记录的 `id`

---

### 2.3 COS 图库（`cos_serve.py`，无前缀）

#### `GET /images/recent`
**功能**：列出最近生成的图片  
**参数**：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `limit` | int | 否 | 返回数量，默认 20 |

**响应**：
```json
{
  "total": 5,
  "items": [
    {
      "id": 123,
      "title": "Generated: ...",
      "prompt": "原始提示词",
      "revised_prompt": "修订后提示词",
      "image_url": "/placeholder.svg",
      "thumbnail_url": "/placeholder.svg",
      "created_at": "2026-06-01T12:00:00",
      "tags": ["mock"],
      "source": "mock"
    }
  ]
}
```

**说明**：
- `source: "mock"` 的项使用 `thumbnail_url`（值为 `/placeholder.svg`）
- `source: "sense_image"` 的项使用 `/cos/image/{source_id}` 代理 URL

---

#### `GET /cos/image/{cos_key}`
**功能**：代理 COS 图片（签名 URL 跳转）  
**参数**：路径参数 `cos_key`（支持 `ref/` 和 `gen/` 前缀）  
**响应**：`302 Redirect` 到 COS 签名 URL（有效期 1 小时）

---

### 2.4 COS 临时凭证（`cos_sts.py`，前缀 `/cos`）

#### `GET /cos/credentials`
**功能**：获取腾讯云 COS STS 临时凭证  
**参数**：无  
**响应**：
```json
{
  "credentials": {
    "tmpSecretId": "...",
    "tmpSecretKey": "...",
    "sessionToken": "..."
  },
  "expiredTime": 1717200000,
  "bucket": "ai-fashion-gen-shanghai-1427746697",
  "region": "ap-shanghai"
}
```

---

### 2.5 图片搜索（`images.py`，前缀 `/images`）

#### `GET /images/`
**功能**：搜索图库图片（支持关键词、标签、日期范围、分页）  
**参数**：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `q` | string | 否 | 关键词（搜索 title 和 prompt） |
| `tags` | string[] | 否 | 标签过滤（需全部匹配） |
| `start_date` | datetime | 否 | 开始时间 |
| `end_date` | datetime | 否 | 结束时间 |
| `page` | int | 否 | 页码，默认 1 |
| `limit` | int | 否 | 每页条数，默认 20，最大 100 |

**响应**：`SearchResponse` 模型

---

### 2.6 健康检查（`main.py`，直接挂载）

#### `GET /health`
**功能**：服务健康检查  
**响应**：
```json
{"ok": true, "backend": "fastapi", "database": "sqlite"}
```

---

## 三、缺失端点（需补齐）

| # | 方法 | 前端调用 | 缺失原因 | 建议后端路由 |
|---|---|---|---|---|
| 1 | `GET` | `/tasks/{id}/prompt` | 无对应 FastAPI 路由 | `GET /images/{id}` |
| 2 | `DELETE` | `/tasks/{id}` | 无对应 FastAPI 路由 | `DELETE /images/{id}` |

### 3.1 建议新增：`GET /images/{id}`

**功能**：获取单条图片记录详情（含 prompt）  
**参数**：路径参数 `id`（整数）  
**响应**：
```json
{
  "id": 123,
  "title": "...",
  "prompt": "原始提示词",
  "revised_prompt": "修订后提示词",
  "image_url": "/placeholder.svg",
  "thumbnail_url": "/placeholder.svg",
  "created_at": "2026-06-01T12:00:00",
  "tags": ["mock"],
  "source": "mock"
}
```

**错误**：
- `404`：记录不存在

### 3.2 建议新增：`DELETE /images/{id}`

**功能**：删除单条图片记录  
**参数**：路径参数 `id`（整数）  
**响应**：
```json
{"deleted": true, "id": 123}
```

**说明**：当前 `Image` 表无软删除字段，建议物理删除。

---

## 四、前端 ↔ 后端路径对照

| 前端调用 | 代理层映射 | FastAPI 实际端点 | 状态 |
|---|---|---|---|
| `GET /api/templates` | 透传 | `GET /api/templates` | ✅ |
| `GET /api/templates/{id}` | 动态匹配 | `GET /api/templates/{id}` | ✅ |
| `GET /templates/search` | 透传 | `GET /api/templates/search` | ✅ |
| `GET /templates/recommended` | 透传 | `GET /api/templates/recommended` | ✅ |
| `GET /templates/recently-used` | 透传 | `GET /api/templates/recently-used` | ✅ |
| `POST /generate` | 透传 | `POST /generate` | ✅ |
| `GET /images/recent` | 透传 | `GET /images/recent` | ✅ |
| `POST /analytics/event` | 透传 | `POST /api/analytics/event` | ✅ |
| `GET /analytics/popular` | 透传 | `GET /api/analytics/popular` | ✅（预留）|
| `GET /cos/credentials` | 透传 | `GET /cos/credentials` | ✅ |
| `GET /tasks/{id}/prompt` | ❌ 本地 fs | — | ❌ 需新增 |
| `DELETE /tasks/{id}` | ❌ 本地 fs | — | ❌ 需新增 |

---

## 五、数据模型（`backend/models.py`）

### `Image` 表

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | Integer PK | 自增主键 |
| `title` | String(255) | 图片标题 |
| `prompt` | Text | 原始提示词 |
| `revised_prompt` | Text | 修订后提示词 |
| `image_url` | String(1024) | 图片 URL（COS 路径或 placeholder）|
| `thumbnail_url` | String(1024) | 缩略图 URL |
| `tags` | JSON | 标签数组 |
| `description` | Text | 描述 |
| `source` | String(50) | 来源：`sense_image` / `mock` |
| `source_id` | String(255) | COS key 或 mock ID |
| `created_at` | DateTime | 创建时间 |
| `updated_at` | DateTime | 更新时间 |

### `UserEvent` 表

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | Integer PK | 自增主键 |
| `event_type` | String(50) | 事件类型 |
| `template_id` | String(255) | 关联模板 ID |
| `query` | String(500) | 搜索词 |
| `category` | String(100) | 分类 |
| `session_id` | String(255) | 会话 ID |
| `created_at` | DateTime | 创建时间 |

---

## 六、环境变量

| 变量 | 默认值 | 用途 |
|---|---|---|
| `PORT` | `3000` | Node.js 前端服务端口 |
| `FASTAPI_PORT` | `8000` | FastAPI 后端端口（代理目标） |
| `HOST` | `127.0.0.1` | Node.js 监听地址 |
| `CORS_ALLOW_ORIGIN` | `http://localhost:3000` | CORS 允许的源 |
| `ENABLE_REAL_IMAGE_API` | *(空)* | 是否启用真实图片生成（默认 `false`）|
| `COS_BUCKET_GEN` | *(空)* | COS 生成图片存储桶 |
| `COS_BUCKET_REF` | *(空)* | COS 参考图片存储桶 |
| `COS_REGION` | *(空)* | COS 区域 |
| `COS_SECRET_ID` | *(空)* | COS 密钥 ID |
| `COS_SECRET_KEY` | *(空)* | COS 密钥 |
| `SENSE_API_KEY` | *(空)* | SenseTime API 密钥 |

---

*文档路径：`docs/api/backend_contract.md`*
