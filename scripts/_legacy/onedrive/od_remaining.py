import json, time, asyncio, aiohttp, cv2, numpy as np

TOKEN_FILE = "D:/Projects/ai-photo-template-miniapp/onedrive_token.json"
PROGRESS_FILE = "D:/Projects/ai-photo-template-miniapp/od_remaining_progress.txt"
CONCURRENT = 8

def log(msg):
    with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

async def get_folder_contents(session, folder_id, all_items, headers):
    url = f"https://graph.microsoft.com/v1.0/me/drive/items/{folder_id}/children?$top=200&$select=id,name,size,file,folder"
    while url:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                for item in data.get("value", []):
                    if "folder" in item:
                        await get_folder_contents(session, item["id"], all_items, headers)
                    elif "file" in item:
                        ext = item["name"][item["name"].rfind('.'):].lower() if '.' in item["name"] else ""
                        if ext in ['.jpg','.jpeg','.png','.gif','.bmp','.webp','.heic','.heif']:
                            all_items.append(item)
                url = data.get("@odata.nextLink")
            else:
                break

async def classify_one(session, img, sem):
    async with sem:
        try:
            img_id = img["id"]
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{img_id}/thumbnails/0/small/content"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    arr = np.frombuffer(data, np.uint8)
                    cv_img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    if cv_img is not None:
                        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                        faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
                        return (img_id, len(faces) > 0)
                # Fallback full image
                url2 = f"https://graph.microsoft.com/v1.0/me/drive/items/{img_id}/content"
                async with session.get(url2, timeout=aiohttp.ClientTimeout(total=30)) as resp2:
                    if resp2.status == 200:
                        data = await resp2.read()
                        arr = np.frombuffer(data, np.uint8)
                        cv_img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                        if cv_img is not None:
                            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                            faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
                            return (img_id, len(faces) > 0)
        except:
            pass
        return (img["id"], None)

async def main():
    with open(TOKEN_FILE) as f:
        token = json.load(f)
    
    refresh_count = 0
    async with aiohttp.ClientSession(headers={"Authorization": f"Bearer {token['access_token']}"}) as session:
        
        # Step 1: Scan remaining images in Pictures
        log("Scanning Pictures for remaining images...")
        remaining = []
        
        # Find Pictures folder
        async with session.get("https://graph.microsoft.com/v1.0/me/drive/root:/Pictures") as resp:
            pics = await resp.json()
            pics_id = pics.get("id")
        
        if pics_id:
            await get_folder_contents(session, pics_id, remaining, {})
        
        log(f"Found {len(remaining)} remaining images")
        
        if not remaining:
            log("Nothing to process!")
            return
        
        # Step 2: Classify remaining images
        log(f"Classifying {len(remaining)} remaining images...")
        sem = asyncio.Semaphore(CONCURRENT)
        tasks = [classify_one(session, img, sem) for img in remaining]
        
        to_delete = []
        to_keep = []
        still_error = []
        processed = 0
        start = time.time()
        
        for coro in asyncio.as_completed(tasks):
            img_id, has_face = await coro
            processed += 1
            
            if has_face is True:
                to_keep.append(img_id)
            elif has_face is False:
                to_delete.append(img_id)
            else:
                img_name = next((x["name"] for x in remaining if x["id"] == img_id), "?")
                still_error.append(img_id)
            
            if processed % 50 == 0 or processed == len(remaining):
                elapsed = int(time.time() - start)
                log(f"{processed}/{len(remaining)} - Keep: {len(to_keep)}, Delete: {len(to_delete)}, Err: {len(still_error)} ({elapsed}s)")
        
        # Step 3: Delete non-people images
        if to_delete:
            log(f"\n=== Deleting {len(to_delete)} non-people images ===")
            sem2 = asyncio.Semaphore(5)
            deleted = 0
            failed = 0
            
            async def del_one(rid):
                nonlocal deleted, failed
                async with sem2:
                    try:
                        async with session.delete(f"https://graph.microsoft.com/v1.0/me/drive/items/{rid}", timeout=aiohttp.ClientTimeout(total=15)) as resp:
                            if resp.status in (204, 200, 202):
                                deleted += 1
                            else:
                                failed += 1
                    except:
                        failed += 1
            
            tasks2 = [del_one(rid) for rid in to_delete]
            for coro in asyncio.as_completed(tasks2):
                await coro
            
            log(f"Deleted: {deleted}, Failed: {failed}")
        
        log(f"\n=== FINAL SUMMARY ===")
        log(f"Scanned: {len(remaining)}")
        log(f"Keep (people): {len(to_keep)}")
        log(f"Deleted (no people): {len(to_delete)}")
        log(f"Still error: {len(still_error)}")
        log(f"Total freed: {len(to_delete)} images")

asyncio.run(main())
