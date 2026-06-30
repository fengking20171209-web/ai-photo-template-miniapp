# AI Fashion Director System v2.0 — 风格库

> 版本：v2.1 | 更新：2026-05-28

## 模块总览

| # | 模块 | 目录 | 文件数 | 说明 |
|---|------|------|--------|------|
| 01 | ModelDNA | model-base/ | 5 | 5 种体型档案 |
| 02 | HairDNA | hairstyle/ | 4 | 12 种发型 + 3 个适配矩阵 |
| 03 | MotionDNA | motions/ | 4 | 22 种动作 + 5 个组合动作 + 2 个矩阵 |
| 04 | OutfitDNA | clothing/ | 8 | 6 大品类 + 肚兜品类 + 裙装品类 + 语义表 + 面料矩阵 + 搭配指南 + 专题研究 |
| 05 | MaterialDNA | materials/ | 1 | 6 种布料材质 |
| 06 | CameraDNA | camera/ | 1 | 6 种镜头 + 4 种品牌构图 |
| 07 | LightDNA | lighting/ | 1 | 8 种布光方案 |
| 08 | SceneDNA | backgrounds/ | 1 | 20 个场景 + 情绪标签 |
| 09 | MoodDNA | mood/ | 1 | 8 种情绪 + 3 个矩阵 |
| 10 | BrandDNA | brand/ | 1 | 7 个品牌摄影语言 |
| 11 | CinematicFrame | cinematic-frame/ | 1 | 4 种电影构图 |
| 12 | PoseSkeleton | pose-skeleton/ | 1 | JSON Schema + 5 个标准骨架 |
| 13 | PromptForge | prompt-forge/ | 1 | 拼接引擎规格 |

**总计**：13 个模块，32 个数据库文件

## OutfitDNA 详细文件

```
clothing/
├── clothing-system.md           # 6 大品类（蕾丝/丝绸/泳装/运动/赛博/裸感）
├── dudou-category.md            # 品类7：中式肚兜（5 子品类）
├── dudou-lower-body-v2.md       # 肚兜 v2.0 新中式下装体系
├── skirt-category.md            # 品类8：包臀裙体系（12 子品类）
├── skirt-database.md            # 裙装专题：8 种结构 + 10 种面料 + 编码体系
├── skirt-pairing-guide.md       # 裙装完整搭配矩阵
├── skirt-comparison-tests.md    # 模糊 vs 精确描述对比测试
├── outfit-semantic-table.md     # 服装语义替代词表
├── outfit-fabric-matrix.md      # 服装 × 面料矩阵
└── bodycon-skirt-deep-dive.md   # 包臀裙专题深度研究
```

## 交叉适配矩阵

- `hairstyle/hair-outfit-matrix.md` — 发型 × 服装
- `hairstyle/hair-mood-matrix.md` — 发型 × 情绪
- `hairstyle/hair-camera-matrix.md` — 发型 × 镜头
- `motions/motion-mood-matrix.md` — 动作 × 情绪
- `motions/motion-outfit-matrix.md` — 动作 × 服装
- `clothing/outfit-fabric-matrix.md` — 服装 × 面料
- `clothing/skirt-pairing-guide.md` — 裙装搭配指南
- `mood/mood-system.md` — 情绪 × 服装/灯光/姿势矩阵

## 概念系列

- `templates/series/concept/neo-chinese-bodycon.md` — 新中式包臀裙概念（3 个 Look）

## SIUF 2026 系列

25 个 Look 已完成，详见 `templates/series/siuf-2026-overview.md`

## 肚兜系列

5 个 v1.0 Look + 3 个 v2.0 优化 Look，详见 `templates/series/dudou-modern/README.md`

## BodyconDressDNA 模块（新增）

`
bodycon-dress/
├── README.md                    # 模块总览 + 4个测试Prompt
├── silhouette/bodycon-silhouettes.md   # 5种核心轮廓
├── fabric/bodycon-fabrics.md           # 7种推荐面料
├── styling/bodycon-styling.md          # 丝袜·鞋子·外套·配饰
├── motion/bodycon-motions.md           # 5个专用动作
├── camera/bodycon-cameras.md           # 6种推荐镜头
└── negative/bodycon-negative.md        # 统一负面约束
`

**总计**：6 个子模块文件，5种轮廓，7种面料，5个动作，6种镜头
