# SIUF 2026 深圳内衣展 — AI 时尚造型系列

## 概述

基于 **AI Fashion Director System v2.0** 的 25 Look 商业化系列。
每个 Look 包含完整的十层 Prompt 结构，可直接用于 GPT Image 生图。

## 文件结构

```
siuf-2026/
├── README.md                          # 本文件
├── 01-black-lace-finale.md            # 黑蕾丝压轴
├── 02-white-lace-bride.md             # 纯白蕾丝新娘
├── 03-sporty-function.md              # 运动机能风
├── 04-luxury-gala.md                  # 奢华酒会
├── 05-swimwear-resort.md              # 泳装度假风
├── 06-cyber-lingerie.md               # 未来机能风
├── 07-lace-loungewear.md              # 蕾丝睡衣慵懒
├── 08-oriental-chinoiserie.md         # 东方新中式
├── 09-pool-goddess.md                 # 湿发泳池女神
├── 10-cyber-angel.md                  # 银翼赛博天使
├── 11-french-silk.md                  # 法式高级睡衣
├── 12-black-secretary.md              # 黑丝秘书御姐
├── 13-tropical-resort.md              # 海岛度假风
├── 14-future-swim.md                  # 未来高定泳装
├── 15-retro-hollywood.md              # 复古好莱坞
├── 16-y2k-sporty.md                   # Y2K 运动机能
├── 17-dark-gothic.md                  # 暗黑哥特
├── 18-minimalist.md                   # 极简主义
├── 19-tropical-jungle.md              # 热带丛林
├── 20-metro-chic.md                   # 摩登都市
├── 21-pink-barbie.md                  # 粉色芭比
├── 22-western-cowboy.md               # 西部牛仔
├── 23-ink-wash-oriental.md            # 水墨东方
├── 24-crystal-luxury.md               # 奢华宝石
└── 25-outdoor-sport.md                # 运动户外
```

## 使用方法

1. 选择一个 Look 文件
2. 复制 "十层 Prompt" 部分
3. 粘贴到 GPT Image 生图工具中
4. 复制 Negative 部分作为负面约束

## 模块化定制

使用 PromptForge 拼接引擎，通过 JSON 输入自定义组合：
- 选择 Model（5 种体型）
- 选择 Hair（12 种发型）
- 选择 Motion（5 个组合动作）
- 选择 Outfit（6 大品类 30+ 子品类）
- 选择 Scene（20 个场景）
- 选择 Mood（8 种情绪）
- 自动生成完整十层 Prompt

详见 `references/style-library/prompt-forge/prompt-forge-engine.md`
