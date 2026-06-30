# 自省触发器系统（IntrospectionTrigger）设计规格

> **目标：** 实现 GBrain 多 Agent 工作流中的自动自省机制，支持任务完成、失败、Prompt 质量评分等触发器的自动自省和修正。

---

## 1. 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Coordinator (协调器)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Generator│  │ Reviewer │  │Introspect│  │ Syncer   │        │
│  │  生成器  │  │  审查器  │  │   自省器  │  │  同步器  │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       │             │             │             │               │
│       └─────────────┴──────┬──────┴─────────────┘               │
│                            │                                    │
│                    ┌───────▼───────┐                            │
│                    │   EventBus    │                            │
│                    │  (事件总线)    │                            │
│                    └───────┬───────┘                            │
│                            │                                    │
│       ┌────────────────────┼────────────────────┐              │
│       ▼                    ▼                    ▼              │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐           │
│  │ 触发器1  │       │ 触发器2  │       │ 触发器3  │           │
│  │任务完成  │       │ 任务失败 │       │Prompt质量│           │
│  └────┬─────┘       └────┬─────┘       └────┬─────┘           │
│       │                  │                  │                 │
│       └──────────────────┼──────────────────┘                 │
│                          ▼                                    │
│                  ┌──────────────┐                             │
│                  │ GBrain API   │                             │
│                  │ (timeline/sync)│                            │
│                  └──────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Agent 角色定义

| 角色 | 职责 | 状态流转 |
|------|------|----------|
| **Coordinator** | 统一调度所有 Agent 和触发器，管理事件流 | idle → introspecting → approving → idle |
| **Generator** | 负责 prompt 生成和图像生成 | idle → working → completed/error → idle |
| **Reviewer** | 审查 prompt 质量和生成结果 | idle → reviewing → approved/rejected → idle |
| **Introspector** | 执行自省分析和修正建议 | idle → introspecting → approved/rejected → idle |
| **Syncer** | 负责与 GBrain 同步数据 | idle → syncing → idle |

---

## 3. 触发器配置

### 3.1 触发器类型

| 类型 | 标识 | 触发条件 | 优先级 |
|------|------|----------|--------|
| **任务完成** | `auto-self-approving` | 任务状态变为 `completed` | 1 |
| **任务失败** | `failure-introspection` | 任务状态变为 `failed` 或发生异常 | 0 |
| **Prompt 质量** | `prompt-quality-check` | Prompt 质量评分低于阈值（默认 70） | 2 |
| **手动触发** | `manual` | 显式调用触发自省 | 3 |

### 3.2 触发器配置结构

```typescript
interface TriggerConfig {
  id: string;              // 触发器唯一标识
  type: TriggerType;       // 触发器类型
  condition: string;       // 触发条件描述
  threshold?: {            // 阈值配置（用于量化触发器）
    value: number;
    operator: "less_than" | "greater_than" | "equals" | "between";
    upperBound?: number;
  };
  actions: TriggerAction[]; // 触发动作
  enabled: boolean;        // 是否启用
  priority: number;        // 优先级
  cooldownMs: number;      // 冷却时间
  maxRetries: number;      // 最大重试次数
  agentRole: AgentRole;    // 关联的 Agent 角色
}
```

### 3.3 触发动作

| 动作 | 说明 |
|------|------|
| `introspect` | 触发自省分析 |
| `correct` | 尝试自动修正 |
| `notify` | 通知 Coordinator |
| `rollback` | 回滚到上一个状态 |
| `sync_to_gbrain` | 同步到 GBrain |

---

## 4. Prompt 质量评分

### 4.1 评分维度

| 维度 | 权重 | 评分标准 |
|------|------|----------|
| **清晰度 (clarity)** | 25% | 主体、动作、环境描述是否明确 |
| **具体性 (specificity)** | 25% | 细节描述（材质、光影、色彩）是否充分 |
| **完整性 (completeness)** | 20% | 必要元素（风格、构图、光影、质量）是否齐全 |
| **风格一致性 (style_consistency)** | 15% | 风格描述是否一致，无冲突 |
| **负向提示词质量** | 15% | 负向提示词是否包含常见负面元素 |

### 4.2 评分阈值

| 分数范围 | 评级 | 触发行为 |
|----------|------|----------|
| ≥ 85 | 优秀 | 通过自省 |
| 70-84 | 良好 | 轻微自省，可选修正 |
| 50-69 | 一般 | 触发自省，建议修正 |
| < 50 | 较低 | 强制自省，需要修正 |

---

## 5. 自省结果处理

### 5.1 自省结果状态

| 状态 | 说明 | 后续操作 |
|------|------|----------|
| `passed` | 自省通过 | 标记为 approved，更新成功计数 |
| `needs_correction` | 需要修正 | 尝试自动修正（最多 3 次） |
| `needs_review` | 需要人工审查 | 发布 review_required 事件 |
| `rollback_needed` | 需要回滚 | 执行回滚操作 |

### 5.2 自省发现（Finding）

```typescript
interface IntrospectionFinding {
  description: string;      // 问题描述
  severity: "low" | "medium" | "high" | "critical";
  category: "prompt_quality" | "template_mismatch" | "parameter_error" | "output_quality" | "other";
  suggestedCorrection?: string;
  evidence?: string;
}
```

### 5.3 结果处理流程

```
自省完成
    │
    ▼
┌─────────────────┐
│ 检查 severity   │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼
 critical   high      medium      low
    │         │          │          │
    ▼         ▼          ▼          ▼
 rollback  correction  review?   passed
    │         │          │          │
    ▼         ▼          ▼          ▼
 回滚      修正       人工审查   通过
```

---

## 6. GBrain 集成

### 6.1 时间线记录

自省结果同步到 GBrain 时间线：

```
POST /api/v1/timeline/{slug}
{
  "summary": "[Introspection] Task task_ancient_diaochan_20260605010614: needs_correction",
  "details": {
    "introspectionId": "uuid",
    "taskId": "task_...",
    "status": "needs_correction",
    "findings": [...],
    "suggestions": [...],
    "durationMs": 1234,
    "timestamp": "2026-06-05T01:06:14.000Z"
  }
}
```

### 6.2 同步规则

| 规则 | 说明 |
|------|------|
| `gbrainFirst` | 任务开始前查询 GBrain 获取参考 |
| `recordEverything` | 所有自省结果记录到 GBrain |
| `syncAfterWrite` | 写入 GBrain 后执行 sync |
| `selfApproving` | 任务完成后触发自省 |
| `autoSelfApproving` | 自动自省并存储 |

---

## 7. 事件协议

### 7.1 事件类型

| 事件 | 说明 | 优先级 |
|------|------|--------|
| `task_started` | 任务开始 | 5 |
| `task_completed` | 任务完成 | 10 |
| `task_failed` | 任务失败 | 10 |
| `trigger_fired` | 触发器触发 | 5 |
| `introspection_started` | 自省开始 | 5 |
| `introspection_completed` | 自省完成 | 5 |
| `correction_applied` | 修正应用 | 3 |
| `rollback_started` | 回滚开始 | 8 |
| `rollback_completed` | 回滚完成 | 8 |
| `sync_to_gbrain` | 同步到 GBrain | 2 |
| `agent_state_changed` | Agent 状态变更 | 1 |
| `prompt_quality_scored` | Prompt 质量评分 | 3 |

### 7.2 事件结构

```typescript
interface AgentEvent {
  eventId: string;           // 事件唯一标识
  type: EventType;           // 事件类型
  sourceAgent: string;       // 来源 Agent
  targetAgent?: string;      // 目标 Agent
  timestamp: string;         // 时间戳
  payload: Record<string, unknown>; // 负载数据
  priority: number;          // 优先级
}
```

---

## 8. 集成方式

### 8.1 工作流集成（装饰器模式）

保持原有 workflow 函数签名不变，通过装饰器/包装器模式集成：

```typescript
// 原始 workflow
export async function runImageTaskWorkflow(config, templateId) { ... }

// 包装后的 workflow（集成自省）
export async function runImageTaskWorkflowWithIntrospection(config, templateId) {
  const coordinator = createCoordinator();
  
  await coordinator.handleTaskStarted(task);
  
  try {
    const result = await originalWorkflow(config, templateId);
    
    // 触发自省
    const triggerResult = coordinator.getIntrospectionTrigger()
      .evaluateTaskCompleted(result.task);
    
    if (triggerResult.triggered) {
      await coordinator.processIntrospectionResult(
        triggerResult.introspectionResult
      );
    }
    
    return result;
  } catch (error) {
    await coordinator.handleTaskFailed({ task, error });
    throw error;
  }
}
```

### 8.2 降级模式

当 `gbrainEnabled=false` 时，系统自动降级为本地模式：

```typescript
if (config.gbrainEnabled) {
  const gbrainClient = createGBrainClient();
  const coordinator = createCoordinator({}, gbrainClient);
} else {
  const coordinator = createCoordinator(); // 无 GBrain 同步
}
```

---

## 9. 文件结构

```
src/agents/
├── index.ts              # 模块入口
├── types.ts              # 类型定义
├── eventBus.ts           # 事件总线
├── introspectionTrigger.ts # 自省触发器
└── coordinator.ts        # 协调器

docs/superpowers/specs/
└── introspection-trigger-spec.md  # 本设计文档
```

---

## 10. 后续步骤

1. **集成测试**：编写 GBrain 客户端 mock 测试，验证触发器逻辑
2. **工作流集成**：将 Coordinator 集成到 `runImageTaskWorkflow` 和 `generatePromptWorkflow`
3. **CLI 支持**：在 CLI 脚本中添加自省触发选项
4. **API 支持**：在 HTTP Server 中添加自省状态查询端点
5. **监控面板**：添加自省结果统计和可视化

---

## 11. 验收标准

- [x] 定义触发器配置（触发条件、阈值、动作）
- [x] 实现任务完成触发器（autoSelfApproving）
- [x] 实现失败触发器
- [x] 实现 Prompt 质量评分触发器
- [x] 自省结果处理：记录到 GBrain timeline、生成修正建议、可选回滚
- [x] 自省触发器与 Agent 框架集成，由 Coordinator 统一调度
- [ ] 工作流集成（Phase 2）
- [ ] 集成测试（Phase 2）
