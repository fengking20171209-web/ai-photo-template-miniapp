# 图片搜索接口

## 接口概述

本接口用于在 AI 图库中搜索图片，支持关键词模糊匹配、标签精确筛选、日期范围过滤以及分页查询。返回结果按创建时间降序排列（最新的排在最前面）。

| 项目 | 说明 |
|------|------|
| 接口用途 | 搜索图片列表，支持多条件组合筛选 |
| 认证要求 | 暂不需要认证 |
| 数据存储 | PostgreSQL，标签字段使用 JSONB 类型存储 |
| 排序规则 | 按 `created_at` 降序排列 |

---

## 请求方法/路径

```
GET /images/
```

**Base URL**（开发环境示例）：`http://localhost:8000`

**完整请求地址示例**：`http://localhost:8000/images/?q=nature&tags=ai&page=1&limit=20`

---

## 请求参数

### 查询参数（Query Parameters）

所有参数均通过 URL 查询字符串传递。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `q` | string | 否 | - | 搜索关键词，对 `title`（标题）和 `prompt`（提示词）字段进行模糊匹配，不区分大小写 |
| `tags` | string[] | 否 | - | 标签数组，精确匹配。可多次传递，如 `?tags=nature&tags=ai`，返回的图片必须同时包含所有指定的标签 |
| `start_date` | datetime | 否 | - | 开始日期，ISO 8601 格式，如 `2024-01-01T00:00:00`，筛选 `created_at >= start_date` 的记录 |
| `end_date` | datetime | 否 | - | 结束日期，ISO 8601 格式，如 `2024-12-31T23:59:59`，筛选 `created_at <= end_date` 的记录 |
| `page` | integer | 否 | 1 | 页码，最小值为 **1**，表示第几页 |
| `limit` | integer | 否 | 20 | 每页返回数量，范围为 **1-100** |

### 参数组合说明

- 所有参数均可独立使用，也可任意组合。不传任何参数时返回全部图片（按时间降序、默认分页）。
- `tags` 参数多次传递时，图片必须**同时包含**所有指定标签（逻辑与关系），而非包含任一标签。
- `start_date` 和 `end_date` 可单独使用，也可组合使用以限定完整的日期范围。
- `q` 关键词搜索同时在 `title` 和 `prompt` 两个字段中匹配，使用 ILIKE 不区分大小写。

---

## 请求示例

### 示例 1：关键词搜索

搜索标题或提示词中包含 "nature" 的图片，取第 1 页，每页 20 条。

```bash
curl -X GET "http://localhost:8000/images/?q=nature&page=1&limit=20" \
  -H "Accept: application/json"
```

### 示例 2：多标签精确筛选

搜索同时包含 "nature" 和 "ai" 两个标签的图片（JSONB 数组包含匹配）。

```bash
curl -X GET "http://localhost:8000/images/?tags=nature&tags=ai&page=1&limit=20" \
  -H "Accept: application/json"
```

### 示例 3：日期范围 + 分页

搜索 2024 年 1 月期间创建的图片，取第 2 页，每页 10 条。

```bash
curl -X GET "http://localhost:8000/images/?start_date=2024-01-01T00:00:00&end_date=2024-01-31T23:59:59&page=2&limit=10" \
  -H "Accept: application/json"
```

### 示例 4：组合查询（关键词 + 标签 + 日期）

搜索标题/提示词包含 "sunset"、同时带有 "landscape" 标签、且在 2024 年上半年创建的图片。

```bash
curl -X GET "http://localhost:8000/images/?q=sunset&tags=landscape&start_date=2024-01-01T00:00:00&end_date=2024-06-30T23:59:59&page=1&limit=20" \
  -H "Accept: application/json"
```

### 示例 5：无筛选条件（获取全部）

获取全部图片列表，按创建时间降序排列，默认第 1 页，每页 20 条。

```bash
curl -X GET "http://localhost:8000/images/" \
  -H "Accept: application/json"
```

---

## 响应结构说明

### 响应状态码

| 状态码 | 说明 |
|--------|------|
| 200 OK | 请求成功，返回搜索结果的 JSON 数据 |

### 响应体结构（SearchResponse）

| 字段 | 类型 | 说明 |
|------|------|------|
| `total` | integer | 符合条件的图片总数（不受分页影响） |
| `page` | integer | 当前页码 |
| `pages` | integer | 总页数（`ceil(total / limit)`，至少为 1） |
| `items` | ImageOut[] | 当前页的图片列表，按 `created_at` 降序排列 |

### 单条图片结构（ImageOut）

`items` 数组中的每个元素包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | integer | 图片唯一标识 ID |
| `title` | string \| null | 图片标题 |
| `image_url` | string | 原图 URL |
| `thumbnail_url` | string \| null | 缩略图 URL |
| `tags` | string[] | 标签数组，如 `["nature", "ai"]` |
| `created_at` | string (ISO 8601) | 创建时间，格式如 `2024-01-15T08:30:00` |

---

## 响应示例

### 成功响应（200 OK）

```json
{
  "total": 100,
  "page": 1,
  "pages": 5,
  "items": [
    {
      "id": 1,
      "title": "示例图片",
      "image_url": "https://example.com/images/1.jpg",
      "thumbnail_url": "https://example.com/thumbs/1.jpg",
      "tags": ["nature", "ai"],
      "created_at": "2024-01-15T08:30:00"
    },
    {
      "id": 2,
      "title": "山间日落",
      "image_url": "https://example.com/images/2.jpg",
      "thumbnail_url": "https://example.com/thumbs/2.jpg",
      "tags": ["nature", "landscape", "sunset"],
      "created_at": "2024-01-14T16:45:00"
    },
    {
      "id": 3,
      "title": null,
      "image_url": "https://example.com/images/3.jpg",
      "thumbnail_url": null,
      "tags": [],
      "created_at": "2024-01-13T10:00:00"
    }
  ]
}
```

### 空结果响应（200 OK）

当没有任何记录匹配筛选条件时，仍返回 200 状态码，`items` 为空数组：

```json
{
  "total": 0,
  "page": 1,
  "pages": 1,
  "items": []
}
```

---

## 错误说明

### 常见错误码

| 状态码 | 错误场景 | 说明 |
|--------|----------|------|
| **422 Unprocessable Entity** | 参数校验失败 | 请求参数类型不匹配或超出有效范围，如 `page=0`（最小值为 1）、`limit=200`（最大值为 100）、`start_date` 格式不正确等。FastAPI 会自动返回详细的校验错误信息。 |
| **500 Internal Server Error** | 服务器内部错误 | 数据库连接异常或其他服务端错误 |

### 422 错误响应示例

```json
{
  "detail": [
    {
      "type": "greater_than_equal",
      "loc": ["query", "page"],
      "msg": "Input should be greater than or equal to 1",
      "input": "0"
    }
  ]
}
```

---

## 前端使用建议

### 1. 分页处理

- **初始加载**：建议默认 `page=1`，`limit=20`。
- **翻页逻辑**：根据响应中的 `total` 和 `pages` 字段渲染分页组件。`pages = ceil(total / limit)`。
- **边界检查**：
  - 用户输入页码时，确保不小于 1。
  - 请求的页码超过 `pages` 时，接口会正常返回空 `items` 数组（`total` 仍为实际总数）。
- **页码同步**：URL 查询参数应与页面分页状态保持同步，便于分享和刷新。

### 2. 标签参数构建

- `tags` 参数需**多次**传递以实现"同时包含所有标签"的逻辑。例如同时筛选 "nature" 和 "ai"：

```javascript
// JavaScript / TypeScript 示例
const params = new URLSearchParams();
params.append('tags', 'nature');
params.append('tags', 'ai');
params.append('page', '1');

const url = `/images/?${params.toString()}`;
// 结果: /images/?tags=nature&tags=ai&page=1
```

```python
# Python requests 示例
import requests

response = requests.get(
    "http://localhost:8000/images/",
    params={
        "tags": ["nature", "ai"],  # 传入列表会自动展开为多个同名参数
        "page": 1,
    }
)
```

- 注意：`tags=nature,ai`（逗号分隔）**不会**被正确解析为两个独立标签，请务必使用多次传参的方式。

### 3. 日期参数格式

- 日期参数必须使用 **ISO 8601** 格式传递，如 `2024-01-15T08:30:00`。
- 建议始终包含时区信息或统一使用 UTC 时间，避免时区差异导致筛选结果不符合预期。

```javascript
// JavaScript 示例：将 Date 对象格式化为 ISO 字符串
const startDate = new Date('2024-01-01').toISOString(); // "2024-01-01T00:00:00.000Z"
const endDate = new Date('2024-12-31T23:59:59').toISOString();
```

### 4. 关键词搜索提示

- `q` 参数为模糊匹配，搜索范围包括图片标题（`title`）和生成提示词（`prompt`），不区分大小写。
- 如无需关键词搜索，省略 `q` 参数即可，不要传空字符串 `q=`（传空字符串会导致匹配空内容，通常返回空结果）。

### 5. 性能建议

- 建议根据实际 UI 设计合理设置 `limit` 值（如瀑布流可设 20-50，网格布局可设 12-24）。
- 避免 `limit=100` 频繁请求大量数据，影响加载速度和服务器性能。
- 标签和日期筛选能显著缩小搜索范围，建议优先让用户使用标签筛选，再辅以关键词搜索。

---

## 技术实现备注（供参考）

| 技术点 | 实现方式 |
|--------|----------|
| 关键词搜索 | PostgreSQL `ILIKE` 操作符，匹配 `title` OR `prompt` |
| 标签匹配 | PostgreSQL JSONB `@>` 操作符（数组包含），GIN 索引加速 |
| 日期筛选 | `created_at` 字段范围比较 |
| 分页 | SQL `LIMIT` / `OFFSET`，按 `created_at DESC` 排序 |
| 数据模型 | Pydantic v2 `BaseModel`，自动序列化和校验 |
