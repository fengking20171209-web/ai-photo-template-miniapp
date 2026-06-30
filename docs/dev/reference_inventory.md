# Reference Inventory

本文档用于整理本项目已下载的 GPT-Image-2 提示词资料库，说明每个资料库适合解决什么问题、日常该查哪些文件、如何把案例转成我们自己的模板资产。

## 本地资料库总览

| 资料库 | 本地路径 | 规模 | 适合用途 |
| --- | --- | ---: | --- |
| ZeroLu 精选玩法库 | `references/awesome-gpt-image` | 28 个文件，约 5 MB | 快速找灵感、学习高价值玩法、拆解 32 个精选案例 |
| EvoLinkAI 大规模案例库 | `references/awesome-gpt-image-2-API-and-Prompts` | 849 个文件，约 180 MB | 批量检索案例、抽取模式、对照图片效果、扩展模板库 |

## ZeroLu 精选玩法库

### 定位

这是一个轻量、精选、玩法导向的 GPT Image 2 提示词仓库。它的价值不是“资料特别多”，而是案例经过筛选，适合快速判断某种玩法是否值得产品化。

### 关键入口

| 内容 | 文件 |
| --- | --- |
| 简体中文主文档 | `references/awesome-gpt-image/README.zh-CN.md` |
| 英文主文档 | `references/awesome-gpt-image/README.md` |
| 推广说明中文 | `references/awesome-gpt-image/PROMOTION_CN.md` |
| 图片素材 | `references/awesome-gpt-image/assets/` |

### 重点场景

| 场景 | 对本项目的价值 |
| --- | --- |
| 摄影与照片级写实 | 优化职业形象、街拍写真、真实生活感模板 |
| 游戏与娱乐 | 后续可拓展娱乐化模板、短视频封面、社交传播玩法 |
| UI / UX 与社交媒体 | 可用于小程序界面 mockup、营销图、社交动态模拟 |
| 字体排版与海报设计 | 强化产品海报、商业海报、信息图模板 |
| 信息图、教育与文档 | 强化形象分析图卡、知识拆解图卡 |
| 角色与一致性 | 强化漫画角色卡、角色三视图、表情包模板 |
| 图像编辑与风格迁移 | 后续接入用户上传图编辑、漫画上色、局部替换 |

### 推荐用法

- 新模板立项时先查它，判断玩法是否有传播价值。
- 需要“案例感”时优先看它，因为它的案例更短、更容易拆。
- 不要直接复制整段提示词，要拆成我们模板系统里的字段。

## EvoLinkAI 大规模案例库

### 定位

这是一个更大的 GPT-Image-2 案例库，包含多语言说明、分类案例、图片结果和社区来源。它适合作为长期资料池，用来批量抽取提示词模式。

### 关键入口

| 内容 | 文件 |
| --- | --- |
| 简体中文主文档 | `references/awesome-gpt-image-2-API-and-Prompts/README_zh-CN.md` |
| 英文主文档 | `references/awesome-gpt-image-2-API-and-Prompts/README.md` |
| 中文分类案例 | `references/awesome-gpt-image-2-API-and-Prompts/cases/*_zh-CN.md` |
| 案例图片 | `references/awesome-gpt-image-2-API-and-Prompts/images/` |
| 社区数据 | `references/awesome-gpt-image-2-API-and-Prompts/data/ingested_tweets.json` |

### 中文分类文件

| 分类 | 文件 | 适合抽取的模板方向 |
| --- | --- | --- |
| 人像摄影 | `cases/portrait_zh-CN.md` | 古风写真、职业头像、街拍、杂志封面、模特图册 |
| 海报插画 | `cases/poster_zh-CN.md` | 商业海报、信息图、文旅海报、艺术海报 |
| UI 与社媒 | `cases/ui_zh-CN.md` | 小程序界面、电商首页、直播截图、社交动态 |
| 电商图 | `cases/ecommerce_zh-CN.md` | 产品主图、详情页、商品卖点图 |
| 广告创意 | `cases/ad-creative_zh-CN.md` | 品牌广告、节日活动、促销海报 |
| 角色设计 | `cases/character_zh-CN.md` | 漫画角色卡、三视图、角色一致性 |
| 对比实验 | `cases/comparison_zh-CN.md` | A/B 测试、参数对比、画质与风格评估 |

### 推荐用法

- 扩展模板库时查它，因为案例覆盖面大。
- 做某一类模板的批量升级时，集中阅读同一个分类文件。
- 需要图片参考时，结合 `images/` 目录查看输出效果。
- 做评测时参考 `comparison_zh-CN.md`，把不同描述方式变成测试项。

## 资料到模板的映射关系

| 我们的模板分类 | 优先参考 |
| --- | --- |
| 古风美女 | `portrait_zh-CN.md`、`poster_zh-CN.md`、ZeroLu 的摄影与海报案例 |
| 职业形象 | `portrait_zh-CN.md`、ZeroLu 的摄影与照片级写实 |
| 形象分析 | ZeroLu 的色彩/发型/信息图玩法、`poster_zh-CN.md`、`comparison_zh-CN.md` |
| 漫画角色 | `character_zh-CN.md`、ZeroLu 的角色一致性案例 |
| 产品海报 | `ecommerce_zh-CN.md`、`ad-creative_zh-CN.md`、ZeroLu 的海报设计案例 |
| 模特大赛 | `portrait_zh-CN.md`、`poster_zh-CN.md`、时尚杂志和图册类案例 |

## 案例筛选标准

一个案例适合进入我们的模板库，至少要满足下面 4 点：

- 可复用：不是只适合某个名人或某个梗。
- 可商业化：适合头像、写真、海报、图卡、商家素材等真实需求。
- 可结构化：能拆成主体、脸部、服装、场景、光线、镜头、画质、负面词。
- 可控：对人物一致性、排版、文字、产品位置、画幅有明确约束。

## 不建议直接产品化的内容

- 涉及真实公众人物合成的娱乐案例。
- 过度依赖特定 IP、游戏、影视品牌的案例。
- 文字过多且容易生成错字的复杂海报。
- 暴露、低俗、擦边或难以安全审查的视觉方向。

这些内容仍然可以学习结构，但不直接进入模板商城。
