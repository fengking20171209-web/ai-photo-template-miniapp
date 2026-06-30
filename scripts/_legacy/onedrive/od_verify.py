import json, requests

TOKEN_FILE = "D:/Projects/ai-photo-template-miniapp/onedrive_token.json"
CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"

with open(TOKEN_FILE) as f:
    token = json.load(f)

resp = requests.post(
    "https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
    data={
        "client_id": CLIENT_ID,
        "grant_type": "refresh_token",
        "refresh_token": token["refresh_token"],
        "scope": "Files.ReadWrite.All offline_access User.Read",
    },
)
result = resp.json()
if "access_token" not in result:
    print("Token refresh failed:", result.get("error", "?"))
    exit(1)

at = result["access_token"]
headers = {"Authorization": f"Bearer {at}"}

# Account info
me = requests.get("https://graph.microsoft.com/v1.0/me?$select=displayName,userPrincipalName", headers=headers).json()
print(f"Account: {me.get('userPrincipalName', '?')}")

# Drive quota
drive = requests.get("https://graph.microsoft.com/v1.0/me/drive", headers=headers).json()
q = drive.get("quota", {})
used_mb = q.get("used", 0) / 1024 / 1024
total_mb = q.get("total", 0) / 1024 / 1024
print(f"\nTotal: {total_mb:.0f} MB ({total_mb/1024:.1f} GB)")
print(f"Used:  {used_mb:.0f} MB ({used_mb/1024:.2f} GB)")
print(f"Free:  {(total_mb - used_mb):.0f} MB ({(total_mb - used_mb)/1024:.2f} GB)")
print(f"State: {q.get('state', '?')}")

# Count remaining images
print("\nScanning remaining files...")
remaining = []
url = "https://graph.microsoft.com/v1.0/me/drive/root/children?$top=200&$select=id,name,size,file,folder"
while url:
    resp = requests.get(url, headers=headers)
    data = resp.json()
    for item in data.get("value", []):
        if "file" in item:
            ext = item["name"][item["name"].rfind("."):].lower() if "." in item["name"] else ""
            if ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".heif"]:
                remaining.append(item)
    url = data.get("@odata.nextLink")

print(f"Remaining image files at root: {len(remaining)}")

# Check Pictures folder
resp = requests.get("https://graph.microsoft.com/v1.0/me/drive/root:/Pictures", headers=headers)
if resp.status_code == 200:
    pics = resp.json()
    cc = pics.get("folder", {}).get("childCount", 0)
    print(f"Pictures folder contains: {cc} items")
