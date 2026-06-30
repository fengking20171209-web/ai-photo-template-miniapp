# PromptForge — 模块化 Prompt 拼接引擎 v2.0

> 版本：v2.0 | 创建：2026-05-28 | 拼接规则 + 输出格式 + 模板

---

## 一、引擎概述

PromptForge 是 AI Fashion Director System 的核心拼接引擎，
将 13 个模块的数据库通过标准化输入，拼接为完整的十层中文 Prompt。

**输入**：JSON 格式的模块选择
**输出**：十层中文 Prompt + 英文负面约束，可直接用于 GPT Image 生图

---

## 二、输入格式

```json
{
  "model": "default-model",
  "hair": "wet-wave",
  "motion": "SIUF_LOOKBACK_BEND",
  "outfit": "lace-black",
  "material": "micro-lace",
  "camera": "85mm-low-angle",
  "lighting": "runway-spotlight",
  "scene": "siuf-runway",
  "mood": "confident",
  "brand": "siuf-official",
  "cinematic_frame": null,
  "pose_skeleton": "SIUF_LOOKBACK_BEND"
}
```

### 输入字段说明

| 字段 | 必填 | 来源模块 | 示例值 |
|------|------|----------|--------|
| model | ✅ | ModelDNA | default-model, petite-model, athletic-model, high-fashion-model, mature-editorial-model |
| hair | ✅ | HairDNA | wet-wave, center-straight, high-ponytail, ... (12种) |
| motion | ✅ | MotionDNA | SIUF_RUNWAY_WALK, SIUF_LOOKBACK_BEND, ... (5个组合动作) |
| outfit | ✅ | OutfitDNA | lace-black, silk-wine, swimwear-neon, ... (全品类) |
| material | ⭕ | MaterialDNA | micro-lace, semi-silk, liquid-metallic, ... (6种) |
| camera | ⭕ | CameraDNA | 85mm, 50mm, 35mm, 24mm, 135mm, macro |
| lighting | ✅ | LightDNA | runway-spotlight, golden-hour, ... (8种) |
| scene | ✅ | SceneDNA | siuf-runway, infinity-pool, cyber-showcase, ... (20种) |
| mood | ✅ | MoodDNA | confident, mysterious, playful, ... (8种) |
| brand | ⭕ | BrandDNA | vogue, maxim, vs-runway, siuf-official, ... (7种) |
| cinematic_frame | ⭕ | CinematicFrame | cinematic-widescreen, cinematic-close, ... (4种) |
| pose_skeleton | ⭕ | PoseSkeleton | SIUF_RUNWAY_WALK, SIUF_LOOKBACK_BEND, ... (5种) |

---

## 三、拼接规则

### 规则 1：十层顺序拼接

按固定顺序拼接，每层之间用逗号分隔：

```
① Model → ② Hair → ③ Motion → ④ PoseSkeleton → ⑤ Outfit → ⑥ Material → ⑦ Camera → ⑧ Lighting → ⑨ Scene → ⑩ Mood
```

### 规则 2：模块内语义排序

每个模块的描述词按以下语义相关性排序：
1. 体型/结构特征（最核心）
2. 材质/质感描述
3. 光影效果
4. 动态/情绪修饰

### 规则 3：品牌模板覆盖

如果指定了 brand 字段：
- Camera 层追加品牌构图描述词
- Lighting 层参考品牌适配灯光
- 整体色调和风格参考品牌语言

### 规则 4：电影构图叠加

如果指定了 cinematic_frame 字段：
- Camera 层替换为电影构图参数
- 画幅比和构图风格覆盖默认值
- 灯光参考电影构图的光影要求

### 规则 5：情绪关键词附加

MoodDNA 的情绪关键词附加在 Scene 层之后，作为场景的情绪注释。

### 规则 6：材质自动匹配

如果未指定 material 字段：
- 根据 outfit 品类自动推荐最佳材质
- 参考 outfit-fabric-matrix 的 ⭐最佳 搭配

### 规则 7：负面约束统一

无论输入如何变化，负面约束统一为：

```
Negative: plastic skin, overexposed, messy background, bad anatomy, blurred face, distorted hands, unnatural skin texture, low quality, watermark, text
```

---

## 四、输出格式

### 标准输出

```markdown
# SIUF 2026 深圳内衣展 — Look XX：{Look名称}

> 风格：{风格关键词} | 场景：{场景名} | 镜头：{镜头描述}
> Model：{model编码} | Hair：{hair编码} | Motion：{motion编码}

## 十层 Prompt

① Model: {从 model-base/ 对应文件提取的 Prompt 拼接模板}

② Hair: {从 hairstyle/ 对应发型提取的描述词}

③ Motion: {从 motions/ 对应动作提取的五段式描述}

④ PoseSkeleton: {从 pose-skeleton/ 对应骨架提取的骨架描述}

⑤ Outfit: {从 clothing/ 对应服装提取的描述模板}

⑥ Material: {从 materials/ 对应材质提取的描述词}

⑦ Camera: {从 camera/ 对应镜头提取的描述词 + 品牌构图}

⑧ Lighting: {从 lighting/ 对应方案提取的描述词}

⑨ Scene: {从 backgrounds/ 对应场景提取的描述词}

⑩ Mood: {从 mood/ 对应情绪提取的描述词}

## Negative
plastic skin, overexposed, messy background, bad anatomy, blurred face, distorted hands, unnatural skin texture, low quality, watermark, text
```

---

## 五、拼接示例

### 输入

```json
{
  "model": "high-fashion-model",
  "hair": "wet-wave",
  "motion": "SIUF_RUNWAY_WALK",
  "outfit": "lace-black",
  "material": "micro-lace",
  "camera": "135mm",
  "lighting": "runway-spotlight",
  "scene": "siuf-runway",
  "mood": "confident",
  "brand": "siuf-official"
}
```

### 输出（完整 Prompt）

亚洲年轻女性，国际超模风格，25-30岁冷艳气质，长脸偏方，颧骨高挺，下颌线锐利如刀刻，眼窝深邃，175-180cm骨感修长身材，超模比例十头身，冷白皮，骨骼结构立体，锁骨突出，颈部修长，眼神冷淡带攻击性，天生T台脸，
湿感大波浪长卷发，黑色发丝光泽如水，发尾湿润感，大波浪卷度自然垂落，慵懒中带精致，
SIUF_RUNWAY_WALK T台步态，正面走来步态稳健有力，定点pose侧身展示，回眸收尾冷峻表情，head_high gaze_forward expression_fierce，hip_sway_confident weight_shifting_rhythmically，long_stride toes_pointed heels_high，mid-stride动态捕捉，
参考T台模特标准步态骨架，重心在前脚后脚蹬地，胯部自然摆动双肩平行，
黑色蕾丝镂空内衣套装，半透明蕾丝罩杯精致刺绣花边，高腰蕾丝底裤侧面绑带，黑色吊带袜，Swarovski水晶锁骨链，细跟黑色高跟鞋，
微距蕾丝刺绣面料，花纹投射精致阴影到肌肤，透光与不透光精美对比，刺绣细节极致丰富，高定工艺级别面料，
135mm长焦镜头F2.8光圈，空间压缩效果背景元素堆叠，侧身轮廓极致突出，SIUF展会官方级构图品牌感，
秀场追光灯效果头顶45度强聚光灯照射，侧面追光勾勒身体轮廓，烟雾中光线散射体积光，冷色温专业秀场照明，
2026 SIUF深圳内衣展主舞台，蓝色冰屏LED背景，T台射灯烟雾效果，高反射地面映射灯光，国际时装周级秀场设计，
自信霸气冷艳疏离，秀场女王气场不怒自威，高级时装压迫感，T台压轴戏剧张力

Negative: plastic skin, overexposed, messy background, bad anatomy, blurred face, distorted hands, unnatural skin texture, low quality, watermark, text
```

---

## 六、Look 规划模板

### SIUF 2026 系列 25 个 Look 的标准输入

以下为所有 25 个 Look 的推荐模块组合：

| # | model | hair | motion | outfit | scene | mood |
|---|-------|------|--------|--------|-------|------|
| 01 | high-fashion | wet-wave | RUNWAY_WALK | lace-black | siuf-runway | confident |
| 02 | default | princess-half | EDITORIAL_STAND | lace-white | brand-showcase | mysterious |
| 03 | athletic | high-ponytail | CANDID_MOTION | sportswear-high | sport-launch | energetic |
| 04 | mature-editorial | low-bun | LOOKBACK_BEND | silk-wine | vip-lounge | luxurious |
| 05 | athletic | bun-clean | POOLSIDE_RECLINE | swimwear-neon | infinity-pool | playful |
| 06 | high-fashion | cyber-silver | EDITORIAL_STAND | cyberwear-silver | cyber-showcase | cold |
| 07 | default | shark-clip | CANDID_MOTION | lace-blush | hotel-bedroom | candid |
| 08 | default | oriental-bun | EDITORIAL_STAND | lace-embroidery | oriental-courtyard | mysterious |
| 09 | athletic | wet-wave | POOLSIDE_RECLINE | swimwear-white | infinity-pool-sunset | confident |
| 10 | high-fashion | cyber-silver | EDITORIAL_STAND | cyberwear-pvc | cyber-showcase | cold |
| 11 | mature-editorial | french-curl | LOOKBACK_BEND | silk-cream | luxury-hotel | luxurious |
| 12 | mature-editorial | low-bun | TWIST_TURN | lace-black | urban-night | dominant |
| 13 | petite | wet-wave | CANDID_MOTION | swimwear-floral | tropical-beach | playful |
| 14 | high-fashion | bun-clean | EDITORIAL_STAND | swimwear-metallic | minimalist-runway | editorial |
| 15 | mature-editorial | french-curl | LOOKBACK_BEND | swimwear-black-vintage | urban-night | mysterious |
| 16 | petite | twin-ponytails | CANDID_MOTION | sportswear-y2k | stadium | energetic |
| 17 | high-fashion | high-ponytail | EDITORIAL_STAND | lace-gothic | black-studio | dominant |
| 18 | default | center-straight | STANDING_NEUTRAL | nude-minimal | white-studio | editorial |
| 19 | athletic | wet-wave | CANDID_MOTION | lace-cutout | tropical-jungle | playful |
| 20 | high-fashion | low-bun | EDITORIAL_STAND | cyberwear-geometric | city-rooftop | confident |
| 21 | petite | twin-ponytails | DANCE_SPIN | sportswear-pink | pink-studio | playful |
| 22 | athletic | wet-wave | CANDID_MOTION | lace-cutout | wooden-fence | confident |
| 23 | default | oriental-bun | TWIST_TURN | lace-sheer | ink-wash | mysterious |
| 24 | high-fashion | bun-clean | EDITORIAL_STAND | lace-crystal | black-studio | luxurious |
| 25 | athletic | high-ponytail | CANDID_MOTION | sportswear-outdoor | stadium | energetic |
