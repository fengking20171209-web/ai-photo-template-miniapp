# 补丁计划 — 第 5 步：提交一次 Git

## 1. 背景与目标

前 4 步完成后，项目产生大量改动（新增模板、修复硬编码、前端优化、脚本补充）。本步骤目标是**将本轮所有成果保存到 Git**，形成可回溯的版本节点。

**目标**：
1. 整理本轮所有改动文件
2. 编写规范的 Git 提交信息
3. 执行 `git commit`，形成版本快照

## 2. 修改范围

| 操作 | 影响面 |
|------|--------|
| `git add` + `git commit` | Git 版本控制 |

**本轮不修改任何工作区文件**，仅执行版本控制操作。

## 3. 不会修改的内容

工作区文件零变动，仅提交已完成的改动。

## 4. 具体步骤

### 步骤 1：确认工作区状态

```bash
git status
```

确认所有改动文件均已纳入，无遗漏、无意外文件。

### 步骤 2：暂存所有改动

```bash
git add .
```

或按需分批次 `git add`（如代码、模板、文档分开提交）。

### 步骤 3：编写提交信息

**提交信息格式（Conventional Commits）：**

```
feat(template): expand categories from 6 to 10, add 11 new templates

- Fix category hardcoding in template.ts and templateSchema.ts
- Add 11 new templates across 3 directions (product/portrait/ancient)
- Migrate 30 legacy templates to standard 8-field structure
- Fix concept_neo-chinese-bodycon.json data quality
- Add frontend category filter and mock generation闭环
- Fix SenseNova SDK auth (access_key_id → secret_access_key)
- Add sensetime → http mapping in appConfig.ts
- Add build/typecheck npm scripts
- Generate project documentation (discipline, templates, risks)

Closes: round-1 template expansion
```

### 步骤 4：执行提交

```bash
git commit -m "feat(template): expand categories from 6 to 10, add 11 new templates"
```

### 步骤 5：验证提交

```bash
git log --oneline -1
```

确认提交成功，信息正确。

## 5. 验收标准

- [ ] `git status` 显示工作区干净（无未跟踪/未提交改动）
- [ ] `git log` 显示提交成功
- [ ] 提交信息包含本轮核心改动摘要
- [ ] 提交后 `npm run check` 仍通过（验证提交完整性）

## 6. 验收命令

```bash
git status
git log --oneline -5
npm run check
```

## 7. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|:----:|:----:|----------|
| 意外提交敏感文件（如 `.env`） | 低 | 高 | 提交前检查 `git status`，确保 `.env` 在 `.gitignore` 中 |
| 提交信息遗漏重要改动 | 中 | 低 | 对照本轮文件清单逐项核对 |

## 8. 回滚方案

如需撤销提交：

```bash
# 保留改动，撤销提交
git reset --soft HEAD~1

# 完全撤销（慎用）
# git reset --hard HEAD~1
```

## 9. 确认签字

- [ ] 提交前检查清单已完成
- [ ] 提交信息已审阅
- [ ] 可以执行
