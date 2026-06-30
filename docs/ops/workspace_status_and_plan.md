# AI Photo Template Miniapp — 工作区状态报告与下一步计划

> 编制时间：2026-05-27
> 工作区：D:\Projects\ai-photo-template-miniapp
> 备份：E:\BaiduNetdiskDownload\...\ai-photo-template-miniapp

---

## 一、当前工作区状态

### 1.1 项目概况

| 项目 | 说明 |
|------|------|
| 名称 | AI Photo Template Miniapp（AI 写真模板工坊） |
| 定位 | 本地可运行的 AI 写真模板生成系统 |
| 技术栈 | TypeScript (Node.js) + Python (FastAPI) + 原生 HTML/JS |
| 模板数 | 6 个（古风、职业、形象分析、漫画、产品海报、模特大赛） |
| 生图模式 | Mock（默认），可切换 HTTP API |
| 版本 | v0.1.0 |

### 1.2 文件结构

```
ai-photo-template-miniapp/
├── src/                    # TypeScript 核心模块（12 个文件）
│   ├── config/             # 配置读取
│   ├── server/             # HTTP 服务、任务存储
│   ├── services/           # Prompt 拼接、生图服务
│   ├── templates/          # 模板加载、校验
│   ├── types/              # 类型定义
│   └── workflows/          # 生成、列表、生图工作流
├── backend/                # Python FastAPI 后端
│   ├── main.py             # 入口（仅注册 images router）
│   ├── routers/images.py   # 图片搜索 API
│   ├── models.py           # 数据模型
│   ├── schemas/            # 请求/响应 schema
│   ├── services/           # 搜索服务
│   └── tests/              # 测试
├── public/                 # 前端页面（原生 HTML/JS/CSS）
│   ├── index.html          # 主页面
│   ├── app.js              # 前端逻辑
│   └── styles.css          # 样式
├── templates/              # 6 个模板 JSON
├── scripts/                # 12 个脚本（CLI、同步、测试）
├── docs/                   # 8 个文档（产品、API、部署、模板系统）
├── references/             # 3 个参考仓库
│   ├── awesome-gpt-image/
│   ├── awesome-gpt-image-2/          # 新增：GPT-Image2 风格库
│   └── awesome-gpt-image-2-API-and-Prompts/
├── deploy/                 # 腾讯云部署脚本
├── plugins/                # Kimi Agent 插件
├── output/                 # 生成结果、归档
├── logs/                   # 同步日志
├── uploads/                # 用户上传目录
├── prompts/                # 基础 Prompt、安全规则
├── .env                    # 环境变量（mock 模式）
├── package.json            # Node.js 依赖
├── tsconfig.json           # TypeScript 配置
└── README.md               # 项目说明
```

### 1.3 功能验证状态

| 功能 | 状态 | 说明 |
|------|------|------|
| TypeScript 编译 | ✅ 通过 | 零错误 |
| 模板加载（6个） | ✅ 通过 | 全部正常 |
| Prompt 拼接 | ✅ 通过 | 结构化输出 |
| Mock 生图任务 | ✅ 通过 | 生成 task.json |
| HTTP API 服务 | ✅ 可用 | `npm run api`，端口 3000 |
| 前端页面 | ✅ 可用 | public/index.html |
| GPT-Image2 Skill | ✅ 已安装 | ~/.codex/skills/ |
| 百度网盘同步 | ✅ 已配置 | 每2小时自动同步 |
| Python 后端 | ⚠️ 缺环境 | 系统无 Python，需安装 |
| Git 版本控制 | ❌ 未初始化 | 无法 git restore/diff |

### 1.4 关键发现

1. **没有 `backend/api/` 目录** — 后端路由在 `backend/routers/`
2. **没有 `frontend/` 目录** — 前端是 `public/` 下的原生 HTML/JS
3. **没有 `ai_lab_routes.py`** — 后端只有 `routers/images.py`
4. **没有 Vue.js** — 前端是 vanilla JS，不是 Vue 框架
5. **没有 Git 仓库** — 无法做版本恢复

---

## 二、已完成功能（V0.1）

### 2.1 TypeScript 前端模块

| 模块 | 文件 | 功能 |
|------|------|------|
| 配置 | src/config/appConfig.ts | 根目录、输出目录、API 配置 |
| 模板加载 | src/templates/templateRepository.ts | 根据 ID 读取模板 JSON |
| 模板校验 | src/templates/templateSchema.ts | 校验模板结构 |
| Prompt 拼接 | src/services/promptBuilder.ts | 模板字段 → 完整 Prompt |
| 生图服务 | src/services/aiImageService.ts | mock/HTTP 双模式 |
| HTTP 服务 | src/server/httpServer.ts | REST API 服务器 |
| 任务存储 | src/server/taskStore.ts | 本地 JSON 任务记录 |
| 生成工作流 | src/workflows/generatePromptWorkflow.ts | 加载→拼接→写文件 |
| 生图工作流 | src/workflows/runImageTaskWorkflow.ts | 模板→Prompt→生图 |
| 列表工作流 | src/workflows/listTemplatesWorkflow.ts | 列出可用模板 |

### 2.2 Python 后端

| 模块 | 文件 | 功能 |
|------|------|------|
| 入口 | backend/main.py | FastAPI app，注册 images router |
| 图片搜索 | backend/routers/images.py | GET /images 搜索接口 |
| 数据模型 | backend/models.py | SQLAlchemy 模型 |
| 搜索服务 | backend/services/search_service.py | 搜索逻辑 |
| Schema | backend/schemas/search.py | 请求/响应定义 |

### 2.3 前端页面

| 文件 | 功能 |
|------|------|
| public/index.html | 模板列表、详情、生成结果页 |
| public/app.js | 前端交互逻辑 |
| public/styles.css | 页面样式 |

### 2.4 模板（6个）

| 模板 ID | 分类 | 用途 |
|---------|------|------|
| ancient_diaochan | 古风美女 | 国风写真、古装头像 |
| career_flight_attendant | 职业形象 | 职业头像、个人品牌 |
| beauty_analysis | 形象分析 | 发型、妆容、色彩图卡 |
| noir_character_card | 漫画角色 | 角色卡、IP 设定 |
| product_poster | 产品海报 | 电商主图、直播封面 |
| model_contest | 模特大赛 | 模特报名图、时尚图册 |

### 2.5 参考资料库

| 仓库 | 用途 |
|------|------|
| awesome-gpt-image | 精选玩法导引 |
| awesome-gpt-image-2 | GPT-Image2 风格库 + 工业模板（新增） |
| awesome-gpt-image-2-API-and-Prompts | 案例库 + API 示例 |

---

## 三、下一步工作计划

### Phase 1：基础加固（本周）

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | 初始化 Git 仓库 | `git init` + 首次提交，建立版本控制 |
| P0 | 安装 Python 环境 | 安装 Python 3.10+，跑通后端 |
| P1 | 后端跑通验证 | `pip install -r requirements.txt` + 启动测试 |
| P1 | 前端本地预览 | `npm run api` 启动服务，浏览器验收 |
| P2 | 清理 output 历史 | 归档已完成的任务记录 |

### Phase 2：Prompt Forge 提示词锻造器（下周）

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | 新增 Prompt Forge 页面 | 基于 gpt-image-2-style-library 的结构化 Prompt 生成 |
| P0 | 中文需求输入 | 支持自然语言描述 → 结构化 Prompt |
| P1 | 用途选择 | 有声书封面、三国人物、古装写真、婚纱、职业头像、海报 |
| P1 | 风格选择 | 电影感、写实摄影、古风国潮、商业海报、历史古典、高级写真 |
| P2 | Prompt 输出 | 结构化结果（模板、Prompt、负面提示、比例、约束） |
| P2 | 复制功能 | 一键复制 main_prompt / negative_prompt |

### Phase 3：模板库扩充（第3周）

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | 有声书封面模板 | 借鉴 awesome-gpt-image-2 的海报/出版分类 |
| P0 | 三国人物图模板 | 貂蝉、小乔、甄姬、诸葛亮、赵云 |
| P1 | 古风场景图模板 | 赤壁、洛水、宫廷、江南水榭 |
| P1 | 课程海报模板 | 财税课程、AI 教程、知识库封面 |
| P2 | 网站配图模板 | 有声书首页 Banner、专题页图 |

### Phase 4：接入真实生图 API（第4周）

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | 接入 GPT Image API | 替换 mock 为真实生图 |
| P1 | 图片上传接口 | 先保存到 uploads/ |
| P2 | 接入 gpt-image-2-style-library Skill | Agent 辅助生成 Prompt |
| P2 | 任务持久化 | 数据库存储任务记录 |

### Phase 5：商业化准备（第5-6周）

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P1 | 腾讯云部署 | CVM + Nginx + PM2 |
| P1 | 用户系统 | 登录、鉴权 |
| P2 | 支付对接 | 微信/支付宝 |
| P2 | 高清图解锁 | 付费后返回高清图 |
| P3 | 抖音小程序 | WebView 嵌入 |

---

## 四、技术决策记录

| 决策 | 选择 | 原因 |
|------|------|------|
| 前端框架 | 原生 HTML/JS（非 Vue/React） | MVP 阶段轻量优先 |
| 后端框架 | FastAPI (Python) | 异步、自动文档、适合 AI 服务 |
| 模板格式 | JSON | 结构化、易扩展、Agent 可读 |
| 生图模式 | mock → HTTP 双模式 | 开发阶段不依赖外部 API |
| 参考资料 | awesome-gpt-image-2 | 工业级模板库，370+ 案例 |
| 同步方案 | robocopy + Windows 任务计划 | 解决百度网盘同步慢的问题 |

---

## 五、风险与待确认

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 无 Git 版本控制 | 无法恢复历史版本 | 尽快 git init + 首次提交 |
| Python 未安装 | 后端无法运行 | 安装 Python 3.10+ |
| 百度网盘同步延迟 | 文件版本不一致 | 已配置每2小时自动同步 |
| 无真实生图 API | 只能 mock 演示 | Phase 4 接入 GPT Image |
| 无用户系统 | 无法商业化 | Phase 5 添加 |

---

## 六、验收清单

- [ ] Git 仓库初始化并首次提交
- [ ] Python 环境安装完成
- [ ] 后端 `python -m backend.main` 启动成功
- [ ] 前端 `npm run api` 启动成功
- [ ] 浏览器访问 http://localhost:3000 正常
- [ ] 6 个模板全部可加载
- [ ] Mock 生图任务正常
- [ ] Prompt Forge 页面原型完成
- [ ] 百度网盘同步脚本正常运行