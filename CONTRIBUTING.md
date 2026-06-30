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
