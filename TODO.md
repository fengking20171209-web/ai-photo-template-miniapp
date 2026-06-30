# 待办事项 — AI Fashion Reference Asset Library
## 更新日期：2026-05-30

## [x] 已完成
1. FastAPI 后端 SQLite 适配 ✅
2. COS STS 临时凭证服务 ✅
3. OneDrive 清理完成：2436 张非人物图片删除，释放 4.3 GB ✅
4. SenseTime 商汤生图 API 接入（prompt 优化+生图+COS 上传管线）✅
5. COS 图片代理端点 ✅
6. 模板 API（/api/templates, /api/templates/{id}）✅
7. 前端 SPA 完整重写（三标签页：生成/作品集/上传，连接 FastAPI）✅
8. 参考图批量上传完成（26 条索引，face/ 目录 9 张全部上传）✅
9. 模板系列完善：SIUF 2026（25个）+ 肚兜（5个）+ 新中式概念（1个）= 共 37 个模板 ✅

## [ ] 待完成
### 高优先级
1. 前端细调（浏览器视觉验证 + 样式微调）
2. COS 防盗链配置 → 需登录腾讯云控制台手动操作（见 scripts/cos_hotlink_guide.py）
3. 生成图 gallery 完善（点击大图查看、删除功能）

### 中优先级
4. iPhone 快捷指令（选照片→存本地→触发生成）
5. TypeScript 模板引擎完善（从 JSON 模板自动组装 prompt）
6. COS CDN 加速配置

### 低优先级
7. OneDrive 清理技能后续优化
8. 百度网盘同步自动化
9. FastAPI 后端生产部署（PostgreSQL + 密钥管理）
