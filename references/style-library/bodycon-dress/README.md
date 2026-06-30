# BodyconDressDNA — 模块总览 v1.0

> 版本：v1.0 | 创建：2026-05-28 | 柔塑曲线紧身裙专题

---

## 模块定位

把"紧身包臀短裙/连衣裙"从简单的性感元素，升级成可工程化控制的时装系统。

**核心不是**：越紧越好、胸大翘臀、直白性感
**核心是**：哑光·干净·贴合·支撑·比例·腿线·胸颈线·腰臀线

---

## 文件结构

```
bodycon-dress/
├── README.md                              # 本文件
├── silhouette/
│   └── bodycon-silhouettes.md             # 5 种核心轮廓
├── fabric/
│   └── bodycon-fabrics.md                 # 7 种推荐面料
├── styling/
│   └── bodycon-styling.md                 # 丝袜·鞋子·外套·配饰
├── motion/
│   └── bodycon-motions.md                 # 5 个专用动作
├── camera/
│   └── bodycon-cameras.md                 # 6 种推荐镜头
└── negative/
    └── bodycon-negative.md                # 统一负面约束
```

---

## 5 种核心轮廓

| # | 编码 | 名称 | 核心面料 | 场景 |
|---|------|------|----------|------|
| 01 | spaghetti_strap_bodycon | 细肩带经典 | matte compact jersey | 白棚·极简 |
| 02 | ruched_side_bodycon | 褶皱抽绳 | stretch jersey | 酒店·街拍 |
| 03 | bandage_bodycon | 绷带结构 | bandage knit | 晚宴·秀场 |
| 04 | ribbed_knit_bodycon | 针织极简 | ribbed knit | 通勤·都市 |
| 05 | oriental_halter_bodycon | 新中式融合 | satin+matte | 新中式场景 |

---

## 与现有模块对接

| BodyconDressDNA | 对接模块 |
|-----------------|----------|
| silhouette | OutfitDNA → skirt-database |
| fabric | MaterialDNA + fabric-engineering |
| styling | skirt-pairing-guide |
| motion | MotionDNA → 5个组合动作 |
| camera | CameraDNA → 6种镜头 |
| negative | 统一标准 |
| 模型 | ModelDNA → default-model |
| 发型 | HairDNA → 12种发型 |
| 场景 | SceneDNA → 20个场景 |
| 情绪 | MoodDNA → 8种情绪 |

---

## 4 个测试Prompt

### A｜白棚经典黑裙

```
realistic East Asian fashion model, soft natural face,
slightly fuller cheeks, visible skin texture,
calm confident expression,
black spaghetti strap bodycon mini dress,
clean scoop neckline, matte compact jersey,
soft sculpted waist, smooth hip line,
natural long leg line,
standing in a clean white studio,
one hand gently adjusting the hem,
relaxed shoulders,
85mm full-body editorial photography,
soft daylight, high-end magazine look
```

### B｜酒店御姐款

```
realistic East Asian woman, elegant mature beauty,
black bodycon mini dress with thin straps,
matte ponte double-knit fabric,
structured but soft silhouette,
deep collarbone line,
refined waist-to-hip proportion,
sheer smoky gray tights, pointed black heels,
modern luxury hotel interior, warm ambient light,
three-quarter side pose, one hand near waist,
85mm editorial fashion photography
```

### C｜街拍极简款

```
young adult East Asian model,
black minimal bodycon mini dress, scoop neckline,
matte stretch fabric,
oversized beige blazer draped over shoulders,
sheer nude tights, pointed heels,
urban street background, natural walking pose,
one leg stepping forward,
clean editorial street style,
70mm lens, soft afternoon light
```

### D｜新中式融合款

```
modern oriental bodycon mini dress,
dudou-inspired halter neckline,
embroidered satin upper detail,
matte fitted black mini skirt lower part,
soft sculpted silhouette,
Chinese round fan accessory,
luxury oriental hotel interior, warm lantern light,
realistic East Asian model, soft round face,
elegant posture,
85mm full-body editorial fashion photography
```
