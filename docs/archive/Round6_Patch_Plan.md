# Round 6 Patch Plan

> 目标：补齐缺失路由 `GET /images/{id}` 和 `DELETE /images/{id}`
> 文件数：3

---

## 文件 1：backend/routers/cos_serve.py

**新增两个端点**：

```python
@router.get("/images/{image_id}")
def get_image(image_id: int, db: Session = Depends(get_db)):
    """Get a single image record by ID."""
    img = db.query(Image).filter(Image.id == image_id).first()
    if not img:
        raise HTTPException(status_code=404, detail=f"Image {image_id} not found")
    
    cos_key = img.source_id or ""
    if img.source == "mock":
        image_url = img.thumbnail_url or "/placeholder.svg"
        thumbnail_url = img.thumbnail_url or "/placeholder.svg"
    else:
        image_url = f"/cos/image/{cos_key}" if cos_key else None
        thumbnail_url = f"/cos/image/{cos_key}" if cos_key else None
    
    return {
        "id": img.id,
        "title": img.title,
        "prompt": img.prompt,
        "revised_prompt": img.revised_prompt,
        "image_url": image_url,
        "thumbnail_url": thumbnail_url,
        "created_at": img.created_at.isoformat() if img.created_at else None,
        "tags": img.tags or [],
        "source": img.source,
    }


@router.delete("/images/{image_id}")
def delete_image(image_id: int, db: Session = Depends(get_db)):
    """Delete an image record by ID."""
    img = db.query(Image).filter(Image.id == image_id).first()
    if not img:
        raise HTTPException(status_code=404, detail=f"Image {image_id} not found")
    db.delete(img)
    db.commit()
    return {"deleted": True, "id": image_id}
```

---

## 文件 2：src/server/httpServer.ts

**新增代理路由**（在 `/images/recent` 之后）：

```typescript
// Dynamic /images/{id} for GET and DELETE
const imagesIdMatch = url.pathname.match(/^\/images\/(\d+)$/);
if (imagesIdMatch && ["GET", "DELETE"].includes(method)) {
    const imageId = imagesIdMatch[1];
    await proxyToFastAPI(request, response, method, `/images/${imageId}`, url.search);
    return;
}
```

---

## 文件 3：public/app.js

**3 处路径修改**：

```javascript
// L742: 复制提示词
const data = await api(`/images/${encodeURIComponent(result.task_id)}`);
// 取 revised_prompt:
if (data.revised_prompt) { ... }

// L780: loadTaskPrompt
const data = await api(`/images/${encodeURIComponent(taskId)}`);
if (data.revised_prompt) { ... }

// L847: deleteTask
const resp = await api(`/images/${encodeURIComponent(taskId)}`, { method: 'DELETE' });
```

**注意**：前端原调用 `/tasks/${id}/prompt`（带 `/prompt` 后缀），改为 `/images/${id}` 后，从返回体中取 `revised_prompt` 字段。

---

## 验收测试

```bash
# 1. 启动后端
uvicorn backend.main:app --port 8001

# 2. 启动前端
npm run api

# 3. 生成一条记录（mock）
curl -X POST http://localhost:3000/generate \
  -H "Content-Type: application/json" \
  -d '{"template_id": "ancient_diaochan"}'

# 4. 获取单条记录
curl http://localhost:3000/images/1

# 5. 删除记录
curl -X DELETE http://localhost:3000/images/1
```

---

## 变更摘要

| 文件 | 新增 | 修改 | 删除 |
|---|---|---|---|
| `cos_serve.py` | 2 个端点（~35 行） | 0 | 0 |
| `httpServer.ts` | 1 段代理（~6 行） | 0 | 0 |
| `app.js` | 0 | 3 处路径（~3 行） | 0 |
