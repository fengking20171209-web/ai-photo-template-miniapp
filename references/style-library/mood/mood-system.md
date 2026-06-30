# MoodDNA — 情绪系统 v2.0

> 版本：v2.0 | 创建：2026-05-28 | 8 种核心情绪 + 情绪×姿势矩阵

---

## 01. Confident（自信）

**编码**：confident
**关键词**：自信、掌控、力量、从容
**面部**：直视镜头，嘴角微扬或平静，下巴微抬，眉眼舒展
**体态**：开放姿态，重心稳固，挺胸收腹，占据空间
**叙事**：她知道自己在做什么，不需要任何人的认可

### Prompt 情绪修饰
自信从容的气场，不刻意的掌控感，从容不迫的优雅，
眼神直视镜头传递坚定信念，姿态开放占据空间

---

## 02. Mysterious（神秘）

**编码**：mysterious
**关键词**：神秘、深邃、若隐若现、不可捉摸
**面部**：眼神深邃或回避镜头，嘴角似笑非笑，光影遮挡部分面容
**体态**：有遮挡的姿态，回头、侧身、半隐半现
**叙事**：她有什么秘密，你想知道但永远猜不透

### Prompt 情绪修饰
神秘莫测的深邃气质，若隐若现的诱惑力，
眼神中藏着故事，光影中半遮半掩，
不可捉摸的距离感，引人探究的神秘魅力

---

## 03. Playful（俏皮）

**编码**：playful
**关键词**：俏皮、活泼、甜美、轻松
**面部**：笑容灿烂，眼睛弯弯，自然不做作的表情
**体态**：动态活泼，旋转、跳跃、自然动作
**叙事**：她在享受这一刻，快乐是会传染的

### Prompt 情绪修饰
俏皮活泼的青春气息，甜美自然的笑容，
轻松自在的快乐感，灵动活泼的姿态，
无忧无虑的感染力，充满生命力的少女感

---

## 04. Energetic（活力）

**编码**：energetic
**关键词**：活力、运动、力量、阳光
**面部**：坚定有神，运动后的自然红润，充满力量感
**体态**：运动动态，肌肉线条显现，力量与美结合
**叙事**：她的美来自生命力，来自运动和汗水

### Prompt 情绪修饰
活力四射的运动精神，阳光健康的力量美，
运动后的自然红润和微汗光泽，充满生命力的姿态，
自信飒爽的运动精神，肌肉线条与柔美的完美结合

---

## 05. Luxurious（奢华）

**编码**：luxurious
**关键词**：奢华、高级、优雅、从容
**面部**：从容淡定，眼神中有阅历沉淀，嘴角微微上扬
**体态**：优雅从容，动作慢而有质感，占据空间的方式很高级
**叙事**：她习惯了美好的事物，奢华是她的日常

### Prompt 情绪修饰
奢华从容的高级感，阅历沉淀的优雅美，
动作缓慢而有质感，每一个细节都透着精致，
不刻意的贵气，浑然天成的奢华气质

---

## 06. Dominant（主导）

**编码**：dominant
**关键词**：主导、强势、霸气、掌控
**面部**：俯视或平视镜头，表情冷静或微带攻击性，眉眼锐利
**体态**：占据主导地位的姿态，叉腰、双手抱头、后弓
**叙事**：她是这里的女王，规则由她来定

### Prompt 情绪修饰
强势主导的女王气场，不怒自威的掌控力，
霸气外露的姿态和表情，凌厉锐利的眼神，
统治级别的存在感，让周围的空气都凝固

---

## 07. Editorial（编辑）

**编码**：editorial
**关键词**：编辑、概念化、艺术、前卫
**面部**：无表情或概念化表情，时尚大片的冷淡感
**体态**：杂志级定点pose，几何感强，概念化肢体语言
**叙事**：她不是在拍照，她是在创造一件艺术品

### Prompt 情绪修饰
杂志编辑级的概念化表达，艺术化的肢体语言，
高级时装大片的冷淡美学，几何感的构图和姿态，
前卫先锋的时尚态度，超越常规的视觉表达

---

## 08. Cold（冷酷）

**编码**：cold
**关键词**：冷酷、疏离、距离感、冰感
**面部**：无表情，冷淡疏离，五官在冷光中更显立体
**体态**：不动如山，距离感的姿态，力量感但不攻击
**叙事**：她不属于这个世界，她的美有距离感

### Prompt 情绪修饰
冷酷疏离的冰感美学，距离感带来的高级吸引力，
无表情的冷淡中透着强大气场，五官在冷光中更立体，
不属于人间的超脱感，冰冷中的极致美

---

## 情绪 × 姿势矩阵

| 情绪 | 最佳动作 | 次选动作 | 禁忌动作 |
|------|----------|----------|----------|
| confident | RUNWAY_WALK, BACK_ARCH, OVER_SHOULDER | EDITORIAL_STAND, HAIR_FLIP | WALKING_BACK(回避) |
| mysterious | TWIST_TURN, WALKING_BACK, INTIMATE_GAZE | LOOKBACK_BEND, FLOOR_POSE | OVERHEAD_REACH(开放) |
| playful | CANDID_MOTION, DANCE_SPIN, OVERHEAD_REACH | HAIR_FLIP, POOLSIDE_RECLINE | STANDING_NEUTRAL(静态) |
| energetic | CANDID_MOTION, DEEP_SQUAT, HAIR_FLIP | OVERHEAD_REACH, DANCE_SPIN | FLOOR_POSE(静态) |
| luxurious | ARCH_BACK, FLOOR_POSE, EDITORIAL_STAND | SIDE_POSE, POOLSIDE_RECLINE | DEEP_SQUAT(运动) |
| dominant | RUNWAY_WALK, HANDS_BEHIND_HEAD, BACK_ARCH | EDITORIAL_STAND, DEEP_SQUAT | CANDID_MOTION(随意) |
| editorial | EDITORIAL_STAND, FLOOR_POSE, SIDE_POSE | STANDING_NEUTRAL, TWIST_TURN | DANCE_SPIN(活泼) |
| cold | STANDING_NEUTRAL, WALKING_BACK, HANDS_BEHIND_HEAD | EDITORIAL_STAND, INTIMATE_GAZE | DANCE_SPIN(活泼) |

---

## 情绪 × 服装矩阵

| 情绪 | 最佳服装 | 次选服装 | 不适配 |
|------|----------|----------|--------|
| confident | lace-black, sportswear-high, cyberwear-silver | silk-wine, swimwear-neon | nude-minimal(太安静) |
| mysterious | lace-black, lace-nude, silk-cream | oriental-bun系列, ink-wash系列 | sportswear-neon(太运动) |
| playful | swimwear-neon, sportswear-pink, lace-blush | twin-ponytails系列 | cyberwear-black(太冷) |
| energetic | sportswear-neon, sportswear-high, swimwear-neon | sportswear-y2k | silk-cream(太安静) |
| luxurious | silk-wine, silk-cream, lace-crystal | lace-black, lace-nude | sportswear-neon(太运动) |
| dominant | lace-black, cyberwear-liquid, lace-gothic | silk-black, sportswear-high | lace-blush(太甜) |
| editorial | cyberwear-silver, nude-minimal, lace-white | silk-silver, all极简系列 | sportswear-pink(太甜) |
| cold | cyberwear-silver, cyberwear-black, lace-black | lace-gothic, silk-black | lace-blush(太暖) |

---

## 情绪 × 灯光矩阵

| 情绪 | 最佳灯光 | 次选灯光 | 色温范围 |
|------|----------|----------|----------|
| confident | runway-spotlight, golden-hour | soft-editorial-box | 3200-5600K |
| mysterious | cinematic-tungsten, neon-edge | luxury-hotel-ambient | 2700-3500K |
| playful | golden-hour, pool-reflection | soft-editorial-box | 3200-5500K |
| energetic | runway-spotlight, golden-hour | pool-reflection | 5000-6500K |
| luxurious | cinematic-tungsten, luxury-hotel-ambient | golden-hour | 2700-4000K |
| dominant | runway-spotlight, cyber-blue-purple | neon-edge | 5000-10000K |
| editorial | soft-editorial-box, cinematic-tungsten | cyber-blue-purple | 3200-5500K |
| cold | cyber-blue-purple, neon-edge | runway-spotlight | 5000-10000K |
