# AI 写真工坊 Studio

> 一个完全 DIY、用户驱动的 AI 写真生成工作室：稳定的人物一致性、可复用素材库、跨库智能推荐与本地提示词副驾，全程以「可编辑的 Prompt 草稿」为唯一生成来源。

后端 FastAPI + SQLite，前端原生 JavaScript，接入云端图像 API（SenseNova / Agnes，OpenAI 兼容）。无需自训练模型、不依赖 LoRA。

## 核心特性

- **DIY Prompt OS**：最终提示词只来自用户输入（场景/人物/服装/姿态/光影标签 + 自定义文字）+ 可选模特身份，**不注入任何模板风格档案**（无"古风/历史美人"漂移），并带提示词溯源与注入拦截。
- **模特库（人物一致性）**：绑定参考脸图（作为 img2img 输入复用）+ 自动注入身份一致性 / 防换脸·换身材的正负提示词，实现多次生成同一人。后端持久化（SQLite）。
- **背景库（440）/ 服装库（510）**：纯文本+标签、多维筛选；服装使用时尚/editorial 措辞。点击任意素材**只追加到可编辑 Prompt 草稿**，绝不直接生图。
- **CRE v2 跨库推荐引擎**：规则式加权（概念重叠 + 用量 + 模特亲和 + 会话上下文），可解释、确定性、纯内存（<50ms）；支持 v1/v2 切换。
- **Prompt Copilot（本地规则）**：自动补全为严格 7 段结构 `[Model][Background][Outfit][Pose][Lighting][Camera][Style Keywords]`、增强、3 变体、随机协调；流式分阶段呈现；不生图、无外部 API。
- **一键生成工作流**：空着直接点也能出图（CRE 自动补全缺失项），或「Surprise」随机协调；用户输入始终优先。
- **精品库管理**：作品集浏览、单删 / 多选批量删除（同时清理本地文件）。

## 快速开始

```bash
# 1. 配置环境变量（参考 .env.example），填入图像 API 凭据
cp .env.example .env

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动后端（同时托管前端静态页）
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# 4. 打开 http://127.0.0.1:8000/
```

可选：开启真实生成需在环境变量设置 `ENABLE_REAL_IMAGE_API=true`（默认走零成本 mock）。

## 技术栈

- 后端：Python · FastAPI · SQLAlchemy · SQLite (WAL)
- 前端：原生 JavaScript + CSS（暗色 Studio 主题）
- 图像 API：SenseNova U1（text2img）、Agnes Image 2.1（text2img / img2img），OpenAI 兼容
- 数据：JSON 模板/素材库，SQLite 画廊与模特库

## 提示词管线（严格分层）

```
用户输入（最高优先）
  → 模特身份（若选中）
  → 背景 / 场景
  → DIY 基线（现代电影写实，无风格档案）
  → 负面词（系统安全 + 一致性）
```

素材库与推荐引擎仅作为"提示词原料"建议，写入可编辑草稿；用户改完再生成。

## 测试

```bash
python -m pytest tests/backend backend/tests -q
```

## 许可证

MIT License，详见 [LICENSE](LICENSE)。
