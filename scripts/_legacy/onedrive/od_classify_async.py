import json, os, time, asyncio, aiohttp, cv2, numpy as np

TOKEN_FILE = "D:/Projects/ai-photo-template-miniapp/onedrive_token.json"
IMAGES_FILE = "D:/Projects/ai-photo-template-miniapp/onedrive_images.json"
PROGRESS_FILE = "D:/Projects/ai-photo-template-miniapp/od_progress2.txt"
RESULT_FILE = "D:/Projects/ai-photo-template-miniapp/od_classify_result.json"
CONCURRENT = 10  # parallel downloads

with open(TOKEN_FILE) as f:
    tok = json.load(f)
with open(IMAGES_FILE, encoding="utf-8") as f:
    all_images = json.load(f)

cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
total = len(all_images)
to_delete, to_keep, errors = [], [], []

def log(msg):
    with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

def detect_face(img_bytes):
    arr = np.frombuffer(img_bytes, np.uint8)
    cv_img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if cv_img is None:
        return None
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
    return len(faces) > 0

async def classify_one(session, img, sem):
    async with sem:
        img_id = img["id"]
        img_name = img["name"]
        try:
            # Try thumbnail first
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{img_id}/thumbnails/0/small/content"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    has_face = detect_face(data)
                    if has_face is not None:
                        return ("keep" if has_face else "delete", img)
                
                # Fallback: full image
                url2 = f"https://graph.microsoft.com/v1.0/me/drive/items/{img_id}/content"
                async with session.get(url2, timeout=aiohttp.ClientTimeout(total=30)) as resp2:
                    if resp2.status == 200:
                        data = await resp2.read()
                        has_face = detect_face(data)
                        if has_face is not None:
                            return ("keep" if has_face else "delete", img)
            
            return ("error", {"id": img_id, "name": img_name, "error": f"http_{resp.status}"})
        except Exception as e:
            return ("error", {"id": img_id, "name": img_name, "error": str(e)[:60]})

async def main():
    sem = asyncio.Semaphore(CONCURRENT)
    access_token = tok["access_token"]
    
    async with aiohttp.ClientSession(headers={"Authorization": f"Bearer {access_token}"}) as session:
        tasks = [classify_one(session, img, sem) for img in all_images]
        processed = 0
        start = time.time()
        
        log(f"Async classification of {total} images (concurrency={CONCURRENT})")
        
        for coro in asyncio.as_completed(tasks):
            result = await coro
            kind, data = result
            processed += 1
            
            if kind == "keep":
                to_keep.append(data)
            elif kind == "delete":
                to_delete.append(data)
            else:
                errors.append(data)
            
            if processed % 100 == 0 or processed == total:
                elapsed = int(time.time() - start)
                pct = processed / total * 100
                rate = processed / elapsed if elapsed > 0 else 0
                remaining = (total - processed) / rate if rate > 0 else 0
                est_str = f"{int(remaining//60)}m{int(remaining%60)}s" if remaining < 3600 else f"{int(remaining//3600)}h{int(remaining%3600//60)}m"
                log(f"{processed}/{total} ({pct:.0f}%) {elapsed//60}m{elapsed%60}s | Est: {est_str} | Keep:{len(to_keep)} Del:{len(to_delete)} Err:{len(errors)}")
                
                # Checkpoint every 500
                if processed % 500 == 0:
                    with open("D:/Projects/ai-photo-template-miniapp/od_checkpoint2.json", "w") as f:
                        json.dump({"i": processed, "keep": len(to_keep), "del": len(to_delete), "err": len(errors)}, f)
    
    # Save results
    result = {
        "total": total,
        "to_keep": [{"id": k["id"], "name": k["name"], "path": k.get("_path","")} for k in to_keep],
        "to_delete": [{"id": d["id"], "name": d["name"], "path": d.get("_path",""), "size": d.get("size",0)} for d in to_delete],
        "errors": errors[:50],
        "to_keep_count": len(to_keep),
        "to_delete_count": len(to_delete),
    }
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    elapsed = int(time.time() - start)
    sz = sum(d.get("size",0) for d in to_delete)
    log(f"\nDONE in {elapsed//60}m{elapsed%60}s")
    log(f"Keep: {len(to_keep)} | Delete: {len(to_delete)} ({sz/1024/1024:.1f}MB) | Errors: {len(errors)}")

asyncio.run(main())
