# SIUF 2026 系列总览

> 版本：v2.0 | 更新：2026-05-28 | AI Fashion Director System v2.0

## 系列概述

SIUF 2026 深圳国际内衣展 × AI Fashion Director System 联合打造的 25 Look 商业化系列。
基于 13 模块数据库 + 十层 Prompt 结构 + PromptForge 拼接引擎生成。

---

## 25 个 Look 索引

### 已验证（7 个，v1.0 → v2.0 升级）

| # | 文件 | Look 名称 | Model | Hair | Motion | Outfit | Scene | Mood |
|---|------|-----------|-------|------|--------|--------|-------|------|
| 01 | [01-black-lace-finale.md](01-black-lace-finale.md) | 黑蕾丝压轴 | high-fashion | wet-wave | RUNWAY_WALK | lace-black | siuf-runway | confident |
| 02 | [02-white-lace-bride.md](02-white-lace-bride.md) | 纯白蕾丝新娘 | default | princess-half | EDITORIAL_STAND | lace-white | brand-showcase | mysterious |
| 03 | [03-sporty-function.md](03-sporty-function.md) | 运动机能风 | athletic | high-ponytail | CANDID_MOTION | sportswear-high | sport-launch | energetic |
| 04 | [04-luxury-gala.md](04-luxury-gala.md) | 奢华酒会 | mature-editorial | low-bun | LOOKBACK_BEND | silk-wine | vip-lounge | luxurious |
| 05 | [05-swimwear-resort.md](05-swimwear-resort.md) | 泳装度假风 | athletic | bun-clean | POOLSIDE_RECLINE | swimwear-neon | infinity-pool | playful |
| 06 | [06-cyber-lingerie.md](06-cyber-lingerie.md) | 未来机能风 | high-fashion | cyber-silver | EDITORIAL_STAND | cyberwear-silver | cyber-showcase | cold |
| 07 | [07-lace-loungewear.md](07-lace-loungewear.md) | 蕾丝睡衣慵懒 | default | shark-clip | CANDID_MOTION | lace-blush | hotel-bedroom | candid |

### 新增批次一（8 个，08-15）

| # | 文件 | Look 名称 | Model | Hair | Outfit | Scene | Mood |
|---|------|-----------|-------|------|--------|-------|------|
| 08 | [08-oriental-chinoiserie.md](08-oriental-chinoiserie.md) | 东方新中式 | default | oriental-bun | lace-embroidery | oriental-courtyard | mysterious |
| 09 | [09-pool-goddess.md](09-pool-goddess.md) | 湿发泳池女神 | athletic | wet-wave | swimwear-white | infinity-pool-sunset | confident |
| 10 | [10-cyber-angel.md](10-cyber-angel.md) | 银翼赛博天使 | high-fashion | cyber-silver | cyberwear-pvc | cyber-showcase | cold |
| 11 | [11-french-silk.md](11-french-silk.md) | 法式高级睡衣 | mature-editorial | french-curl | silk-cream | luxury-hotel | luxurious |
| 12 | [12-black-secretary.md](12-black-secretary.md) | 黑丝秘书御姐 | mature-editorial | low-bun | lace-black+pantyhose | urban-night | dominant |
| 13 | [13-tropical-resort.md](13-tropical-resort.md) | 海岛度假风 | petite | wet-wave | swimwear-floral | tropical-beach | playful |
| 14 | [14-future-swim.md](14-future-swim.md) | 未来高定泳装 | high-fashion | bun-clean | swimwear-metallic | minimalist-runway | editorial |
| 15 | [15-retro-hollywood.md](15-retro-hollywood.md) | 复古好莱坞 | mature-editorial | french-curl | swimwear-black-vintage | urban-night | mysterious |

### 新增批次二（10 个，16-25）

| # | 文件 | Look 名称 | Model | Hair | Outfit | Scene | Mood |
|---|------|-----------|-------|------|--------|-------|------|
| 16 | [16-y2k-sporty.md](16-y2k-sporty.md) | Y2K 运动机能 | petite | twin-ponytails | sportswear-y2k | stadium | energetic |
| 17 | [17-dark-gothic.md](17-dark-gothic.md) | 暗黑哥特 | high-fashion | high-ponytail | lace-gothic | black-studio | dominant |
| 18 | [18-minimalist.md](18-minimalist.md) | 极简主义 | default | center-straight | nude-minimal | white-studio | editorial |
| 19 | [19-tropical-jungle.md](19-tropical-jungle.md) | 热带丛林 | athletic | wet-wave | lace-cutout | tropical-jungle | playful |
| 20 | [20-metro-chic.md](20-metro-chic.md) | 摩登都市 | high-fashion | low-bun | cyberwear-geometric | city-rooftop | confident |
| 21 | [21-pink-barbie.md](21-pink-barbie.md) | 粉色芭比 | petite | twin-ponytails | sportswear-pink | pink-studio | playful |
| 22 | [22-western-cowboy.md](22-western-cowboy.md) | 西部牛仔 | athletic | wet-wave | lace-cutout | wooden-fence | confident |
| 23 | [23-ink-wash-oriental.md](23-ink-wash-oriental.md) | 水墨东方 | default | oriental-bun | lace-sheer | ink-wash | mysterious |
| 24 | [24-crystal-luxury.md](24-crystal-luxury.md) | 奢华宝石 | high-fashion | bun-clean | lace-crystal | black-studio | luxurious |
| 25 | [25-outdoor-sport.md](25-outdoor-sport.md) | 运动户外 | athletic | high-ponytail | sportswear-outdoor | stadium | energetic |

---

## 模块覆盖统计

| 模块 | 编码数 | 覆盖率 |
|------|--------|--------|
| ModelDNA | 5 个体型 | 5/5 ✅ |
| HairDNA | 12 个发型 | 12/12 ✅ |
| MotionDNA | 5 个组合动作 | 5/5 ✅ |
| OutfitDNA | 6 大品类 + 30 子品类 | ✅ |
| MaterialDNA | 6 种材质 | 6/6 ✅ |
| CameraDNA | 6 种镜头 + 4 品牌构图 | ✅ |
| LightDNA | 8 种布光 | 8/8 ✅ |
| SceneDNA | 20 个场景 | ✅ |
| MoodDNA | 8 种情绪 | 8/8 ✅ |
| BrandDNA | 7 个品牌语言 | 7/7 ✅ |
| CinematicFrame | 4 种电影构图 | 4/4 ✅ |
| PoseSkeleton | 5 个标准骨架 + JSON Schema | ✅ |
| PromptForge | 拼接引擎完整规格 | ✅ |

---

## Prompt 结构规范

每个 Look 文件包含完整十层结构：
1. Model — 模特体型+脸型+肤质+年龄+气质
2. Hair — 发型名+发丝细节+动态感+风格适配
3. Motion — 动作编码+五段式拆解+动态修饰
4. PoseSkeleton — 骨架参考描述
5. Outfit — 服装品类+材质+剪裁+品牌感+配饰
6. Material — 面料名+光影交互+质感描述
7. Camera — 机位+焦段+光圈+构图+品牌模板
8. Lighting — 主光源+辅助光+轮廓光+氛围+色温
9. Scene — 场景名+环境细节+情绪标签
10. Mood — 情绪关键词+氛围修饰+叙事感

负面约束统一英文格式。
