# MuseFlow AI Studio (Phase 1: 轻量级基础设施与骨架) 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 构建面向“个人本地娱乐”的 MuseFlow AI Studio 核心底座，优化原生 SQLite 性能解决读写锁死，建立轻量级内存队列与 WebSocket 实时推送，并初始化 Next.js 三栏一底布局。

**架构：** 完全抛弃 Docker、PostgreSQL、Redis。使用开启 WAL 模式的高性能 SQLite 作为本地存储。利用 Python `asyncio.Queue` 构建单进程异步生图队列，避免跨进程开销。前端保持 Next.js 三栏布局，状态划分严谨。

**技术栈：** FastAPI, SQLite (WAL), asyncio (内置), Next.js, Tailwind CSS, Shadcn UI, TanStack Query, Zustand, WebSockets.

---

### 任务 1：重写数据库连接引擎 (开启 WAL 高性能模式)

**文件：**
- 修改：`backend/database.py`
- 修改：`backend/requirements.txt`
- 测试：`tests/backend/test_db_wal.py`

- [ ] **步骤 1：编写并发读写测试**
  在 `test_db_wal.py` 中编写异步测试，模拟 5 个协程同时向数据库快速读写，预期在默认 SQLite 模式下可能会触发锁报错或延迟较高。
- [ ] **步骤 2：精简无用依赖**
  清理 `requirements.txt`，确保没有 `psycopg2` 或 `redis` 等无效依赖。
- [ ] **步骤 3：修改数据库连接池并启用 WAL**
  修改 `database.py`，配置 SQLAlchemy 的 `create_engine` 传入 `connect_args={"check_same_thread": False}`，并在引擎连接事件 (engine listener) 中执行 `PRAGMA journal_mode=WAL;` 以及 `PRAGMA synchronous=NORMAL;`。
- [ ] **步骤 4：运行测试验证通过**
  运行并发测试验证不报错且速度提升。
- [ ] **步骤 5：Commit**
  `git commit -m "chore(db): optimize sqlite for local high-performance using WAL mode"`

### 任务 2：重构数据库核心模型 (Schema)

**文件：**
- 修改：`backend/models.py`
- 测试：`tests/backend/test_models.py`

- [ ] **步骤 1：编写模型验证测试**
  验证 `prompt_versions` 和 `generation_jobs` 表是否能正确关联。
- [ ] **步骤 2：运行测试验证失败**
  预期失败，因为结构尚未迁移。
- [ ] **步骤 3：编写最小实现代码**
  修改 `models.py`，建立 `projects`, `assets`, `prompt_versions` (含模板参数), `generation_jobs` (加 `idempotency_key` 防用户手抖多点), `favorites`。
- [ ] **步骤 4：生成 Alembic 迁移并跑通测试**
  执行 Alembic migration 更新本地开发库。
- [ ] **步骤 5：Commit**
  `git commit -m "feat(db): redesign core schema with local prompt versioning"`

### 任务 3：构建本地内存任务队列与 WebSocket 推送

**文件：**
- 创建：`backend/services/queue_manager.py`
- 创建：`backend/routers/ws.py`
- 修改：`backend/main.py`

- [ ] **步骤 1：编写内存队列调度测试**
  编写测试提交一个虚拟生图任务，验证 `asyncio.Queue` 是否能正常处理。
- [ ] **步骤 2：实现本地任务队列**
  在 `queue_manager.py` 中实现基于 `asyncio` 的后台 worker 循环，消费生图任务，并在关键进度点触发事件广播。
- [ ] **步骤 3：实现 WebSocket Router**
  在 `ws.py` 中建立 ConnectionManager，将 `queue_manager` 触发的事件直接推送给连接的本地客户端。
- [ ] **步骤 4：运行测试验证通过**
  模拟投递任务，验证 WebSocket 端点收到状态推送。
- [ ] **步骤 5：Commit**
  `git commit -m "feat(api): implement local asyncio queue and websocket broadcasting"`

### 任务 4：初始化 Next.js 前端应用与本地状态库

**文件：**
- 创建：`frontend/package.json`
- 创建：`frontend/store/uiStore.ts`
- 创建：`frontend/providers/QueryProvider.tsx`

- [ ] **步骤 1：创建 Next.js 项目**
  执行 `npx create-next-app@latest frontend --typescript --tailwind --eslint`。安装 `zustand` 和 `@tanstack/react-query`。
- [ ] **步骤 2：实现本地 UI 状态 (Zustand)**
  创建 `uiStore.ts` 控制本地折叠面板等。
- [ ] **步骤 3：配置服务器数据同步层 (React Query)**
  配置 `QueryProvider.tsx`。
- [ ] **步骤 4：运行服务测试**
  执行 `npm run dev` 确保启动。
- [ ] **步骤 5：Commit**
  `git commit -m "chore(web): init next.js with zustand and query for local studio"`

### 任务 5：搭建“三栏一底”骨架屏

**文件：**
- 重写：`frontend/app/layout.tsx`
- 创建：四个子区域组件

- [ ] **步骤 1：构建基础 Shell**
  编写左侧（灵感库）、中间（对话）、右侧（瀑布流）、底部（控制台）的代码骨架。
- [ ] **步骤 2：填入 Mock 占位与交互**
  连接 Zustand 确保折叠交互有效。
- [ ] **步骤 3：测试 UI 功能**
  编写 Vitest 测试交互逻辑。
- [ ] **步骤 4：验证视图**
  浏览器确认。
- [ ] **步骤 5：Commit**
  `git commit -m "feat(web): build local IDE layout shell"`
