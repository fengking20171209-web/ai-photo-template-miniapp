# 开源工程化闭环 — 设计规格

> **目标：** 将现有项目从"商业化 MVP"改造为"开箱即用的开源 AI 写真模板工具"，移除所有付费逻辑，补齐开源标准文件、CI/CD、Docker 和多语言文档。

---

## 1. 范围边界

| 包含 | 排除 |
|------|------|
| 移除 `price`/`is_free` 字段及相关 UI 逻辑 | 新增生图 API 适配（Phase 2） |
| 添加 MIT LICENSE、CONTRIBUTING.md、CODE_OF_CONDUCT.md | 抖音小程序（Phase 3） |
| GitHub Actions CI（类型检查 + 模板校验） | 模板编辑器（方案 B） |
| Docker + docker-compose 一键部署 | 社区模板市场（方案 B） |
| 英文 README + 多语言文档 | 支付/会员体系 |

---

## 2. 付费代码移除

### 2.1 前端 `public/app.js`

- `renderTemplateCard`：移除价格标签显示逻辑，卡片不再展示 `"免费"` 或 `"¥X.X"`
- `renderTemplateDetail`：按钮文字统一为 `"免费生成"`，移除 `"解锁并生成"`
- `renderBatchBar`：移除 `totalPrice` / `paidCount` 计算，batch bar 仅显示已选择数量
- `generateFromTemplate`：移除 `is_free === false` 时的付费拦截提示，所有模板直接调用生成
- 全局搜索 `price`、`is_free`、`解锁`、`付费` 关键字，确保无残留

### 2.2 模板 JSON 数据

- 54 个模板文件统一移除 `price` 和 `is_free` 字段
- 保留所有业务字段：`template_id`、`category`、`title`、`version`、`ratio`、`face_lock`、`style`、`scene`、`clothing`、`prompt_blocks`、`options`、`negative_prompt`、`tags`
- 使用一次性脚本 `scripts/remove_price_fields.py` 批量处理

### 2.3 后端兼容层

- `backend/routers/templates.py`：保留 `is_free` 查询参数但忽略其过滤效果（向后兼容），返回全部模板
- `backend/schemas/`：Pydantic 模型中 `price` / `is_free` 设为 `Optional` 并默认值，避免旧调用报错

---

## 3. 开源标准文件

### 3.1 LICENSE
- MIT License
- Copyright (c) 2026 [项目维护者名称]
- 允许商业使用、修改、分发、私有使用

### 3.2 CONTRIBUTING.md
- 开发环境搭建（Node.js 20+, Python 3.11+）
- 分支规范：`feat/`、`fix/`、`docs/`、`refactor/`
- PR 模板检查清单
- 代码提交规范（Conventional Commits）
- 如何贡献模板 JSON

### 3.3 CODE_OF_CONDUCT.md
- Contributor Covenant 2.1 标准版本

### 3.4 GitHub 模板
- Issue 模板：Bug 报告、功能请求
- PR 模板：变更说明、测试步骤、检查清单

---

## 4. CI/CD（GitHub Actions）

### 4.1 `.github/workflows/ci.yml` — 主检查流

**触发：** `push` / `pull_request` 到 `master`

**任务矩阵：**
| Job | 运行器 | 步骤 |
|-----|--------|------|
| `frontend-check` | ubuntu-latest | `npm ci` → `npm run check` → `npm run list` |
| `template-validate` | ubuntu-latest | Python 脚本校验 54 个 JSON 的 schema、必填字段、template_id 唯一性 |
| `backend-check` | ubuntu-latest | `pip install -r backend/requirements.txt` → `pytest backend/tests/`（如有测试） |

### 4.2 `.github/workflows/templates.yml` — 模板变更专用

**触发：** `templates/**` 文件变更

**步骤：**
1. 校验所有模板 JSON 语法正确性
2. 检查 `template_id` 与文件名一致性
3. 检查必填字段：`template_id`、`category`、`title`、`version`、`prompt_blocks`
4. 检查 `prompt_blocks` 八层结构完整性

---

## 5. Docker 支持

### 5.1 镜像策略

| 服务 | 镜像 | 说明 |
|------|------|------|
| Node API | `node:20-alpine` | 前端静态文件 + Express API |
| FastAPI | `python:3.11-slim` | 图库搜索后端 |
| (可选) Nginx | `nginx:alpine` | 生产环境反向代理 |

### 5.2 本地开发启动

```bash
docker-compose up
# → Node API  http://localhost:3000
# → FastAPI   http://localhost:8000
```

### 5.3 卷挂载

- `./templates:/app/templates` — 模板热更新无需重建镜像
- `./uploads:/app/uploads` — 用户上传持久化
- `./output:/app/output` — 生成结果持久化
- `./.env:/app/.env` — 配置外置

---

## 6. 文档国际化

### 6.1 文档结构

```
docs/
├── en/
│   ├── getting-started.md      # 安装与运行
│   ├── api-reference.md        # API 文档（从 docs/api/ 合并）
│   ├── template-authoring.md   # 模板编写指南
│   └── architecture.md         # 架构说明
├── zh-CN/
│   ├── getting-started.md
│   ├── api-reference.md
│   ├── template-authoring.md
│   └── architecture.md
└── ARCHITECTURE.md             # 双语架构总览（图形 + 说明）
```

### 6.2 README 重写策略

**`README.md`（英文主文档）：**
- Hero 段落：一句话介绍 + 核心功能 bullet
- Screenshot/GIF 占位
- Quick Start（Docker 方式优先，3 步启动）
- Features 列表
- Tech Stack
- Contributing 链接
- License

**`README.zh-CN.md`（中文完整版）：**
- 从现有 README.md 迁移全部内容
- 更新去除商业化描述
- 添加指向英文 README 的链接

---

## 7. 自检清单

- [x] **占位符扫描：** 无"TODO"、"待定"、"后续实现"
- [x] **内部一致性：** 模板 JSON 移除字段后，前端/后端消费逻辑同步调整
- [x] **范围检查：** 纯工程化，不涉及新功能开发
- [x] **模糊性检查：** Docker 端口、文件路径已明确

---

## 8. 后续步骤

此规格经用户批准后，调用 `writing-plans` 技能生成详细实现计划。
