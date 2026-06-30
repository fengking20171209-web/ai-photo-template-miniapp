import os, json
from dotenv import load_dotenv
load_dotenv('D:/Projects/ai-photo-template-miniapp/.env')
from qcloud_cos import CosConfig, CosS3Client
config = CosConfig(
    Region=os.getenv('COS_REGION'),
    SecretId=os.getenv('COS_SECRET_ID'),
    SecretKey=os.getenv('COS_SECRET_KEY'),
)
client = CosS3Client(config)
response = client.list_buckets()
# Print the full response structure to see what we get
print(json.dumps(response, indent=2, default=str, ensure_ascii=False))
