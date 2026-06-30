import subprocess
import sys
from pathlib import Path

root = Path(r"D:\Projects\ai-photo-template-miniapp")
log_dir = root / "logs"
log_dir.mkdir(exist_ok=True)
out = open(log_dir / "ui-fastapi.out.log", "ab", buffering=0)
err = open(log_dir / "ui-fastapi.err.log", "ab", buffering=0)
flags = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd=str(root),
    stdin=subprocess.DEVNULL,
    stdout=out,
    stderr=err,
    creationflags=flags,
    close_fds=True,
)
print(proc.pid)
