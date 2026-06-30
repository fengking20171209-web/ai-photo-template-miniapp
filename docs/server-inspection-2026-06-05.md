# 腾讯云服务器全面巡检报告

**日期**: 2026-06-05 08:45 CST  
**服务器**: VM-0-5-ubuntu (Tailscale IP: 100.92.38.117)  
**巡检方式**: Tailscale 内网互通 + SSH + API 健康检查 + 端口扫描

---

## 一、GBrain 配置与使用

### 1.1 基本信息

| 项目 | 详情 |
|------|------|
| **服务名** | `gbrain-api.service` |
| **运行状态** | ✅ Active (running) |
| **监听端口** | 8081 (0.0.0.0) |
| **运行目录** | `/home/ubuntu/gbrain` |
| **启动命令** | `/home/ubuntu/gbrain/venv/bin/python api_server.py` |
| **资源限制** | MemoryMax=512M, CPUQuota=100% |
| **运行时间** | 约 11 小时 (自 2026-06-04 21:30) |

### 1.2 技术架构

```
GBrain Light API v1.0.0
├── 框架: Flask 3.1.3
├── 存储: 本地 Markdown 文件 (/home/ubuntu/gbrain/{category}/*.md)
├── 索引: 内存索引 (load_index() 加载所有 .md 文件)
└── 分类: people, companies, concepts, projects, originals, ideas, deals, decisions, reviews
```

### 1.3 API 端点

| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| `/api/v1/health` | GET | 健康检查 | ✅ |
| `/api/v1/stats` | GET | 统计信息 | ✅ |
| `/api/v1/search?q=` | GET | 全文搜索 | ✅ |
| `/api/v1/get/<path:slug>` | GET | 获取页面 | ✅ **已修复** |
| `/api/v1/put` | POST | 写入/更新页面 | ✅ |
| `/api/v1/timeline/<path:slug>` | POST | 添加时间线 | ✅ |
| `/api/v1/sync` | POST | 触发索引同步 | ✅ |

### 1.4 当前数据

| 分类 | 文件数 |
|------|--------|
| projects | 3 |
| decisions | 1 |
| reviews | 3 |
| 其他 | 0 |
| **总计** | **7 个有效文件** |

**projects 目录内容**:
- `pi-agent.md` — Pi Agent 多智能体协同开发系统
- `gbrain-sync.md` — GBrain 跨设备同步方案
- `gbrain-deployment.md` — GBrain 部署记录

**decisions 目录内容**:
- `2026-06-05-001.md` — COS 私有桶迁移决策记录

**reviews 目录内容**:
- `self-approving-night-task-2026-06-04.md`
- `self-approving-cos-migration-2026-06-05.md`
- `cos-private-bucket-test-2026-06-05.md`

### 1.5 ⚠️ 发现的 Bug 及修复

**问题**: `/api/v1/get/<slug>` 和 `/api/v1/timeline/<slug>` 路由无法处理包含 `/` 的 slug（如 `projects/pi-agent`），Flask 默认 `<slug>` 转换器不包含 `/`。

**修复**: 将 `<slug>` 改为 `<path:slug>`，重启服务后验证通过。

```diff
- @app.route('/api/v1/get/<slug>')
+ @app.route('/api/v1/get/<path:slug>')

- @app.route('/api/v1/timeline/<slug>', methods=['POST'])
+ @app.route('/api/v1/timeline/<path:slug>', methods=['POST'])
```

**修复时间**: 2026-06-05 08:45  
**验证**: `curl http://100.92.38.117:8081/api/v1/get/projects/pi-agent` ✅ 返回完整内容

### 1.6 GBrain 集成规则（来自 pi-agent.md）

1. **gbrainFirst**: 所有 Agent 必须在任务开始前查询 GBrain
2. **recordEverything**: 所有决策、发现、变更必须记录到 GBrain
3. **syncAfterWrite**: 写入 GBrain 后必须执行 sync
4. **selfApproving**: 所有 Agent 必须在任务完成后触发自省
5. **autoSelfApproving**: 每次任务完成后自动自省并存储

---

## 二、服务器系统概况

| 项目 | 详情 |
|------|------|
| **主机名** | VM-0-5-ubuntu |
| **系统** | Ubuntu 24.04.4 LTS (Noble Numbat) |
| **内核** | 6.8.0-111-generic |
| **运行时间** | 26 天 12 小时 |
| **CPU** | 4 核 |
| **内存** | 3.6GB (已用 2.1GB, 可用 1.5GB) |
| **磁盘** | 40GB (已用 26GB, 可用 13GB, **68%**) |
| **Tailscale IP** | 100.92.38.117 |
| **公网 IP** | 124.222.122.217 |

---

## 三、运行服务全景

### 3.1 Systemd 服务

| 服务 | 状态 | 说明 |
|------|------|------|
| `gbrain-api.service` | ✅ running | GBrain Light API Server (8081) |
| `ai-photo-template-miniapp.service` | ✅ running | AI Photo Template API (3200) |
| `evercore.service` | ✅ running | EverCore Memory System (1995) ⚠️ 端口关闭 |
| `fengvoice-api.service` | ✅ running | FengVoice FastAPI (8100) |
| `kimi-cloudops.service` | ✅ running | Kimi CloudOps Agent |
| `tailscaled.service` | ✅ running | Tailscale 节点代理 |
| `nginx.service` | ✅ running | 反向代理 (80/443) |
| `docker.service` | ✅ running | Docker 容器引擎 |
| `shadowsocks-libev.service` | ✅ running | Shadowsocks 代理 |
| `fail2ban.service` | ✅ running | 入侵防护 |

### 3.2 Docker 容器

| 容器名 | 镜像 | 状态 | 端口 |
|--------|------|------|------|
| `memsys-milvus-etcd` | etcd:v3.5.5 | ✅ healthy | 2379-2380 |
| `memsys-elasticsearch` | elasticsearch:8.11.0 | ✅ healthy | 19200, 19300 |
| `memsys-milvus-standalone` | milvus:v2.5.2 | ✅ healthy | 19530, 9091 |
| `memsys-redis` | redis:7.2-alpine | ✅ healthy | 6381 (127.0.0.1) |
| `memsys-mongodb` | mongo:7.0 | ✅ healthy | 27017 |
| `memsys-milvus-minio` | minio:latest | ✅ healthy | 9000-9001 |
| `prajna-api` | prajna-theater-prajna-api | ✅ healthy | 2054→8000 |
| `prajna-frontend` | nginx:1.25-alpine | ✅ running | 80, 443 |
| `trendrader-redis` | redis:6.2-alpine | ✅ running | 6380 |
| `tina-worker-img` | tina-worker-img | ✅ running | - |
| `redis-local` | redis:6.2-alpine | ✅ running | 6379 (127.0.0.1) |
| `finsight-backend` | tina-finsight-backend | ✅ healthy | 8000 |
| `finsight-nginx` | nginx:1.25-alpine | ✅ running | 2053 |

### 3.3 端口扫描结果

| 端口 | 服务 | 状态 | 备注 |
|------|------|------|------|
| 8081 | GBrain API | ✅ OPEN | 已修复路由 bug |
| 3200 | AI Photo Template | ✅ OPEN | Sensenova dry_run=false |
| 1995 | EverCore | ❌ CLOSED | ⚠️ 服务可能已停止或绑定 127.0.0.1 |
| 80 | Nginx HTTP | ✅ OPEN | 301 → HTTPS |
| 443 | Nginx HTTPS | ✅ OPEN | |
| 27017 | MongoDB | ✅ OPEN | |
| 6379 | Redis | ❌ CLOSED | 绑定 127.0.0.1 (容器内) |
| 19530 | Milvus | ✅ OPEN | |
| 19200 | Elasticsearch | ✅ OPEN | |
| 9000 | MinIO | ✅ OPEN | |

---

## 四、AI Photo Template Miniapp 状态

| 项目 | 详情 |
|------|------|
| **服务名** | `ai-photo-template-miniapp.service` |
| **端口** | 3200 |
| **健康检查** | ✅ `/health` 返回 `{ok: true, provider: sensenova, dry_run: false}` |
| **AI 提供商** | Sensenova (商汤) |
| **Dry Run** | false (生产模式) |

---

## 五、待办事项

### 5.1 GBrain 相关

- [x] 修复 `/api/v1/get/<slug>` 路由 bug（已修复）
- [x] 本地项目添加 TypeScript GBrain 客户端 (`src/services/gbrainClient.ts`)
- [x] 本地项目添加 Python 批量同步工具 (`scripts/gbrain_sync.py`)
- [x] 配置 `appConfig.ts` 集成 GBrain 配置
- [x] 更新 `.env.example` 添加 GBrain 环境变量
- [ ] 在工作流中实际调用 GBrain 客户端（待集成到 `generatePromptWorkflow.ts` 等）
- [ ] 添加 GBrain 客户端集成测试

### 5.2 服务器维护

- [ ] 排查 EverCore (1995) 端口关闭问题
- [ ] 磁盘空间监控（当前 68%，建议设置告警）
- [ ] EverCore 完整备份（P0）
- [ ] Docker 卷备份（P0）

---

## 六、GBrain 使用示例

### 6.1 搜索知识

```bash
curl "http://100.92.38.117:8081/api/v1/search?q=pi-agent"
```

### 6.2 获取页面

```bash
curl "http://100.92.38.117:8081/api/v1/get/projects/pi-agent"
```

### 6.3 写入页面

```bash
curl -X POST http://100.92.38.117:8081/api/v1/put \
  -H "Content-Type: application/json" \
  -d '{"slug": "projects/my-project", "content": "# My Project\\n\\nContent here"}'
```

### 6.4 添加时间线

```bash
curl -X POST http://100.92.38.117:8081/api/v1/timeline/projects/pi-agent \
  -H "Content-Type: application/json" \
  -d '{"summary": "执行了服务器巡检"}'
```

### 6.5 同步索引

```bash
curl -X POST http://100.92.38.117:8081/api/v1/sync
```

---

**巡检完成时间**: 2026-06-05 08:50 CST
