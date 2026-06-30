# AI Photo Template Miniapp — 标准操作流程 (SOP)

> 版本：v2.0 | 更新：2026-05-28

## 项目概述

AI 写真模板小程序，包含 AI Fashion Director System v2.0 风格引擎。
基于 TypeScript + Python FastAPI，部署于腾讯云。

## 目录结构

```
ai-photo-template-miniapp/
├── admin/                    # 管理文档
│   ├── SOP.md               # 本文件
│   └── checkpoints/         # QA 抽检记录
├── references/
│   └── style-library/       # AI Fashion Director System v2.0
│       ├── model-base/      # ModelDNA — 5 种体型
│       ├── hairstyle/       # HairDNA — 12 种发型 + 3 矩阵
│       ├── motions/         # MotionDNA — 22 种动作 + 5 组合
│       ├── clothing/        # OutfitDNA — 6 品类 + 语义表
│       ├── materials/       # MaterialDNA — 6 种材质
│       ├── camera/          # CameraDNA — 6 镜头 + 4 品牌构图
│       ├── lighting/        # LightDNA — 8 种布光
│       ├── backgrounds/     # SceneDNA — 20 个场景
│       ├── mood/            # MoodDNA — 8 种情绪 + 3 矩阵
│       ├── brand/           # BrandDNA — 7 品牌语言
│       ├── cinematic-frame/ # CinematicFrame — 4 种电影构图
│       ├── pose-skeleton/   # PoseSkeleton — JSON Schema
│       └── prompt-forge/    # PromptForge — 拼接引擎
├── templates/
│   └── series/
│       └── siuf-2026/       # SIUF 2026 系列 25 个 Look
├── src/                      # TypeScript 前端
├── backend/                  # Python FastAPI 后端
├── scripts/ops/              # 运维脚本
└── docs/                     # 文档
```

## 文件命名规范

- 模块文件：`{模块名}-{版本}.md`（英文小写，连字符分隔）
- Look 文件：`{编号}-{英文名}.md`（两位数编号）
- 矩阵文件：`{主体}-×-{维度}-matrix.md`

## 安全规则

- `.env` 文件禁止提交
- API Key 只存在 `.env` 或环境变量中
- 敏感配置不进入同步脚本

## 同步流程

1. 本地修改完成后执行 `scripts/ops/sync-baidudisk.ps1`
2. 同步范围：`references/`、`templates/`、`admin/`、`docs/`
3. 排除：`node_modules`、`.git`、`__pycache__`、`.env`、`*.log`
4. 同步日志：`logs/sync-*.log`

## QA 抽检流程

1. 每批次完成后随机抽取 3-5 个 Look
2. 检查十层完整性、语言升级、模块一致性、负面约束
3. 修复问题记录到 `admin/checkpoints/`
4. 修复后再次抽检验证

## 扩展指南

### 新增 Look
1. 确定 Model + Hair + Motion + Outfit + Scene + Mood 组合
2. 参考 `prompt-forge/prompt-forge-engine.md` 的拼接规则
3. 按十层结构编写 Prompt
4. 使用 `clothing/outfit-semantic-table.md` 替换禁用词

### 新增模块
1. 在 `style-library/` 下创建新目录
2. 按现有模块格式编写数据库文件
3. 创建对应的适配矩阵
4. 更新 `style-library/README.md` 和本 SOP

### 代码对接
- `src/services/promptBuilder.ts` — 前端 Prompt 构建
- `backend/api/ai_lab_routes.py` — AI 实验室 API
- 模块 JSON → PromptForge 拼接 → 十层 Prompt 输出
