import json, requests
CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"
resp = requests.post("https://login.microsoftonline.com/consumers/oauth2/v2.0/devicecode", data={"client_id": CLIENT_ID, "scope": "Files.ReadWrite.All offline_access User.Read"})
dc = resp.json()
with open("D:/Projects/ai-photo-template-miniapp/od_dc.json", "w") as f:
    json.dump(dc, f)
print(f"CODE={dc['user_code']}")
