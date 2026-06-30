# 模板系统设计

每个模板使用 JSON 管理。

## 核心字段

```json
{
  "template_id": "ancient_diaochan",
  "category": "古风美女",
  "title": "三国貂蝉",
  "version": "1.0.0",
  "ratio": "4:5",
  "face_lock": true,
  "style": "真人古风写真",
  "prompt_blocks": {
    "subject": "",
    "face": "",
    "clothing": "",
    "scene": "",
    "lighting": "",
    "camera": "",
    "quality": "",
    "commercial_use": ""
  },
  "options": {
    "quality": "high",
    "face_strength": 0.75
  },
  "negative_prompt": []
}
```

## Prompt 拼接顺序

```text
用户头像保持
+ 模板角色身份
+ 脸部保真
+ 服装
+ 场景
+ 光影
+ 构图
+ 画质
+ 安全约束
```
