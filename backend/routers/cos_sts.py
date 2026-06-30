"""COS STS temporary credential service.

Provides temporary credentials for frontend clients to access COS
objects directly with limited permissions (ref/* and gen/* paths).
"""

import json
import os
import time

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.sts.v20180813 import sts_client, models

load_dotenv()

router = APIRouter()

# COS bucket ARN patterns (APPID: 1427746697)
APPID = os.environ.get("COS_APPID", "1427746697")
BUCKET_REF = os.environ.get("COS_BUCKET_REF", f"ai-fashion-ref-shanghai-{APPID}")
BUCKET_GEN = os.environ.get("COS_BUCKET_GEN", f"ai-fashion-gen-shanghai-{APPID}")
REGION = os.environ.get("COS_REGION", "ap-shanghai")

# STS config
STS_NAME = "ai-fashion-federation"
STS_DURATION = 1800  # 30 minutes


def _build_cos_policy() -> str:
    """Build a COS access policy limiting to ref/* and gen/* paths."""
    policy = {
        "version": "2.0",
        "statement": [
            {
                "effect": "allow",
                "action": [
                    "name/cos:GetObject",
                    "name/cos:PutObject",
                    "name/cos:HeadObject",
                    "name/cos:GetBucket",
                ],
                "resource": [
                    f"qcs::cos:{REGION}:uid/{APPID}:{BUCKET_REF}/ref/*",
                    f"qcs::cos:{REGION}:uid/{APPID}:{BUCKET_GEN}/gen/*",
                ],
            }
        ],
    }
    return json.dumps(policy)


@router.get("/credentials")
def get_cos_credentials():
    """Return temporary COS credentials for frontend access.

    Returns tmpSecretId, tmpSecretKey, sessionToken, expiredTime,
    bucket, and region for use with the COS JavaScript SDK.
    """
    secret_id = os.environ.get("COS_SECRET_ID")
    secret_key = os.environ.get("COS_SECRET_KEY")

    if not secret_id or not secret_key:
        raise HTTPException(status_code=500, detail="COS credentials not configured in .env")

    try:
        cred = credential.Credential(secret_id, secret_key)
        client = sts_client.StsClient(cred, REGION)

        req = models.GetFederationTokenRequest()
        req.Name = STS_NAME
        req.DurationSeconds = STS_DURATION
        req.Policy = _build_cos_policy()

        resp = client.GetFederationToken(req)
        creds = resp.Credentials

        return {
            "credentials": {
                "tmpSecretId": creds.TmpSecretId,
                "tmpSecretKey": creds.TmpSecretKey,
                "sessionToken": creds.Token,
            },
            "expiredTime": resp.ExpiredTime,
            "bucket": BUCKET_GEN,
            "region": REGION,
        }
    except TencentCloudSDKException as e:
        raise HTTPException(status_code=502, detail=f"STS API error: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
