import os
from dotenv import load_dotenv
load_dotenv('D:/Projects/ai-photo-template-miniapp/.env')
from qcloud_cos import CosConfig, CosS3Client
config = CosConfig(Region=os.getenv('COS_REGION'), SecretId=os.getenv('COS_SECRET_ID'), SecretKey=os.getenv('COS_SECRET_KEY'))
client = CosS3Client(config)
r = client.head_object(Bucket=os.getenv('COS_BUCKET_GEN'), Key='gen/test-upload/2026-05-28/original/test_cos_upload.png')
print('File verified on COS')
print('  ETag: ' + str(r.get('ETag','')))
print('  Size: ' + str(r.get('Content-Length',0)) + ' bytes')
print('  Type: ' + str(r.get('Content-Type','')))
