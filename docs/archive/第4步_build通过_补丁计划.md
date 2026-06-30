# 补丁计划 — 第 4 步：build 通过

## 1. 背景与目标

当前项目缺少 `build` 和 `typecheck` npm 脚本，导致常用命令无法直接运行。虽然 `npx tsc` 和 `npm run check` 可以正常工作，但标准命令缺失影响团队协作和 CI/CD 集成。

**目标**：
1. 添加标准 `build` 脚本（`tsc`）到 `package.json`
2. 添加标准 `typecheck` 脚本（`tsc --noEmit`）到 `package.json`
3. 验证 `npm run build` 和 `npm run typecheck` 都能正常通过

## 2. 修改范围

| 文件路径 | 操作 | 影响面 |
|----------|:----:|--------|
| `package.json` | 修改 | npm scripts 配置 |

**本轮修改文件数：1 个**，符合工程纪律。

## 3. 不会修改的内容

`.env` / COS / 真 API / 依赖 / 删除 / 格式化 / 超过 3 个文件

## 4. 具体变更内容

### 文件 A：`package.json`

**变更前：**
```json
"scripts": {
  "dev": "tsx scripts/generate_prompt.ts",
  "generate": "tsx scripts/generate_prompt.ts",
  "image": "tsx scripts/run_image_task.ts",
  "api": "tsx scripts/start_api.ts",
  "list": "tsx scripts/list_templates.ts",
  "smoke": "powershell -ExecutionPolicy Bypass -File scripts/smoke_test.ps1",
  "catalog": "powershell -ExecutionPolicy Bypass -File scripts/generate_template_catalog.ps1",
  "check": "tsc --noEmit"
}
```

**变更后：**
```json
"scripts": {
  "dev": "tsx scripts/generate_prompt.ts",
  "generate": "tsx scripts/generate_prompt.ts",
  "image": "tsx scripts/run_image_task.ts",
  "api": "tsx scripts/start_api.ts",
  "list": "tsx scripts/list_templates.ts",
  "smoke": "powershell -ExecutionPolicy Bypass -File scripts/smoke_test.ps1",
  "catalog": "powershell -ExecutionPolicy Bypass -File scripts/generate_template_catalog.ps1",
  "check": "tsc --noEmit",
  "typecheck": "tsc --noEmit",
  "build": "tsc"
}
```

## 5. 验收标准

- [ ] `npm run typecheck` 执行成功（等价于 `npm run check`）
- [ ] `npm run build` 执行成功（`tsc` 编译通过，生成 `.js` 文件）
- [ ] 编译后项目结构正常，无报错
- [ ] 原有 `npm run check` 不受影响

## 6. 验收命令

```bash
# 1. 验证 typecheck
npm run typecheck

# 2. 验证 build
npm run build

# 3. 验证原有 check 不受影响
npm run check
```

## 7. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|:----:|:----:|----------|
| `tsc` 编译生成 `.js` 文件污染源码目录 | 低 | 低 | 已验证 `npx tsc` 通过，且 `tsconfig.json` 中 `outDir` 若未配置，文件会与 `.ts` 同目录。需确认是否接受。 |

**补充说明**：若 `tsconfig.json` 未配置 `outDir`，`npm run build` 会在 `src/` 下生成 `.js` 文件。这是预期行为，不影响运行时（`tsx` 直接执行 `.ts`）。如需隔离，可配置 `outDir: "dist"`。

## 8. 回滚方案

```bash
git checkout -- package.json
# 如已生成 .js 文件，清理：
find src -name "*.js" -delete
```

## 9. 确认签字

- [ ] 计划已审阅
- [ ] 修改范围确认
- [ ] 可以执行
