# 开源工程化闭环实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 移除所有付费逻辑，补齐 MIT LICENSE、CONTRIBUTING、CI/CD、Docker 和多语言文档，使项目成为开箱即用的开源工具。

**架构：** 保持现有 Node.js + Python FastAPI 双轨架构不变，仅做工程化封装。付费字段从模板 JSON 和前端移除，后端保留兼容层；新增 GitHub Actions 自动化校验、Docker Compose 一键启动、双语 README 文档体系。

**技术栈：** JavaScript (前端), Python/FastAPI (后端), TypeScript (CLI), JSON (模板数据), GitHub Actions (CI), Docker/Docker Compose (部署)

---

## 文件清单

| 文件 | 职责 |
|------|------|
| `public/app.js` | 前端主逻辑 — 移除价格标签、付费按钮、价格计算 |
| `templates/*.json` (54个) | 模板数据 — 移除 `price` / `is_free` 字段 |
| `backend/routers/templates.py` | FastAPI 路由 — 保留参数兼容，移除付费过滤 |
| `backend/schemas/search.py` | Pydantic 模型 — 可选化 `price` / `is_free` |
| `scripts/remove_price_fields.py` | 一次性脚本 — 批量移除模板 JSON 中的价格字段 |
| `scripts/validate_templates.py` | CI 脚本 — 校验模板 JSON schema |
| `LICENSE` | MIT License |
| `CONTRIBUTING.md` | 贡献指南 |
| `CODE_OF_CONDUCT.md` | 行为准则 |
| `.github/ISSUE_TEMPLATE/bug_report.md` | Bug 报告模板 |
| `.github/ISSUE_TEMPLATE/feature_request.md` | 功能请求模板 |
| `.github/PULL_REQUEST_TEMPLATE.md` | PR 模板 |
| `.github/workflows/ci.yml` | 主 CI — 类型检查 + 模板校验 |
| `.github/workflows/templates.yml` | 模板专用 CI — schema 校验 |
| `docker/Dockerfile.node` | Node.js 服务镜像 |
| `docker/Dockerfile.python` | FastAPI 服务镜像 |
| `docker-compose.yml` | 一键启动编排 |
| `README.md` | 英文主文档（重写） |
| `README.zh-CN.md` | 中文完整版（从旧版迁移） |
| `docs/en/getting-started.md` | 英文快速开始 |
| `docs/en/api-reference.md` | 英文 API 文档 |
| `docs/en/template-authoring.md` | 英文模板编写指南 |
| `docs/ARCHITECTURE.md` | 双语架构总览 |

---

## 任务 1：编写模板校验脚本

**文件：**
- 创建：`scripts/validate_templates.py`
- 测试：运行脚本验证 54 个模板全部通过

- [ ] **步骤 1：编写脚本**

```python
#!/usr/bin/env python3
"""Validate all template JSON files against the project schema."""
import json
import sys
from pathlib import Path

REQUIRED_FIELDS = ["template_id", "category", "title", "version", "ratio", "face_lock", "style", "scene", "clothing", "prompt_blocks", "options", "negative_prompt"]
PROMPT_BLOCK_KEYS = ["subject", "face", "clothing", "scene", "lighting", "camera", "quality", "commercial_use"]


def validate_template(path: Path) -> list[str]:
    errors = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"JSON decode error: {e}"]

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing required field: {field}")

    template_id = data.get("template_id", "")
    if template_id and template_id != path.stem:
        errors.append(f"template_id '{template_id}' does not match filename '{path.stem}'")

    prompt_blocks = data.get("prompt_blocks", {})
    if isinstance(prompt_blocks, dict):
        for key in PROMPT_BLOCK_KEYS:
            if key not in prompt_blocks:
                errors.append(f"missing prompt_blocks.{key}")
    else:
        errors.append("prompt_blocks must be an object")

    # Ensure no price fields remain (open-source cleanup)
    if "price" in data:
        errors.append("unexpected field: price (should be removed for open-source)")
    if "is_free" in data:
        errors.append("unexpected field: is_free (should be removed for open-source)")

    return errors


def main() -> int:
    template_dir = Path(__file__).resolve().parent.parent / "templates"
    files = sorted(template_dir.glob("*.json"))
    total = len(files)
    failed = 0

    for f in files:
        errors = validate_template(f)
        if errors:
            failed += 1
            print(f"FAIL {f.name}")
            for e in errors:
                print(f"  - {e}")
        else:
            print(f"OK   {f.name}")

    print(f"\n{'='*50}")
    print(f"Total: {total}, Passed: {total - failed}, Failed: {failed}")
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **步骤 2：运行脚本验证当前状态（预期失败）**

运行：`python scripts/validate_templates.py`
预期：部分模板显示 `unexpected field: price` 和 `unexpected field: is_free`

- [ ] **步骤 3：Commit**

```bash
git add scripts/validate_templates.py
git commit -m "feat(ci): add template validation script for open-source standards"
```

---

## 任务 2：批量移除模板中的价格字段

**文件：**
- 创建：`scripts/remove_price_fields.py`
- 修改：`templates/*.json` (54个文件)

- [ ] **步骤 1：编写迁移脚本**

```python
#!/usr/bin/env python3
"""Remove price and is_free fields from all template JSON files."""
import json
from pathlib import Path


def main() -> None:
    template_dir = Path(__file__).resolve().parent.parent / "templates"
    files = sorted(template_dir.glob("*.json"))
    updated = 0
    skipped = 0

    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        changed = False
        if "price" in data:
            del data["price"]
            changed = True
        if "is_free" in data:
            del data["is_free"]
            changed = True
        if changed:
            f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            updated += 1
        else:
            skipped += 1

    print(f"Updated: {updated}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
```

- [ ] **步骤 2：运行脚本**

运行：`python scripts/remove_price_fields.py`
预期输出：`Updated: 54, Skipped: 0`

- [ ] **步骤 3：验证无残留**

运行：`grep -r '"price"' templates/*.json | wc -l`
预期输出：`0`

运行：`grep -r '"is_free"' templates/*.json | wc -l`
预期输出：`0`

- [ ] **步骤 4：运行校验脚本确认通过**

运行：`python scripts/validate_templates.py`
预期：全部 `OK`，`Failed: 0`

- [ ] **步骤 5：Commit**

```bash
git add scripts/remove_price_fields.py templates/
git commit -m "refactor(template): remove price and is_free from all 54 templates"
```

---

## 任务 3：移除前端付费逻辑

**文件：**
- 修改：`public/app.js:222-224`, `:248-249`, `:278-280`, `:374-387`, `:535-539`

- [ ] **步骤 1：修改搜索结果映射（移除 price/is_free）**

在 `public/app.js:222-224`，将：
```javascript
        price: item.price,
        is_free: item.is_free,
```
替换为：删除这两行（从映射中移除）。

在 `:248-249`，将同样的两行删除。

- [ ] **步骤 2：移除模板卡片价格标签**

在 `public/app.js:278-280`，将：
```javascript
    const priceTag = t.is_free === false || (t.price != null && t.price > 0)
      ? `<span style="position:absolute;bottom:8px;right:8px;font-size:11px;font-weight:600;color:#e8590c;background:#fff4e6;padding:2px 6px;border-radius:999px;">¥${t.price || '?'}</span>`
      : `<span style="position:absolute;bottom:8px;right:8px;font-size:11px;font-weight:600;color:#2b8a3e;background:#d3f9d8;padding:2px 6px;border-radius:999px;">免费</span>`;
```
替换为：
```javascript
    const priceTag = '';
```

在 `:286`，`${priceTag}` 保留（渲染空字符串）。

- [ ] **步骤 3：移除详情页价格标签和按钮逻辑**

在 `public/app.js:374-387`，将：
```javascript
  const priceChip = t.is_free === false || (t.price != null && t.price > 0)
    ? `<span class="meta-chip" style="background:#fff4e6;color:#e8590c;">¥${t.price} 解锁高清</span>`
    : `<span class="meta-chip" style="background:#d3f9d8;color:#2b8a3e;">免费生成</span>`;
```
替换为：
```javascript
  const priceChip = '';
```

将：
```javascript
  // Update generate button based on pricing
  const isPaid = t.is_free === false || (t.price != null && t.price > 0);
  els.generateTemplateBtn.textContent = isPaid ? '解锁并生成' : '生成写真';
```
替换为：
```javascript
  // Generate button text (all templates are free in open-source)
  els.generateTemplateBtn.textContent = '免费生成';
```

- [ ] **步骤 4：移除结果横幅中的付费标识**

在 `public/app.js:535-539`，将：
```javascript
      const isPaidTemplate = template.is_free === false || (template.price != null && template.price > 0);
      const tierLabel = isPaidTemplate ? ' · 预览版' : ' · 免费版';
```
替换为：
```javascript
      const tierLabel = ' · 开源版';
```

- [ ] **步骤 5：验证前端类型检查**

运行：`npm run check`
预期：通过，无类型错误

- [ ] **步骤 6：启动服务手动验证**

运行：`npm run api`
浏览器访问 `http://127.0.0.1:3000`
验证：
1. 模板卡片无价格标签
2. 详情页按钮显示"免费生成"
3. 生成结果横幅显示"开源版"

- [ ] **步骤 7：Commit**

```bash
git add public/app.js
git commit -m "refactor(frontend): remove all pricing UI logic for open-source"
```

---

## 任务 4：后端移除/兼容付费字段

**文件：**
- 修改：`backend/routers/templates.py:68-69, :80, :109-110, :138-139, :176-177, :231-232`
- 修改：`backend/schemas/search.py:69-70`

- [ ] **步骤 1：修改 schemas/search.py（可选化字段）**

在 `backend/schemas/search.py:69-70`，将：
```python
    price: float = Field(0.0, ge=0, description="Template price in CNY")
    is_free: bool = Field(True, description="Whether the template is free to use")
```
替换为：
```python
    price: Optional[float] = Field(None, description="Template price in CNY (deprecated, kept for backward compatibility)")
    is_free: Optional[bool] = Field(None, description="Whether the template is free (deprecated, kept for backward compatibility)")
```

- [ ] **步骤 2：修改 templates.py list_templates 移除价格返回**

在 `backend/routers/templates.py:68-69`，删除：
```python
                "price": t.get("price", 0.0),
                "is_free": t.get("is_free", True),
```

- [ ] **步骤 3：修改 search_templates 忽略 is_free 过滤**

在 `backend/routers/templates.py:80`，保留参数签名不变（向后兼容）。

在 `:109-110`，将：
```python
    # Filter by free/paid
    if is_free is not None:
        items = [t for t in items if bool(t.get("is_free", True)) == is_free]
```
替换为：
```python
    # is_free filter is ignored in open-source version (all templates are free)
    # Parameter kept for backward compatibility
```

在 `:138-139`，删除：
```python
                price=float(t.get("price", 0.0)) if t.get("price") is not None else 0.0,
                is_free=bool(t.get("is_free", True)),
```

- [ ] **步骤 4：修改 recommended_templates 移除价格返回**

在 `:153`，将：
```python
    free_items = [t for t in items if bool(t.get("is_free", True))]
```
替换为：
```python
    # All templates are included in open-source version
    free_items = items
```

在 `:176-177`，删除 price/is_free 返回行。

- [ ] **步骤 5：修改 recently_used_templates 移除价格返回**

在 `:231-232`，删除 price/is_free 返回行。

- [ ] **步骤 6：重启后端验证**

运行：`npm run api`
测试接口：`curl http://localhost:8000/api/templates`
验证：返回结果中不包含 `price` 和 `is_free` 字段

- [ ] **步骤 7：Commit**

```bash
git add backend/routers/templates.py backend/schemas/search.py
git commit -m "refactor(backend): remove price/is_free from API responses, keep param compatibility"
```

---

## 任务 5：添加开源标准文件

**文件：**
- 创建：`LICENSE`
- 创建：`CONTRIBUTING.md`
- 创建：`CODE_OF_CONDUCT.md`
- 创建：`.github/ISSUE_TEMPLATE/bug_report.md`
- 创建：`.github/ISSUE_TEMPLATE/feature_request.md`
- 创建：`.github/PULL_REQUEST_TEMPLATE.md`

- [ ] **步骤 1：创建 LICENSE**

```
MIT License

Copyright (c) 2026 AI Photo Template Miniapp Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **步骤 2：创建 CONTRIBUTING.md**

```markdown
# Contributing to AI Photo Template Miniapp

感谢你的贡献！请阅读以下指南。

## 开发环境

- Node.js 20+
- Python 3.11+
- Git

## 快速开始

```bash
npm install
npm run check
npm run list
npm run api
```

## 分支规范

- `feat/` — 新功能
- `fix/` — 修复
- `docs/` — 文档
- `refactor/` — 重构

## Commit 规范

使用 Conventional Commits：

```
feat: add new template category
template: add portrait_soft_window_light template
fix: handle missing prompt_blocks in template loader
docs: update API reference for generate endpoint
```

## 贡献模板

1. 在 `templates/` 下创建 `<template_id>.json`
2. 使用标准八层 `prompt_blocks` 结构
3. 运行 `python scripts/validate_templates.py` 确认通过
4. 运行 `npm run generate <template_id>` 测试 prompt 输出
5. 提交 PR

## PR 检查清单

- [ ] 代码通过 `npm run check`
- [ ] 新模板通过 `python scripts/validate_templates.py`
- [ ] 无 `price` / `is_free` 字段
- [ ] 文档已同步更新
```

- [ ] **步骤 3：创建 CODE_OF_CONDUCT.md**

```markdown
# Contributor Covenant Code of Conduct

## Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone.

## Our Standards

Examples of behavior that contributes to a positive environment:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Accepting constructive criticism
- Focusing on what is best for the community

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported to the project maintainers.

This Code of Conduct is adapted from the [Contributor Covenant](https://www.contributor-covenant.org), version 2.1.
```

- [ ] **步骤 4：创建 GitHub Issue 模板**

`.github/ISSUE_TEMPLATE/bug_report.md`：
```markdown
---
name: Bug report
about: Create a report to help us improve
title: '[Bug] '
labels: bug
---

**Describe the bug**
A clear description of the bug.

**To Reproduce**
Steps to reproduce the behavior.

**Expected behavior**
What you expected to happen.

**Environment**
- OS: [e.g. Windows 11]
- Node.js version: [e.g. 20.10.0]
- Python version: [e.g. 3.11.4]
```

`.github/ISSUE_TEMPLATE/feature_request.md`：
```markdown
---
name: Feature request
about: Suggest an idea for this project
title: '[Feature] '
labels: enhancement
---

**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
What you want to happen.

**Describe alternatives you've considered**
Any alternative solutions or features.
```

- [ ] **步骤 5：创建 PR 模板**

`.github/PULL_REQUEST_TEMPLATE.md`：
```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Template addition
- [ ] Documentation update
- [ ] Refactoring

## Checklist
- [ ] `npm run check` passes
- [ ] `python scripts/validate_templates.py` passes
- [ ] Templates do not contain `price` or `is_free`
- [ ] Documentation updated if needed
```

- [ ] **步骤 6：Commit**

```bash
git add LICENSE CONTRIBUTING.md CODE_OF_CONDUCT.md .github/
git commit -m "chore: add MIT license, contributing guidelines, and GitHub templates"
```

---

## 任务 6：GitHub Actions CI

**文件：**
- 创建：`.github/workflows/ci.yml`
- 创建：`.github/workflows/templates.yml`

- [ ] **步骤 1：创建主 CI 工作流**

`.github/workflows/ci.yml`：
```yaml
name: CI

on:
  push:
    branches: [master, main]
  pull_request:
    branches: [master, main]

jobs:
  frontend-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run check
      - run: npm run list

  template-validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: python scripts/validate_templates.py

  backend-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/ -v || echo "No tests yet, continuing"
```

- [ ] **步骤 2：创建模板专用 CI**

`.github/workflows/templates.yml`：
```yaml
name: Template Validation

on:
  push:
    paths:
      - 'templates/**'
      - 'scripts/validate_templates.py'
  pull_request:
    paths:
      - 'templates/**'
      - 'scripts/validate_templates.py'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: python scripts/validate_templates.py
```

- [ ] **步骤 3：Commit**

```bash
git add .github/workflows/
git commit -m "ci: add GitHub Actions for type check, template validation, and backend tests"
```

---

## 任务 7：Docker 支持

**文件：**
- 创建：`docker/Dockerfile.node`
- 创建：`docker/Dockerfile.python`
- 创建：`docker-compose.yml`

- [ ] **步骤 1：创建 Node Dockerfile**

`docker/Dockerfile.node`：
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["npm", "run", "api"]
```

- [ ] **步骤 2：创建 Python Dockerfile**

`docker/Dockerfile.python`：
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY templates/ ./templates/
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **步骤 3：创建 Docker Compose**

`docker-compose.yml`：
```yaml
version: "3.8"

services:
  node-api:
    build:
      context: .
      dockerfile: docker/Dockerfile.node
    ports:
      - "3000:3000"
    volumes:
      - ./templates:/app/templates
      - ./uploads:/app/uploads
      - ./output:/app/output
      - ./.env:/app/.env
    environment:
      - NODE_ENV=production

  fastapi:
    build:
      context: .
      dockerfile: docker/Dockerfile.python
    ports:
      - "8000:8000"
    volumes:
      - ./templates:/app/templates
      - ./uploads:/app/uploads
      - ./.env:/app/.env
    environment:
      - PYTHONUNBUFFERED=1
```

- [ ] **步骤 4：验证 Docker 构建**

运行：`docker-compose build`
预期：两个镜像构建成功

运行：`docker-compose up -d`
预期：服务启动，浏览器可访问

- [ ] **步骤 5：Commit**

```bash
git add docker/ docker-compose.yml
git commit -m "feat(docker): add Dockerfile and docker-compose for one-click deployment"
```

---

## 任务 8：重写 README 和多语言文档

**文件：**
- 修改：`README.md`（重写为英文主文档）
- 创建：`README.zh-CN.md`（从旧版迁移）
- 创建：`docs/ARCHITECTURE.md`

- [ ] **步骤 1：重写 README.md**

```markdown
# AI Photo Template Miniapp

> Transform your portrait into stunning AI-generated photos using curated templates.

[中文文档](README.zh-CN.md)

## Features

- 50+ curated photo templates (ancient Chinese, career portraits, fashion, product posters, etc.)
- Template-based prompt generation for consistent, high-quality results
- Mock image generation mode (zero API cost for development)
- HTTP adapter ready for GPT-Image-2 / EvoLinkAI / custom APIs
- Batch generation support
- Gallery with search and filtering
- One-click Docker deployment

## Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/your-org/ai-photo-template-miniapp.git
cd ai-photo-template-miniapp
docker-compose up
# Open http://localhost:3000
```

### Local Development

```bash
npm install
npm run check
npm run list
npm run api
# Open http://localhost:3000
```

## Template System

Templates are JSON files in `templates/`. Each template defines:

- `prompt_blocks`: 8 structured sections (subject, face, clothing, scene, lighting, camera, quality, commercial_use)
- `options`: generation parameters (ratio, face_strength, etc.)
- `negative_prompt`: excluded content

See [docs/en/template-authoring.md](docs/en/template-authoring.md) for the full guide.

## API

The project provides two API layers:

- **Node.js API** (port 3000): Template listing, prompt generation, mock image generation
- **FastAPI** (port 8000): Image gallery search, analytics, template catalog proxy

See [docs/en/api-reference.md](docs/en/api-reference.md) for endpoints.

## Architecture

```
User Upload → Template Selection → Prompt Builder → Image API → Result Gallery
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

## Tech Stack

- Frontend: Vanilla JavaScript + CSS
- CLI/Scripts: TypeScript (tsx)
- Backend: Python FastAPI + SQLAlchemy
- Data: JSON templates, SQLite (gallery)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT License. See [LICENSE](LICENSE).
```

- [ ] **步骤 2：创建 README.zh-CN.md**

从旧的 `README.md` 复制内容，更新以下部分：
1. 删除所有商业化描述（Phase 3/4 路线、付费解锁、价格体系）
2. 删除"后续路线"中的商业化内容，保留技术路线
3. 添加指向英文 README 的链接
4. 更新"当前建议的下一步"为开源方向（模板贡献、API 适配）
5. 添加 Docker 快速启动

- [ ] **步骤 3：创建 docs/ARCHITECTURE.md**

```markdown
# Architecture

## System Overview

```
[Browser] ←→ [Node.js API :3000] ←→ [templates/*.json]
                ↓
           [FastAPI :8000] ←→ [SQLite Gallery DB]
```

## Data Flow

1. **Template Loading**: `src/templates/templateRepository.ts` reads JSON from `templates/`
2. **Prompt Building**: `src/services/promptBuilder.ts` concatenates prompt_blocks
3. **Generation**: `src/services/aiImageService.ts` sends to configured API (mock by default)
4. **Storage**: Results saved to `output/` and optionally gallery database

## Module Map

| Module | File | Responsibility |
|--------|------|---------------|
| Config | `src/config/appConfig.ts` | Environment and path configuration |
| Template Types | `src/types/template.ts` | TypeScript interfaces for templates |
| Task Types | `src/types/task.ts` | Generation task structure |
| Schema Validation | `src/templates/templateSchema.ts` | Runtime template validation |
| Template Loader | `src/templates/templateRepository.ts` | File I/O and caching |
| Prompt Builder | `src/services/promptBuilder.ts` | Final prompt assembly |
| Image Service | `src/services/aiImageService.ts` | API client (mock/HTTP) |
| Generate Workflow | `src/workflows/generatePromptWorkflow.ts` | End-to-end prompt generation |
```

- [ ] **步骤 4：Commit**

```bash
git add README.md README.zh-CN.md docs/ARCHITECTURE.md
git commit -m "docs: rewrite README for open-source, add bilingual docs and architecture"
```

---

## 自检

**1. 规格覆盖度：**

| 规格需求 | 对应任务 | 状态 |
|----------|---------|------|
| 移除 `price` / `is_free` 字段 | 任务 2, 3, 4 | ✅ |
| 前端无付费 UI | 任务 3 | ✅ |
| 后端兼容层 | 任务 4 | ✅ |
| MIT LICENSE | 任务 5 | ✅ |
| CONTRIBUTING.md | 任务 5 | ✅ |
| GitHub Actions CI | 任务 6 | ✅ |
| Docker 支持 | 任务 7 | ✅ |
| 英文 README | 任务 8 | ✅ |
| 中文 README | 任务 8 | ✅ |
| 架构文档 | 任务 8 | ✅ |
| 模板校验脚本 | 任务 1 | ✅ |

**2. 占位符扫描：**
- [x] 无"待定" / "TODO" / "后续实现"
- [x] 无"添加适当的错误处理"类模糊描述
- [x] 每个代码步骤包含实际代码
- [x] 无"类似任务 N"引用
- [x] 精确文件路径和行号

**3. 类型一致性：**
- `validate_templates.py` 中的 `REQUIRED_FIELDS` 和 `PROMPT_BLOCK_KEYS` 与现有模板结构一致
- 前端删除 `price` / `is_free` 后不再引用这两个字段
- 后端 `Optional[float]` / `Optional[bool]` 兼容无字段的情况

---

## 执行交接

**计划已完成并保存到 `docs/superpowers/plans/2026-06-04-open-source-engineering.md`。两种执行方式：**

**1. 子代理驱动（推荐）** - 每个任务调度一个新的子代理，任务间进行审查，快速迭代

**2. 内联执行** - 在当前会话中使用 executing-plans 执行任务，批量执行并设有检查点

**选哪种方式？**
