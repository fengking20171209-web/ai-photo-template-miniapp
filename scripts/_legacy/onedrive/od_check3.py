import json, requests, os

TOKEN_FILE = os.path.join(os.path.dirname(__file__), '..', 'onedrive_token.json')
with open(TOKEN_FILE) as f:
    token = json.load(f)

headers = {"Authorization": f"Bearer {token['access_token']}"}

# Pictures folder by path
print("=== Pictures by path ===")
resp = requests.get("https://graph.microsoft.com/v1.0/me/drive/root:/Pictures", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"Name: {data.get('name')}, Size: {data.get('size',0)}, folder: {data.get('folder',{})}")
    cid = data.get("id")
    if cid:
        resp2 = requests.get(f"https://graph.microsoft.com/v1.0/me/drive/items/{cid}/children?$top=50", headers=headers)
        children = resp2.json().get("value", [])
        print(f"Children: {len(children)}")
        for c in children:
            ftype = "FOLDER" if "folder" in c else "FILE"
            print(f"  [{ftype}] {c['name']} size={c.get('size',0)/1024:.0f}KB")

# Look for Camera Roll inside Pictures
print("\n=== Pictures/Camera Roll ===")
resp = requests.get("https://graph.microsoft.com/v1.0/me/drive/root:/Pictures/Camera Roll", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    cid = data.get("id")
    if cid:
        resp2 = requests.get(f"https://graph.microsoft.com/v1.0/me/drive/items/{cid}/children?$top=50", headers=headers)
        children = resp2.json().get("value", [])
        print(f"Children: {len(children)}")
        for c in children[:10]:
            print(f"  {c['name']} size={c.get('size',0)/1024:.0f}KB")

# Search recursively
print("\n=== Recursive search for images ===")
for ext in ['jpg', 'png', 'jpeg', 'heic', 'bmp', 'gif', 'webp']:
    resp = requests.get(f"https://graph.microsoft.com/v1.0/me/drive/search(q='.{ext}')?$top=100&$select=id,name,size,parentReference,file", headers=headers)
    if resp.status_code == 200:
        found = resp.json().get("value", [])
        if found:
            print(f".{ext}: {len(found)} found")
            for img in found[:3]:
                path = img.get("parentReference",{}).get("path","")
                print(f"  {img['name']} ({img.get('size',0)/1024:.0f}KB) in {path}")
    else:
        print(f".{ext}: error {resp.status_code}")

# Also try /me/photo
print("\n=== /me/photo ===")
resp = requests.get("https://graph.microsoft.com/v1.0/me/photo", headers=headers)
print(f"Status: {resp.status_code}: {resp.text[:200]}")
