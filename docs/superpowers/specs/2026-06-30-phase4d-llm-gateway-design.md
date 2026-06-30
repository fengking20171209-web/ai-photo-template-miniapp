# Phase 4D：LLM/生图出站网关 设计规格

> **状态：DRAFT —— 待 Fred 审批后才进入实现。** 本文档由 Kiro 在授权自动推进期间起草，
> 遵守 superpowers:brainstorming 的"先设计后实现"红线：在你批准前不会编写任何 4D 实现代码。
> 文末列出**待你拍板的开放问题**。

**日期：** 2026-06-30
**分支建议：** `feature/phase4d-llm-gateway`(从当前 `feature/phase4-prompt-evolution-engine` 切出)
**作者：** Kiro(接管 Codex 后)

---

## 1. 目标(一句话)

在所有真实出站 AI 调用(生图 + 写真助手对话)前面，加一层统一网关，提供
**预算守卫、熔断、出站消毒、结构化错误与可观测性**，让接真实流量时可控、可见、可止损。

## 2. 当前状态评估(已有的"类网关"碎片)

| 能力 | 现状 | 位置 |
|---|---|---|
| 提供方分派 | 已有(agnes / sensenova) | `backend/routers/image_gen.py` |
| 出站生图调用 | 同步 `requests` | `agnes_image.full_pipeline` / `sense_image.full_pipeline` |
| 出站对话调用 | async `httpx`(SSE) | `backend/routers/chat.py` |
| 模型/密钥配置 | 已有(配置+ .env 回退，mtime 缓存) | `backend/services/model_config.py` |
| 提示词组装 | 已有(模板+用户词合并) | `backend/services/prompt_policy.py` |
| 失败处理 | 生图失败回退 mock 且**已透传 reason**；对话错误已脱敏 | 本轮加固完成 |
| SSRF/下载防护 | 已有(https+域名白名单、禁重定向、大小上限) | `local_storage` / `sense_image` |

**结论：** 已有"分派 + 配置 + 提示词 + 错误透传"。4D 要补的是**横切治理层**：预算、熔断、消毒、计量。

## 3. 范围

**做(In)：**
- 统一出站封装 `LLMGateway`，把 3 个出站点(agnes 生图 / sense 生图 / chat)收敛到一处治理。
- **预算守卫**：按"每日 / 每会话"限制调用次数与估算成本，超限拒绝并返回明确原因。
- **熔断器**：某提供方连续失败 N 次→打开熔断，冷却期内直接快速失败(回退 mock/提示)，避免雪崩与配额浪费。
- **出站消毒(Prompt Sanitizer)**：长度上限、控制字符剥离、注入式指令的防御性过滤(**纯防御**，与任何越狱提示词无关)。
- **计量与可观测**：每次调用记录 provider/模型/耗时/结果/估算 token，落 SQLite 表 + 结构化日志。

**不做(Out / YAGNI)：**
- 不引入 Celery/Redis/PostgreSQL(保持本地 SQLite + 进程内,符合既定轻量化方向)。
- 不做多租户、计费账单、分布式限流。
- 不改前端(public/ 由前端负责;网关仅在响应里多回 `gateway` 元信息供 UI 可选展示)。
- 不触碰被拒绝的越狱提示词相关需求。

## 4. 架构

```
路由层(image_gen / chat)
        │  调用
        ▼
   LLMGateway.execute(request)
        │
        ├─ 1. Sanitizer.clean(prompt)        # 长度/控制字符/注入防御
        ├─ 2. BudgetGuard.check(scope)       # 日/会话配额，超限→GatewayRejected
        ├─ 3. CircuitBreaker.allow(provider) # 打开则→GatewayShortCircuit
        ├─ 4. provider_call()                # 现有 full_pipeline / httpx，带超时
        ├─ 5. 记录用量(UsageRecord→SQLite)
        └─ 6. 更新熔断状态(成功/失败计数)
        ▼
   GatewayResult{ ok, data, reason, gateway_meta }
```

**单一职责拆分(便于隔离测试)：**
- `gateway/sanitizer.py` —— 纯函数,无 IO。
- `gateway/budget.py` —— 读/写计数(SQLite),纯逻辑可注入时钟。
- `gateway/circuit_breaker.py` —— 进程内状态机(closed/open/half-open),可注入时钟。
- `gateway/core.py` —— `LLMGateway` 编排上述 + provider 回调。
- `gateway/usage.py` —— `UsageRecord` 模型 + 写入。

## 5. 数据流与契约

**入参(统一)：**
```python
@dataclass
class GatewayRequest:
    kind: Literal["image", "chat"]
    provider: str                 # agnes | sensenova
    prompt: str | None            # 生图/对话文本(用于消毒与计量)
    scope_key: str                # 预算归属(如 "global" 或会话id)
    call: Callable[[], dict]      # 真正的 provider 调用(已绑定参数)
    est_cost: float = 1.0         # 估算成本单位
```

**出参(统一)：**
```python
@dataclass
class GatewayResult:
    ok: bool
    data: dict | None
    reason: str | None            # 失败/拒绝原因(已脱敏,可回前端)
    meta: dict                    # {provider, latency_ms, breaker_state, budget_left}
```

**集成点改动(实现期)：**
- `image_gen.generate_image`：把 `agnes_full_pipeline(...)` / `full_pipeline(...)` 包进 `gateway.execute(...)`；
  失败/拒绝→沿用现有 mock 回退并把 `reason` 透传(已就绪)。
- `chat.py`：在转发前 `sanitizer.clean` + `budget.check` + `breaker.allow`；上游错误计入熔断。

## 6. 错误处理

| 情形 | 行为 | 返回 |
|---|---|---|
| 预算超限 | 不调用上游 | `ok=false, reason="今日生成额度已用完(N/N)"` |
| 熔断打开 | 不调用上游 | `ok=false, reason="服务暂不可用,请稍后(熔断冷却中)"` |
| 上游异常 | 记失败、可能触发熔断 | `ok=false, reason=<脱敏>`;生图回退 mock |
| 消毒拒绝 | 不调用上游 | `ok=false, reason="输入不合规(过长/含非法字符)"` |
| 成功 | 记用量、重置失败计数 | `ok=true, data=...` |

## 7. 测试策略(TDD)

- **Sanitizer**:超长截断、控制字符剥离、保留正常中英文与标点。
- **BudgetGuard**:未超限放行;达上限拒绝;跨"天"重置(注入时钟)。
- **CircuitBreaker**:连续失败达阈值→open;冷却后→half-open;half-open 成功→closed,失败→open。
- **Gateway 编排**:消毒→预算→熔断→调用 顺序;任一拦截则不调用 provider(用 mock callable 断言未被调用)。
- **集成**:`/generate` 在预算超限时返回 mock + reason;`/chat` 在熔断打开时返回明确错误。
- 全部**离线**(不打真实 API),沿用现有 TestClient + monkeypatch 风格。

## 8. 待你拍板的开放问题

1. **预算口径**:按"每日总次数"够用，还是要区分 provider / 区分生图 vs 对话？默认建议:全局每日次数 + 每提供方每日次数双限。
2. **预算上限默认值**:生图/对话各默认多少次/天？(我先放配置项,默认偏宽松,如生图 200/天。)
3. **熔断阈值**:连续失败几次打开、冷却多久？默认建议:5 次 / 60s。
4. **消毒强度**:注入式指令过滤要多激进？默认建议:只做长度+控制字符+剥离明显的"system/ignore previous"类前缀,不做语义级审查(避免误杀正常创作描述)。
5. **用量是否要在 settings 页可视化**?(前端归 Codex,我只提供 `GET /api/gateway/usage` 数据端点。)

---

## 自检(规格)
- 占位符:无 TODO/待定。
- 一致性:契约(`GatewayRequest/Result`)与集成点、测试一致。
- 范围:单一计划可覆盖(网关+3 集成点),未混入无关重构。
- 模糊点:已集中到"开放问题"待决,默认值已给出。
