#!/usr/bin/env python3
"""
GBrain 批量同步工具 — Python 实现

对比结论: Python 适用于 GBrain 的离线批量处理场景
- 与 GBrain 服务端同属 Flask/Python 生态，调试友好
- 适合处理 Markdown 文件的批量解析、提取、分析
- 在已有 Python 脚本模式（scripts/*.py）下扩展自然

用法:
    python scripts/gbrain_sync.py --action search --query "pi-agent"
    python scripts/gbrain_sync.py --action stats
    python scripts/gbrain_sync.py --action sync
    python scripts/gbrain_sync.py --action get --slug "projects/pi-agent"
    python scripts/gbrain_sync.py --action put --slug "projects/test" --content "test content"
    python scripts/gbrain_sync.py --action timeline --slug "projects/test" --summary "added entry"
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Any, Optional

try:
    import requests
except ImportError:
    print("ERROR: requests library required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("gbrain_sync")

GBRAIN_API_URL = os.environ.get("GBRAIN_API_URL", "http://100.92.38.117:8081")
GBRAIN_TIMEOUT = int(os.environ.get("GBRAIN_TIMEOUT_MS", "30000")) / 1000


def _request(method: str, path: str, data: Optional[dict] = None) -> Any:
    """内部请求封装，带超时和错误处理"""
    url = f"{GBRAIN_API_URL.rstrip('/')}{path}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=GBRAIN_TIMEOUT)
        else:
            response = requests.post(url, json=data, timeout=GBRAIN_TIMEOUT)

        if response.status_code >= 400:
            logger.error(f"Request failed: {response.status_code} {response.text[:200]}")
            return None

        return response.json() if response.text else {}
    except requests.exceptions.Timeout:
        logger.error(f"Request timed out after {GBRAIN_TIMEOUT}s: {url}")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None


def action_health() -> None:
    result = _request("GET", "/api/v1/health")
    if result:
        status = "✅ healthy" if result.get("ok") else "❌ unhealthy"
        logger.info(f"Health check: {status} {json.dumps(result)}")
    else:
        logger.error("Health check failed")


def action_stats() -> None:
    result = _request("GET", "/api/v1/stats")
    if result:
        logger.info(f"Stats: {json.dumps(result, ensure_ascii=False, indent=2)}")
    else:
        logger.error("Stats request failed")


def action_search(query: str) -> None:
    result = _request("GET", f"/api/v1/search?q={query}")
    if result:
        total = result.get("total", 0)
        logger.info(f"Search results for '{query}': {total} items")
        for item in result.get("items", [])[:10]:
            slug = item.get("slug", "unknown")
            snippet = (item.get("content", "") or "")[:100].replace("\n", " ")
            logger.info(f"  - {slug}: {snippet}...")
    else:
        logger.error("Search request failed")


def action_get(slug: str) -> None:
    result = _request("GET", f"/api/v1/get/{slug}")
    if result:
        logger.info(f"Page '{slug}':")
        logger.info(f"  Category: {result.get('category', 'unknown')}")
        content = result.get("content", "")
        logger.info(f"  Content length: {len(content)} chars")
        print(content)
    else:
        logger.error(f"Get page '{slug}' failed")


def action_put(slug: str, content: str) -> None:
    result = _request("POST", "/api/v1/put", {"slug": slug, "content": content})
    if result:
        logger.info(f"Page '{slug}' written successfully")
    else:
        logger.error(f"Put page '{slug}' failed")


def action_timeline(slug: str, summary: str) -> None:
    result = _request("POST", f"/api/v1/timeline/{slug}", {"summary": summary})
    if result:
        logger.info(f"Timeline entry added to '{slug}': {summary}")
    else:
        logger.error(f"Add timeline to '{slug}' failed")


def action_sync() -> None:
    result = _request("POST", "/api/v1/sync")
    if result:
        logger.info("Index sync triggered successfully")
    else:
        logger.error("Sync request failed")


def main() -> None:
    parser = argparse.ArgumentParser(description="GBrain 批量同步工具")
    parser.add_argument("--action", required=True, choices=[
        "health", "stats", "search", "get", "put", "timeline", "sync"
    ], help="操作类型")
    parser.add_argument("--query", type=str, help="搜索关键词")
    parser.add_argument("--slug", type=str, help="页面 slug")
    parser.add_argument("--content", type=str, help="页面内容（用于 put 操作）")
    parser.add_argument("--summary", type=str, help="时间线摘要（用于 timeline 操作）")
    parser.add_argument("--api-url", type=str, default=None, help="GBrain API 地址")

    args = parser.parse_args()

    if args.api_url:
        global GBRAIN_API_URL
        GBRAIN_API_URL = args.api_url

    actions = {
        "health": lambda: action_health(),
        "stats": lambda: action_stats(),
        "search": lambda: action_search(args.query or ""),
        "get": lambda: action_get(args.slug or ""),
        "put": lambda: action_put(args.slug or "", args.content or ""),
        "timeline": lambda: action_timeline(args.slug or "", args.summary or ""),
        "sync": lambda: action_sync(),
    }

    action_fn = actions.get(args.action)
    if action_fn:
        action_fn()
    else:
        logger.error(f"Unknown action: {args.action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
