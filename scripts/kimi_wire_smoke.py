import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KIMI_BIN = Path(r"C:\Users\Aerc\.local\bin\kimi.exe")
AGENT_FILE = PROJECT_ROOT / ".kimi" / "agents" / "photo-template-agent.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test Kimi Wire JSON-RPC handshake.")
    parser.add_argument(
        "--prompt",
        help="Optional prompt to send after initialize. This may consume Kimi quota.",
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    if not KIMI_BIN.exists():
        print(json.dumps({"ok": False, "error": f"Kimi not found: {KIMI_BIN}"}, ensure_ascii=False))
        return 1

    command = [
        str(KIMI_BIN),
        "--agent-file",
        str(AGENT_FILE),
        "--wire",
    ]

    env = os.environ.copy()
    env["PATH"] = f"{KIMI_BIN.parent};{env.get('PATH', '')}"

    proc = subprocess.Popen(
        command,
        cwd=str(PROJECT_ROOT),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=env,
    )

    try:
        initialize_id = send(
            proc,
            "initialize",
            {
                "protocol_version": "1.7",
                "client": {"name": "ai-photo-template-wire-smoke", "version": "0.1.0"},
                "capabilities": {"supports_question": True, "supports_plan_mode": True},
            },
        )
        initialize_response = wait_for_id(proc, initialize_id, args.timeout)

        result: dict[str, Any] = {
            "ok": "result" in initialize_response,
            "initialize": initialize_response,
        }

        if args.prompt:
            prompt_id = send(proc, "prompt", {"user_input": args.prompt})
            result["prompt"] = wait_for_id(proc, prompt_id, args.timeout)

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1
    finally:
        proc.kill()


def send(proc: subprocess.Popen[str], method: str, params: dict[str, Any]) -> str:
    request_id = str(uuid.uuid4())
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "id": request_id,
        "params": params,
    }
    assert proc.stdin is not None
    proc.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
    proc.stdin.flush()
    return request_id


def wait_for_id(proc: subprocess.Popen[str], request_id: str, timeout: float) -> dict[str, Any]:
    assert proc.stdout is not None
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        line = proc.stdout.readline()
        if not line:
            if proc.poll() is not None:
                stderr = ""
                if proc.stderr is not None:
                    stderr = proc.stderr.read()
                raise RuntimeError(f"kimi --wire exited early: {stderr}")
            time.sleep(0.05)
            continue

        message = json.loads(line)
        if message.get("id") == request_id:
            return message

    raise TimeoutError(f"Timed out waiting for response id {request_id}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
