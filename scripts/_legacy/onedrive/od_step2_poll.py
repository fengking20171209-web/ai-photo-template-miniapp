import json, requests, sys, time

TOKEN_PATH = "D:/Projects/ai-photo-template-miniapp/onedrive_token.json"
DC_PATH = "D:/Projects/ai-photo-template-miniapp/od_dc.json"

with open(DC_PATH) as f:
    dc = json.load(f)

CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"
TENANT = "consumers"
device_code = dc["device_code"]

resp = requests.post(f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/token", data={
    "client_id": CLIENT_ID,
    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
    "device_code": device_code,
})
result = resp.json()

if "access_token" in result:
    with open(TOKEN_PATH, "w") as f:
        json.dump(result, f)
    headers = {"Authorization": f"Bearer {result['access_token']}"}
    me = requests.get("https://graph.microsoft.com/v1.0/me?$select=displayName,userPrincipalName", headers=headers).json()
    drive = requests.get("https://graph.microsoft.com/v1.0/me/drive", headers=headers).json()
    q = drive.get("quota", {})
    print("AUTH_OK")
    print("ACCOUNT=" + str(me.get("userPrincipalName", "?")))
    print("NAME=" + str(me.get("displayName", "?")))
    print("USED_GB=" + str(round(q.get("used", 0) / 1024**3, 2)))
    print("TOTAL_GB=" + str(round(q.get("total", 0) / 1024**3, 1)))
else:
    err = result.get("error", "?")
    desc = result.get("error_description", "")[:200]
    print(f"FAIL: {err} - {desc}")
