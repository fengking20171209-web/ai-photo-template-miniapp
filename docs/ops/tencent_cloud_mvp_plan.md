# 腾讯云部署版 AI 生图网站 MVP 技术方案

## 目标

先上线一个可访问、可演示、可继续扩展的 AI 写真模板网站。

MVP 不追求完整支付、小程序登录和真实生图扣费链路，优先跑通：

```text
模板列表
→ 模板详情
→ 创建 mock 生图任务
→ 查询任务状态
→ 查看生成 Prompt
```

## 推荐架构

```text
用户浏览器 / 抖音小程序 WebView
        ↓
Nginx HTTPS
        ↓
Node.js API 服务
        ↓
本地模板 JSON + output/tasks
        ↓
mock 生图 / 后续真实生图 API
```

## 腾讯云资源

第一阶段建议：

- CVM：2 核 2G 起步
- 系统：Ubuntu LTS
- Web 入口：Nginx
- Node 运行：Node.js LTS + PM2
- SSL：腾讯云免费证书或 Let’s Encrypt
- 图片存储：先本地 mock，后续迁移 COS

第二阶段再增加：

- PostgreSQL 或 TencentDB
- COS 对象存储
- Redis 队列
- 后台管理登录
- 支付与订单表

## 当前项目运行方式

本地启动 API：

```powershell
npm run api
```

默认端口：

```text
http://localhost:3000
```

默认生图模式：

```text
AI_IMAGE_PROVIDER=mock
AI_IMAGE_DRY_RUN=true
```

## MVP API

已落地接口：

```text
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

## 后续演进顺序

1. 增加前端页面：模板列表、详情、生成结果页。
2. 增加上传头像接口，先保存到 `uploads/`。
3. 把 mock 生图任务替换为真实 API dry-run 配置。
4. 增加任务持久化数据库。
5. 增加图库搜索 API。
6. 增加用户、订单、支付和高清图解锁。

## 当前不做

- 不接真实支付。
- 不默认调用真实生图 API。
- 不先做复杂图库搜索。
- 不先上 Figma 精修视觉稿。
- 不引入 PostgreSQL，避免提前增加部署成本。

