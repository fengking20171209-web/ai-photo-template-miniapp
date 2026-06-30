import json, requests

TOKEN_FILE = "D:/Projects/ai-photo-template-miniapp/onedrive_token.json"
CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"
TENANT = "consumers"

with open(TOKEN_FILE) as f:
    old = json.load(f)

if "refresh_token" not in old:
    print("No refresh token found! Need to re-authorize.")
    exit(1)

resp = requests.post(
    f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/token",
    data={
        "client_id": CLIENT_ID,
        "grant_type": "refresh_token",
        "refresh_token": old["refresh_token"],
        "scope": "Files.ReadWrite.All offline_access User.Read",
    },
)
result = resp.json()

if "access_token" in result:
    with open(TOKEN_FILE, "w") as f:
        json.dump(result, f)
    print("REFRESH_OK")
    print(f"New token expires in: {result.get('expires_in', '?')}s")
    print(f"Has refresh_token: {'refresh_token' in result}")
else:
    print(f"REFRESH_FAIL: {result.get('error', '?')} - {result.get('error_description', '?')[:200]}")
