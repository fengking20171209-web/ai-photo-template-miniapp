import json, time, asyncio, aiohttp

TOKEN_FILE = "D:/Projects/ai-photo-template-miniapp/onedrive_token.json"
RESULT_FILE = "D:/Projects/ai-photo-template-miniapp/od_classify_result.json"
ALL_IMAGES = "D:/Projects/ai-photo-template-miniapp/onedrive_images.json"
PROGRESS_FILE = "D:/Projects/ai-photo-template-miniapp/od_cleanup_progress.txt"
CONCURRENT = 5

def log(msg):
    with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

# Load results
with open(RESULT_FILE, encoding="utf-8") as f:
    result = json.load(f)

with open(ALL_IMAGES, encoding="utf-8") as f:
    all_images = json.load(f)

to_delete_ids = {x["id"] for x in result["to_delete"]}
error_ids = {x["id"] for x in result["errors"]}
keep_ids = {x["id"] for x in result["to_keep"]}

log(f"Delete: {len(to_delete_ids)}, Keep: {len(keep_ids)}, Retry errors: {len(error_ids)}")

# Get fresh token
with open(TOKEN_FILE) as f:
    token = json.load(f)

async def refresh_token_if_needed(session, token_data, start_time):
    if time.time() - start_time > 3000:  # ~50 min
        resp = requests.post(
            "https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
            data={
                "client_id": "14d82eec-204b-4c2f-b7e8-296a70dab67e",
                "grant_type": "refresh_token",
                "refresh_token": token_data["refresh_token"],
                "scope": "Files.ReadWrite.All offline_access User.Read",
            },
        )
        result2 = resp.json()
        if "access_token" in result2:
            token_data.update(result2)
            with open(TOKEN_FILE, "w") as f:
                json.dump(token_data, f)
            session._default_headers["Authorization"] = f"Bearer {result2['access_token']}"
            log("Token refreshed")
            return time.time()
    return start_time

async def delete_images(session, ids, label):
    deleted = 0
    failed = 0
    sem = asyncio.Semaphore(CONCURRENT)
    
    async def delete_one(img_id):
        nonlocal deleted, failed
        async with sem:
            try:
                url = f"https://graph.microsoft.com/v1.0/me/drive/items/{img_id}"
                async with session.delete(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status in (204, 200, 202):
                        return True
                    else:
                        return False
            except:
                return False
    
    tasks = [delete_one(rid) for rid in ids]
    done = 0
    for coro in asyncio.as_completed(tasks):
        ok = await coro
        if ok:
            deleted += 1
        else:
            failed += 1
        done += 1
        if done % 200 == 0:
            log(f"{label}: {done}/{len(ids)} - Deleted: {deleted}, Failed: {failed}")
    
    return deleted, failed

async def retry_classify(session, ids, all_map):
    """Retry classification of error images"""
    import cv2, numpy as np
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    sem = asyncio.Semaphore(CONCURRENT)
    new_delete = []
    new_keep = []
    still_errors = []
    
    async def check_one(img_id):
        async with sem:
            img = all_map.get(img_id, {})
            try:
                url = f"https://graph.microsoft.com/v1.0/me/drive/items/{img_id}/content"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        arr = np.frombuffer(data, np.uint8)
                        cv_img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                        if cv_img is not None:
                            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                            faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
                            return (img_id, "keep" if len(faces) > 0 else "delete")
            except:
                pass
            return (img_id, "error")
    
    tasks = [check_one(eid) for eid in ids]
    done = 0
    for coro in asyncio.as_completed(tasks):
        img_id, verdict = await coro
        done += 1
        if verdict == "delete":
            new_delete.append(img_id)
        elif verdict == "keep":
            new_keep.append(img_id)
        else:
            still_errors.append(img_id)
        if done % 50 == 0:
            log(f"Retry: {done}/{len(ids)} - Delete: {len(new_delete)}, Keep: {len(new_keep)}, Still err: {len(still_errors)}")
    
    return new_delete, new_keep, still_errors

async def main():
    start_token_time = time.time()
    
    async with aiohttp.ClientSession(headers={"Authorization": f"Bearer {token['access_token']}"}) as session:
        # Step 1: Delete confirmed non-people images (2043)
        log(f"\n=== Step 1: Deleting {len(to_delete_ids)} non-people images ===")
        del_start = time.time()
        deleted, failed = await delete_images(session, list(to_delete_ids), "Delete")
        log(f"Delete done: {deleted} deleted, {failed} failed in {int((time.time()-del_start)//60)}m")
        
        # Step 2: Retry error images (388)
        if error_ids:
            log(f"\n=== Step 2: Retrying {len(error_ids)} error images ===")
            all_map = {x["id"]: x for x in all_images}
            new_delete, new_keep, still_errors = await retry_classify(session, error_ids, all_map)
            log(f"Retry done: Delete: {len(new_delete)}, Keep: {len(new_keep)}, Still err: {len(still_errors)}")
            
            # Delete newly classified non-people
            if new_delete:
                log(f"\n=== Step 3: Deleting {len(new_delete)} retried non-people images ===")
                del2, fail2 = await delete_images(session, new_delete, "Retry-Delete")
                log(f"Retry delete done: {del2} deleted, {fail2} failed")
    
    log(f"\n=== COMPLETE ===")

asyncio.run(main())
