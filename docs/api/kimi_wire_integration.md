# Kimi Wire Integration

## 定位

Wire 是 Kimi Code CLI 的底层 JSON-RPC 通信协议。它适合做自定义 UI、自动化测试、IDE 集成和长期任务控制。

对本项目来说，Wire 不是第一阶段生图链路的必需项。当前更推荐的调用顺序是：

```text
本地 CLI / Kimi Agent
→ 项目 Skill
→ 本地插件工具
→ 模板系统
→ mock 生图任务
```

Wire 应放在后续阶段使用，用来把 Kimi Agent 嵌入到我们自己的管理后台、桌面工具或测试流水线里。

## 什么时候使用 Wire

适合：

- 做一个项目专用 Agent 控制台
- 自动化测试 Kimi Agent 的行为
- 在小程序后台管理端嵌入“模板助手”
- 把审批、工具调用、任务事件做成可视化面板
- 捕获 Agent 的中间事件，例如工具调用、审批请求、子 Agent 事件

不适合：

- 简单生成 Prompt
- 简单列出模板
- 简单跑 smoke test
- 普通人工对话

这些场景用 `kimi --print`、`kimi` 交互模式、项目插件或 PowerShell 脚本更简单。

## 推荐分阶段接入

### Phase 1：只做握手验证

目标：确认 `kimi --wire` 可以启动，并能返回 `initialize` 响应。

命令：

```powershell
$env:Path = "C:\Users\Aerc\.local\bin;$env:Path"
uv run python scripts\kimi_wire_smoke.py
```

该命令不会发送 `prompt`，通常不会触发模型推理。

### Phase 2：做自动化 Agent 测试

目标：通过 Wire 发送固定 prompt，检查 Agent 是否能：

- 读取项目规则
- 调用正确工具
- 输出预期格式
- 避免真实生图 API 调用

示例：

```powershell
uv run python scripts\kimi_wire_smoke.py --prompt "只回复 OK"
```

注意：发送 `prompt` 会消耗 Kimi 额度。

### Phase 3：接入内部控制台

目标：在 Web 管理台里展示 Agent 事件流。

需要处理：

- `event`: 内容输出、工具调用、状态更新
- `request`: 审批请求、外部工具调用、结构化问答
- `cancel`: 用户中断任务
- `steer`: 用户在 Agent 运行中追加指令
- `set_plan_mode`: 开关计划模式

## 当前建议

当前项目还处在本地模板系统阶段，Wire 暂时只作为“技术预埋”。短期不建议把主流程绑定到 Wire，否则会过早增加复杂度。

更稳的路线：

```text
先把模板质量、Prompt 拼接、任务记录、mock 生图、文档 SOP 做扎实
→ 再接真实图像 API
→ 再做后台管理端
→ 最后考虑 Wire 控制台和自动化 Agent 测试
```

## 安全边界

Wire Client 必须处理审批请求，不应默认自动批准高风险操作。

建议策略：

- 文件读取：可自动允许
- 生成文档：可自动允许
- 文件写入：需要用户确认或限定目录
- Shell 命令：需要白名单
- 删除、移动、真实 API 调用：默认阻止
- API Key、OAuth token：永不写入日志或前端

## 与本项目已有能力的关系

| 能力 | 当前状态 | 是否依赖 Wire |
| --- | --- | --- |
| 模板 JSON 管理 | 已完成 | 否 |
| Prompt 拼接 | 已完成 | 否 |
| mock 生图任务 | 已完成 | 否 |
| Kimi 项目 Skill | 已完成 | 否 |
| Kimi 本地插件 | 已完成 | 否 |
| Kimi 项目 Agent | 已完成 | 否 |
| Agent 自动化测试 | 待做 | 可选 |
| 自定义 Agent 控制台 | 待做 | 是 |

