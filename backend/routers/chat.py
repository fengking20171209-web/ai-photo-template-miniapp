"""Chat proxy for the in-app AI assistant ("写真助手").

The frontend must NOT embed an API key in client-side JavaScript. This endpoint
proxies chat completions to the Agnes OpenAI-compatible API using a server-side
key, streaming the response back to the browser via SSE.

Frontend usage: POST /chat with an OpenAI-style body ({messages, stream, ...}).
The model and credentials are enforced server-side.
"""
import json
import os

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

load_dotenv()
load_dotenv(".env.sub", override=True)

router = APIRouter()

_raw_base = os.getenv("AGNES_API_BASE", "https://apihub.agnes-ai.com/v1").rstrip("/")
if not _raw_base.endswith("/v1"):
    _raw_base = _raw_base + "/v1"
CHAT_BASE = _raw_base
# Dedicated chat key if provided, else fall back to the image key.
CHAT_KEY = os.getenv("AGNES_CHAT_API_KEY") or os.getenv("AGNES_API_KEY", "")
CHAT_MODEL = os.getenv("AGNES_CHAT_MODEL", "agnes-2.0-flash")


@router.post("")
async def chat(request: Request):
    """Proxy a chat completion to Agnes with the key kept server-side.

    Accepts an OpenAI-style JSON body. ``model`` defaults to the configured
    chat model. Supports streaming (SSE) and non-streaming responses.
    """
    if not CHAT_KEY:
        return JSONResponse(status_code=503, content={"error": "Chat API key not configured"})

    try:
        raw = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})
    if not isinstance(raw, dict):
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})

    messages = raw.get("messages")
    if not isinstance(messages, list) or not messages:
        return JSONResponse(status_code=400, content={"error": "messages is required"})

    stream = bool(raw.get("stream", True))

    # Build a whitelisted payload; model and credentials are enforced server-side
    # so clients cannot override the model or inject arbitrary upstream fields.
    body: dict = {"model": CHAT_MODEL, "messages": messages, "stream": stream}
    if isinstance(raw.get("temperature"), (int, float)):
        body["temperature"] = raw["temperature"]
    if isinstance(raw.get("max_tokens"), int):
        body["max_tokens"] = raw["max_tokens"]

    headers = {
        "Authorization": f"Bearer {CHAT_KEY}",
        "Content-Type": "application/json",
    }
    url = f"{CHAT_BASE}/chat/completions"

    if not stream:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, headers=headers, json=body)
            try:
                payload = resp.json()
            except Exception:
                import logging
                logging.getLogger(__name__).warning("Chat upstream non-JSON %s: %s", resp.status_code, resp.text[:500])
                return JSONResponse(status_code=502, content={"error": "对话服务返回异常"})
            return JSONResponse(status_code=resp.status_code, content=payload)

    async def event_stream():
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", url, headers=headers, json=body) as resp:
                if resp.status_code >= 400:
                    detail = (await resp.aread()).decode("utf-8", "ignore")
                    # Log full upstream detail server-side; return a generic message.
                    import logging
                    logging.getLogger(__name__).warning("Chat upstream %s: %s", resp.status_code, detail[:500])
                    yield f"data: {json.dumps({'error': f'对话服务暂时不可用 (上游 {resp.status_code})'})}\n\n"
                    return
                async for chunk in resp.aiter_raw():
                    if chunk:
                        yield chunk

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
