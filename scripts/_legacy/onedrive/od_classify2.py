import json, requests, os, time, cv2, numpy as np

TOKEN_FILE = "D:/Projects/ai-photo-template-miniapp/onedrive_token.json"
IMAGES_FILE = "D:/Projects/ai-photo-template-miniapp/onedrive_images.json"
PROGRESS_FILE = "D:/Projects/ai-photo-template-miniapp/od_progress.txt"
RESULT_FILE = "D:/Projects/ai-photo-template-miniapp/od_classify_result.json"

with open(TOKEN_FILE) as f:
    t = json.load(f)
with open(IMAGES_FILE, encoding="utf-8") as f:
    all_images = json.load(f)

headers = {"Authorization": f"Bearer {t['access_token']}"}
cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
total = len(all_images)
to_delete, to_keep, errors = [], [], []
start = time.time()

def log(msg):
    with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

log(f"Starting classification of {total} images at {time.ctime()}")
log("i/total, pct, elapsed, keep, del, err")

for i, img in enumerate(all_images):
    img_id = img["id"]
    img_name = img["name"]
    has_face = None
    
    try:
        url = f"https://graph.microsoft.com/v1.0/me/drive/items/{img_id}/thumbnails/0/small/content"
        resp = requests.get(url, headers=headers, timeout=15)
        
        for attempt in range(2):
            try:
                data = resp.content if resp.status_code == 200 else None
                if not data:
                    url2 = f"https://graph.microsoft.com/v1.0/me/drive/items/{img_id}/content"
                    resp = requests.get(url2, headers=headers, timeout=30)
                    data = resp.content if resp.status_code == 200 else None
                if data:
                    arr = np.frombuffer(data, np.uint8)
                    cv_img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    if cv_img is not None:
                        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                        faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
                        has_face = len(faces) > 0
                    break
            except:
                continue
        
    except Exception as e:
        errors.append({"id": img_id, "name": img_name, "error": str(e)})
        continue
    
    if has_face is None:
        errors.append({"id": img_id, "name": img_name, "error": "no_data"})
    elif has_face:
        to_keep.append(img)
    else:
        to_delete.append(img)
    
    if (i + 1) % 100 == 0 or i == total - 1:
        elapsed = int(time.time() - start)
        pct = (i+1)/total*100
        log(f"{i+1}/{total}, {pct:.0f}%, {elapsed//60}m{elapsed%60}s, {len(to_keep)}, {len(to_delete)}, {len(errors)}")
        # Save checkpoint every 500
        if (i + 1) % 500 == 0:
            checkpoint = {"i": i, "to_keep": len(to_keep), "to_delete": len(to_delete), "errors": len(errors)}
            with open("D:/Projects/ai-photo-template-miniapp/od_checkpoint.json", "w") as f:
                json.dump(checkpoint, f)

# Final save
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
size_del = sum(d.get("size",0) for d in to_delete)
log(f"\nDONE in {elapsed//60}m{elapsed%60}s")
log(f"Keep: {len(to_keep)}, Delete: {len(to_delete)} ({size_del/1024/1024:.1f}MB), Errors: {len(errors)}")
