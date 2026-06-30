# AI Photo Template Miniapp

[English](README.md)

一个本地可运行的 AI 写真模板生成系统。它的目标不是简单换脸，而是把"用户上传头像 + 模板化 Prompt + 任务记录 + 后续生图接口"组织成一套可持续扩展的开源内容生产工具。

当前项目重点是第一阶段：先把模板系统、提示词拼接、本地任务记录、参考资料库整理好，为后续接入 GPT-Image-2 生图 API 和小程序前端做准备。

## 当前工作目录

主开发目录：

```text
D:\Projects\ai-photo-template-miniapp
```

原百度网盘同步目录保留为备份，不建议继续作为主开发目录。同步盘会拖慢大量小文件写入、Git clone、解压和依赖安装。

## 项目定位

用户上传自拍或头像后，系统根据模板生成：

- 古风写真
- 职业形象图卡
- 个人形象分析
- 漫画角色卡
- 产品海报
- 模特大赛风格图
- 短视频封面

产品核心是一个可扩展的"AI 模板化内容生成器"。

## 产品流程

```text
用户上传头像
↓
选择模板
↓
选择风格参数
↓
生成 Prompt
↓
记录本地任务
↓
预留 AI 生图 API 请求
↓
后续返回预览图
```

## 已完成能力

- 本地 TypeScript 项目骨架
- 模板 JSON 管理
- 6 个初始模板分类
- 模板结构校验
- 模板加载器
- Prompt 拼接器
- 本地生成任务 `task.json`
- 输出 `output/prompt.txt`
- AI 生图任务入口 `npm run image <template_id>`
- 默认 mock 生图服务，不实际扣费调用
- HTTP 生图服务适配层，后续可接 GPT-Image-2 / EvoLinkAI / 其他兼容接口
- GitHub 下载代理优化
- 两个 GPT-Image-2 参考资料库下载与整理

## 模板分类

| 分类 | 当前模板 | 用途 |
| --- | --- | --- |
| 古风美女 | `ancient_diaochan` | 国风写真、古典头像、写真套图 |
| 职业形象 | `career_flight_attendant` | 职业头像、个人品牌、形象包装 |
| 形象分析 | `beauty_analysis` | 发型、妆容、色彩、珠宝图卡 |
| 漫画角色 | `noir_character_card` | 角色卡、IP 设定、社交头像 |
| 产品海报 | `product_poster` | 电商主图、直播封面、品牌海报 |
| 模特大赛 | `model_contest` | 模特报名图、时尚图册、社媒展示 |
| SIUF 2026 内衣秀 | `siuf2026_01~25` | 内衣展 T 台秀场、时尚编辑 |
| 肚兜现代时装 | `dudou_d01~05` | 新中式肚兜主题、现代时装演绎 |
| 新中式概念 | `concept_neo-chinese-bodycon` | 东方元素与当代剪裁结合 |

## 项目结构

```text
ai-photo-template-miniapp/
├── README.md
├── package.json
├── tsconfig.json
├── .env.example
├── docs/
│   ├── api_design.md
│   ├── network_optimization.md
│   ├── operation_sop.md
│   ├── product_plan.md
│   ├── reference_inventory.md
│   ├── reference_repository.md
│   └── template_system.md
├── prompts/
│   ├── base_prompt.md
│   └── safety_rules.md
├── references/
│   ├── awesome-gpt-image/
│   └── awesome-gpt-image-2-API-and-Prompts/
├── scripts/
│   ├── check_network.ps1
│   ├── download_reference_repo.ps1
│   └── generate_prompt.ts
├── src/
│   ├── config/
│   ├── services/
│   ├── templates/
│   ├── types/
│   └── workflows/
├── templates/
├── uploads/
└── output/
```

## 快速开始

### Docker（推荐）

```bash
git clone https://github.com/your-org/ai-photo-template-miniapp.git
cd ai-photo-template-miniapp
docker-compose up
# 打开 http://localhost:3000
```

### 本地开发

安装依赖：

```bash
npm install
```

生成默认模板 Prompt：

```bash
npm run generate ancient_diaochan
```

生成指定模板：

```bash
npm run generate career_flight_attendant
npm run generate beauty_analysis
npm run generate noir_character_card
npm run generate product_poster
npm run generate model_contest
```

查看模板清单：

```bash
npm run list
```

不依赖 npm 的模板清单：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/list_templates.ps1
```

生成模板目录文档：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/generate_template_catalog.ps1
```

运行生图任务，默认 mock，不调用真实 API：

```bash
npm run image ancient_diaochan
```

不依赖 npm 的烟雾测试：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/smoke_test.ps1
```

只测试单个模板：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/smoke_test.ps1 -TemplateId ancient_diaochan
```

检查生图 API 配置：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check_image_env.ps1
```

类型检查：

```bash
npm run check
```

生成结果：

```text
output/prompt.txt
output/task.json
output/image_task.json
```

## 生图 API 配置

默认 `.env.example`：

```text
AI_IMAGE_API_KEY=
AI_IMAGE_API_URL=
AI_IMAGE_PROVIDER=mock
AI_IMAGE_DRY_RUN=true
OUTPUT_DIR=output
```

默认模式：

```text
AI_IMAGE_PROVIDER=mock
AI_IMAGE_DRY_RUN=true
```

这个模式只会生成 `output/image_task.json`，不会请求真实生图接口。

切换到 HTTP 生图接口时：

```text
AI_IMAGE_PROVIDER=http
AI_IMAGE_DRY_RUN=false
AI_IMAGE_API_URL=https://your-image-api.example.com/generate
AI_IMAGE_API_KEY=your_api_key
```

当前 HTTP 适配层会向 `AI_IMAGE_API_URL` 发送 JSON 请求：

```json
{
  "prompt": "...",
  "negative_prompt": "...",
  "ratio": "4:5",
  "quality": "high",
  "face_strength": 0.78,
  "output_count": 1
}
```

接口返回中如果包含 `url`、`image_url`、`output_url`、`image_urls`、`images`、`data`、`outputs` 等字段，系统会自动提取图片链接写入 `image_task.json`。

## 模板 JSON 结构

每个模板放在 `templates/` 下，文件名与 `template_id` 保持一致。

核心字段：

```json
{
  "template_id": "ancient_diaochan",
  "category": "古风美女",
  "title": "三国貂蝉",
  "version": "1.0.0",
  "ratio": "4:5",
  "face_lock": true,
  "style": "真人古风写真",
  "scene": "烛光宫殿，桃花飘落，古典帷幔",
  "clothing": "粉金色汉风长裙，轻纱披帛，金色发饰，珍珠耳坠",
  "prompt_blocks": {
    "subject": "一位保留用户真实五官的东方女性，三国貂蝉主题造型",
    "face": "保留原始脸型、五官比例、肤色和眼神特征，不改变身份感",
    "clothing": "粉金色汉风长裙，轻纱披帛，精致刺绣，古典腰封",
    "scene": "烛光宫殿，柔和金色背景，桃花花瓣，古风氛围",
    "lighting": "柔和暖光，电影级浅景深，面部清晰自然",
    "camera": "半身肖像，4:5比例，高级古风写真构图",
    "quality": "高清细节，真实皮肤质感，干净高级",
    "commercial_use": "适合社交媒体头像、封面图和写真套图预览"
  },
  "options": {
    "quality": "high",
    "face_strength": 0.78,
    "output_count": 1
  },
  "negative_prompt": ["过度磨皮", "网红脸", "低俗", "裸露"]
}
```

## 代码模块

| 模块 | 文件 | 作用 |
| --- | --- | --- |
| 配置读取 | `src/config/appConfig.ts` | 读取根目录、输出目录、预留 API 配置 |
| 模板类型 | `src/types/template.ts` | 定义模板分类和字段 |
| 任务类型 | `src/types/task.ts` | 定义本地生成任务结构 |
| 模板校验 | `src/templates/templateSchema.ts` | 校验 JSON 是否符合模板规范 |
| 模板加载 | `src/templates/templateRepository.ts` | 根据 template_id 读取模板 |
| Prompt 拼接 | `src/services/promptBuilder.ts` | 把模板字段拼成最终 Prompt |
| 生图服务 | `src/services/aiImageService.ts` | 生成请求体、mock 调用、HTTP API 调用 |
| 工作流 | `src/workflows/generatePromptWorkflow.ts` | 串起加载、拼接、写文件、记任务 |
| 生图任务工作流 | `src/workflows/runImageTaskWorkflow.ts` | 串起模板、Prompt、mock/HTTP 生图、写结果 |
| CLI 入口 | `scripts/generate_prompt.ts` | 命令行调用入口 |
| 生图 CLI 入口 | `scripts/run_image_task.ts` | 生图任务命令入口 |
| 烟雾测试 | `scripts/smoke_test.ps1` | 不依赖 npm，检查模板和 mock 任务结构 |
| 模板清单 | `scripts/list_templates.ts` / `scripts/list_templates.ps1` | 查看当前可用模板 |
| 模板目录生成 | `scripts/generate_template_catalog.ps1` | 生成 `docs/template_catalog.md` |
| 生图配置检查 | `scripts/check_image_env.ps1` | 检查 `.env` 是否能安全运行 |

## 外部参考资料

本项目已整理两个 GPT-Image-2 资料库。

### ZeroLu 精选玩法库

路径：

```text
references/awesome-gpt-image
```

特点：

- 精选玩法导向
- 适合快速找灵感
- 覆盖摄影、游戏、UI、海报、信息图、角色一致性、图像编辑等方向
- 有配套图片资产

优先阅读：

```text
references/awesome-gpt-image/README.zh-CN.md
```

### EvoLinkAI 大规模案例库

路径：

```text
references/awesome-gpt-image-2-API-and-Prompts
```

特点：

- 案例量更大
- 分类更细
- 多语言 README
- 有 `cases/`、`images/`、`data/`
- 适合批量提炼模板模式

优先阅读：

```text
references/awesome-gpt-image-2-API-and-Prompts/README_zh-CN.md
references/awesome-gpt-image-2-API-and-Prompts/cases/portrait_zh-CN.md
references/awesome-gpt-image-2-API-and-Prompts/cases/poster_zh-CN.md
references/awesome-gpt-image-2-API-and-Prompts/cases/ecommerce_zh-CN.md
references/awesome-gpt-image-2-API-and-Prompts/cases/character_zh-CN.md
```

完整资料索引：

```text
docs/reference_inventory.md
```

## Kimi / Agent Skills（待配置）

> 注：项目级 Skill 和专用 Agent 配置尚未创建，以下说明为规划内容。

规划中的项目级 Skill：

```text
.agents/skills/ai-photo-template-workflow/SKILL.md
```

规划用途：

- 新增或优化 AI 写真模板
- 从参考库提炼 Prompt 模式
- 运行 mock 生图任务
- 执行模板安全审查
- 按项目 SOP 更新文档

规划中的 Kimi Agent 配置：

```text
.kimi/agents/photo-template-agent.yaml
```

规划用途：

- 固定当前项目的工作目录和开发边界
- 默认使用 mock 生图模式，避免误触发真实 API 扣费
- 约束密钥、参考资料、模板结构和测试流程

Wire 协议预研文档：

```text
docs/kimi_wire_integration.md
```

Wire 握手测试：

```powershell
uv run python scripts\kimi_wire_smoke.py
```

## 腾讯云网站 MVP

部署规划：

```text
docs/tencent_cloud_mvp_plan.md
```

本地启动 MVP API：

```powershell
npm run api
```

已支持接口：

```text
GET  /
GET  /health
GET  /templates
GET  /templates/{template_id}
POST /generate
GET  /tasks/{task_id}
GET  /tasks/{task_id}/prompt
```

接口文档：

```text
docs/api/mvp.md
```

## 图库搜索后端

Kimi Agents 交付的图库搜索 API 已融合到：

```text
backend/
```

接口：

```text
GET /images/
```

能力：

- 关键词搜索 `title` / `prompt`
- JSONB tags 过滤
- 日期范围过滤
- 分页

说明：

```text
backend/README.md
docs/api/gallery_search.md
```

该模块属于第二阶段图库/结果库能力；当前腾讯云 MVP 主线仍优先使用 `npm run api` 的 Node.js API。

## 部署脚本

腾讯云部署脚本：

```powershell
powershell -ExecutionPolicy Bypass -File deploy\deploy-tencent.ps1
```

部署说明：

```text
deploy/README.md
```

## Kimi 自定义插件

项目内置一个本地 Kimi 插件：

```text
plugins/kimi-photo-template-tools
```

提供工具：

- `list_templates`
- `smoke_test_templates`
- `check_image_env`
- `generate_template_catalog`

安装：

```powershell
$env:Path = "C:\Users\Aerc\.local\bin;$env:Path"
kimi plugin install D:\Projects\ai-photo-template-miniapp\plugins\kimi-photo-template-tools
```

验证：

```powershell
kimi plugin list
kimi plugin info kimi-photo-template-tools
```

## 资料如何融入项目

不要把外部资料直接复制成产品模板，而是按三层使用。

第一层：参考层。

```text
references/
```

用于查案例、看玩法、找图片效果。

第二层：提炼层。

从案例中抽取稳定的提示词模式：

```text
主体身份
脸部保真
服装造型
场景环境
光影氛围
镜头构图
画质要求
商业用途
负面提示
```

第三层：产品层。

把提示词模式改写成我们自己的模板 JSON：

```text
templates/<template_id>.json
```

## 标准作业流程

完整 SOP：

```text
docs/operation_sop.md
```

简版流程：

```text
确定模板目标
↓
查参考资料
↓
拆解提示词模式
↓
编写模板 JSON
↓
npm run generate <template_id>
↓
检查 output/prompt.txt
↓
检查 output/task.json
↓
进入后续生图测试
```

## 网络与代理

当前推荐 GitHub 下载配置：

```text
http.sslbackend = openssl
http.proxy = socks5h://127.0.0.1:10808
```

检查网络：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check_network.ps1
```

重新下载 EvoLinkAI 参考库：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/download_reference_repo.ps1
```

网络说明：

```text
docs/network_optimization.md
```

## 安全与合规边界

禁止生成或产品化：

- 明确裸露
- 性行为暗示
- 未成年人性感化
- 极端暴露服装
- 成人用品露骨营销
- 真实公众人物身份滥用
- 侵犯 IP 或商标的商用模板
- 医疗、法律、金融等高风险误导性内容

推荐方向：

- 高级写真
- 国风造型
- 职业形象
- 时尚海报
- 形象分析
- 产品图录
- 角色设定
- 信息图卡

## 后续路线

### Phase 1：本地模板系统

- 完成模板 JSON
- 完成 Prompt 拼接
- 输出生成任务
- 整理参考资料
- 建立 SOP

### Phase 2：接入 AI 生图 API

- 完成 mock / HTTP 生图接口适配
- 接入图片上传
- 替换为真实 GPT-Image-2 或其他生图接口
- 任务队列
- 结果存储
- 输出图片预览

### Phase 3：小程序/前端

- 用户登录
- 模板浏览
- 上传头像
- 生成任务
- 结果展示
- 社交分享

## 当前建议的下一步

本项目已开源，欢迎贡献模板和代码。

建议顺序：

1. 从 `portrait_zh-CN.md` 提炼 5 个高质量人像模板，提交 PR。
2. 从 `ecommerce_zh-CN.md` 提炼 3 个产品海报模板，提交 PR。
3. 从 ZeroLu 精选库提炼 3 个高传播玩法模板，提交 PR。
4. 为项目添加新的生图 API 适配器（如 OpenAI、Stability AI）。
5. 改进前端 UI，支持模板实时预览。
6. 用 `npm run image <template_id>` 先跑 mock 生图任务验证模板质量。
7. 确认真实 API 供应商后，把 `.env` 切到 `AI_IMAGE_PROVIDER=http`。
