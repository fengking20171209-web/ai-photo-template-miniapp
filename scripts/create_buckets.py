import os
from dotenv import load_dotenv
load_dotenv('D:/Projects/ai-photo-template-miniapp/.env')
from qcloud_cos import CosConfig, CosS3Client

region = os.getenv('COS_REGION')
config = CosConfig(Region=region, SecretId=os.getenv('COS_SECRET_ID'), SecretKey=os.getenv('COS_SECRET_KEY'))
client = CosS3Client(config)

buckets = [
    ('ai-fashion-ref-shanghai', 'ref - external reference images'),
    ('ai-fashion-gen-shanghai', 'gen - AI generated images'),
    ('ai-fashion-doc-shanghai', 'doc - prompts, metadata, documents'),
]

for name, desc in buckets:
    try:
        client.create_bucket(Bucket=name, BucketACL='private')
        print(f'[ok] Created: {name} ({desc})')
    except Exception as e:
        print(f'[warn] {name}: {e}')
