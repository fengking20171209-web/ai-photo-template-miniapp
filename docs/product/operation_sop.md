# Operation SOP

本文档定义本项目后续从“参考资料”到“可运行模板”的标准流程。目标是让每次新增模板都可追踪、可复用、可测试，而不是临时写一段 Prompt。

## 0. 工作目录

默认工作目录：

```text
D:\Projects\ai-photo-template-miniapp
```

百度网盘同步盘里的旧目录只作为备份，不作为主开发目录。

## 1. 每日启动检查

### 1.1 检查代理和 GitHub 速度

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check_network.ps1
```

期望结果：

- `127.0.0.1:10808` 可用。
- GitHub 经代理访问在数秒内完成。
- Git 全局代理保持为 `socks5h://127.0.0.1:10808`。

### 1.2 检查项目结构

```powershell
rg --files
```

重点确认：

- `templates/` 有模板 JSON。
- `references/` 有两个资料库。
- `src/` 有模板加载、Prompt 拼接、任务工作流。

## 2. 新模板生产流程

### 2.1 确定模板目标

先用一句话定义模板：

```text
给用户上传头像生成一张高级职业西装头像，适合 LinkedIn / 小红书 / 简历形象页。
```

必须明确：

- 用户是谁。
- 输出给谁看。
- 输出用在哪里。
- 画面是否需要文字。
- 是否需要保持脸部身份。

### 2.2 查参考资料

按场景选择参考文件：

| 模板方向 | 优先查阅 |
| --- | --- |
| 人像写真 | `references/awesome-gpt-image-2-API-and-Prompts/cases/portrait_zh-CN.md` |
| 商业海报 | `cases/poster_zh-CN.md`、`cases/ad-creative_zh-CN.md` |
| 产品图 | `cases/ecommerce_zh-CN.md` |
| UI / 社媒 | `cases/ui_zh-CN.md` |
| 角色卡 | `cases/character_zh-CN.md` |
| 精选玩法 | `references/awesome-gpt-image/README.zh-CN.md` |

只摘录结构，不直接复制整段案例。

### 2.3 拆解提示词模式

把参考案例拆成下面字段：

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

通用公式：

```text
[角色/身份] + [场景/任务] + [关键细节] + [风格/技术参数] + [安全边界]
```

### 2.4 编写模板 JSON

新增文件到：

```text
templates/<template_id>.json
```

命名规范：

```text
category_keyword.json
```

示例：

```text
career_lawyer.json
beauty_hair_analysis.json
poster_luxury_skincare.json
character_anime_expression_grid.json
```

模板必须符合：

- `template_id` 与文件名一致。
- `category` 只能使用已定义分类。
- `face_lock` 对人像类默认 `true`。
- `negative_prompt` 必填。
- 不写真实公众人物换脸模板。
- 不写暴露、低俗、擦边方向。

### 2.5 生成 Prompt

```bash
npm run generate <template_id>
```

输出：

```text
output/prompt.txt
output/task.json
```

### 2.6 运行 mock 生图任务

第一阶段先跑 mock，确认请求体、任务状态、输出文件都正确。

```bash
npm run image <template_id>
```

输出：

```text
output/prompt.txt
output/image_task.json
```

mock 模式不会请求真实 API，不会产生费用。

### 2.7 人工审查

检查 `output/prompt.txt`：

- 是否保留用户身份特征。
- 是否有完整服装和安全边界。
- 是否过度复杂。
- 是否存在容易生成错字的大段文字。
- 是否能用于商业图卡或模板商城。

检查 `output/task.json`：

- `status` 是否为 `api_reserved`。
- `will_call_api` 是否为 `false`。
- 请求体是否包含 prompt、negative_prompt、ratio、quality、face_strength。

检查 `output/image_task.json`：

- `status` 是否为 `completed`。
- `image_request.provider` 是否为 `mock`。
- `image_request.dry_run` 是否为 `true`。
- `image_response.raw.message` 是否显示没有真实调用。

## 3. 真实生图 API 接入流程

### 3.1 默认配置

`.env.example` 默认保持安全模式：

```text
AI_IMAGE_PROVIDER=mock
AI_IMAGE_DRY_RUN=true
```

### 3.2 切换到 HTTP API

确认供应商、URL、Key 后，创建本地 `.env`：

```text
AI_IMAGE_PROVIDER=http
AI_IMAGE_DRY_RUN=false
AI_IMAGE_API_URL=https://your-image-api.example.com/generate
AI_IMAGE_API_KEY=your_api_key
OUTPUT_DIR=output
```

再运行：

```bash
npm run image <template_id>
```

### 3.3 API 返回格式要求

当前适配层会自动识别以下图片字段：

```text
url
image_url
output_url
urls
image_urls
images
data
outputs
```

如果供应商返回格式不同，需要在 `src/services/aiImageService.ts` 的 `normalizeImageResponse` 中补充解析逻辑。

## 4. 模板升级流程

### 3.1 小改

适用：

- 改光影。
- 改服装。
- 改镜头。
- 加负面词。

流程：

```text
修改模板 JSON
↓
npm run generate <template_id>
↓
检查 output/prompt.txt
```

### 3.2 大改

适用：

- 换场景。
- 换商业定位。
- 改成新模板品类。
- 增加复杂排版或多图结构。

流程：

```text
查参考资料
↓
重新拆提示词模式
↓
新增模板 JSON
↓
保留旧模板
↓
生成并审查
```

不要直接覆盖旧模板，因为旧模板可能已经适合某一类用户。

## 5. 资料库更新流程

### 4.1 更新 EvoLinkAI 大库

```powershell
powershell -ExecutionPolicy Bypass -File scripts/download_reference_repo.ps1
```

### 4.2 更新 ZeroLu 精选库

```powershell
git -C references/awesome-gpt-image pull
```

如网络变慢，先确认代理：

```powershell
git config --global --get http.proxy
```

期望：

```text
socks5h://127.0.0.1:10808
```

## 6. 版本记录建议

每次新增模板时，在提交说明或工作记录里写：

```text
新增模板：career_lawyer
参考来源：portrait_zh-CN.md + ZeroLu 摄影案例
目标用途：职业头像 / 简历图卡
关键改动：强化棚拍光、真实皮肤、深色西装、干净背景
```

## 7. 安全审查规则

必须避免：

- 裸露、低俗、性暗示。
- 未成年人性感化。
- 真实公众人物身份滥用。
- 暴力、仇恨、违法场景。
- 医疗、法律、金融等高风险误导性承诺。
- 侵犯品牌 IP 的商用模板。

推荐替代：

- 高级写真。
- 职业形象。
- 国风造型。
- 商业海报。
- 角色设定。
- 信息图卡。

## 8. 周期性工作节奏

### 每天

- 选 1 个参考案例。
- 拆 1 个提示词模式。
- 优化或新增 1 个模板。

### 每周

- 形成 5-10 个可测试模板。
- 从输出 Prompt 中筛掉复杂、低质、不可商用方向。
- 更新 README 和模板清单。

### 每个阶段

- Phase 1：本地模板系统稳定。
- Phase 2：接入真实生图 API。
- Phase 3：增加小程序前端和模板商城。
- Phase 4：做付费、会员、商家定制和视频版。
