import subprocess
from pathlib import Path

root = Path(r"D:\Projects\ai-photo-template-miniapp")
log_dir = root / "logs"
log_dir.mkdir(exist_ok=True)
log = open(log_dir / "ui-fastapi.log", "a", encoding="utf-8")
proc = subprocess.Popen(
    ["python", "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd=root,
    stdout=log,
    stderr=subprocess.STDOUT,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
)
print(proc.pid)
