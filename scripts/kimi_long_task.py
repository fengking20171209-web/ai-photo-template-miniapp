#!/usr/bin/env python3
"""
Kimi 长任务执行器 — 免授权版

利用本地已登录的 kimi CLI 执行耗时较长的 AI 任务，无需额外配置 API Key。
支持单任务、批量任务、自动批准(yolo)、超时控制、日志归档。

用法示例:
    # 直接执行长 prompt
    python scripts/kimi_long_task.py -p "分析 templates/ 下所有 JSON 文件，输出风格统计报告"

    # 从文件读取任务（适合多行复杂 prompt）
    python scripts/kimi_long_task.py -f prompts/long_analysis.md --timeout 1800

    # 批量执行（自动批准，适合夜间跑批）
    python scripts/kimi_long_task.py --batch tasks/batch.json --yolo --auto

    # 使用 stream-json 输出格式，便于下游解析
    python scripts/kimi_long_task.py -f task.md --format stream-json --output-dir output/kimi-tasks
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── 项目路径 ──────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output" / "kimi-tasks"
DEFAULT_LOG_DIR = PROJECT_ROOT / "logs"

# ── Kimi CLI 自动发现 ─────────────────────────────────
KIMI_CANDIDATES: list[Path] = [
    # Git Bash / MSYS2 风格路径（优先）
    Path("/c/Users/Aerc/.kimi-code/bin/kimi"),
    Path("/c/Users/Aerc/.local/bin/kimi"),
    # Windows 原生风格
    Path(r"C:\Users\Aerc\.kimi-code\bin\kimi.exe"),
    Path(r"C:\Users\Aerc\.local\bin\kimi.exe"),
    Path(r"C:\Users\Aerc\AppData\Local\Programs\kimi\kimi.exe"),
    # 环境变量 PATH 中的 kimi（由 shutil.which 兜底）
]

# Windows 上 kimi 需要 Git Bash；自动检测常见安装位置
BASH_CANDIDATES: list[Path] = [
    Path(r"D:\Program Files\Git\bin\bash.exe"),
    Path(r"C:\Program Files\Git\bin\bash.exe"),
    Path(r"C:\Program Files (x86)\Git\bin\bash.exe"),
    Path(r"C:\Users\Aerc\AppData\Local\Programs\Git\bin\bash.exe"),
]


def discover_bash() -> Path | None:
    """自动发现 Git Bash（kimi-code 在 Windows 上需要）。"""
    user_bash = os.getenv("KIMI_SHELL_PATH")
    if user_bash:
        return Path(user_bash)  # 用户已手动设置，直接使用
    for candidate in BASH_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def discover_kimi() -> Path:
    """自动发现本地 kimi 可执行文件。"""
    for candidate in KIMI_CANDIDATES:
        if candidate.exists():
            return candidate

    import shutil

    found = shutil.which("kimi")
    if found:
        return Path(found)

    raise RuntimeError(
        "未找到 kimi CLI。请确保已安装并登录 kimi-code。\n"
        "安装地址: https://moonshotai.github.io/kimi-code/"
    )


# ── 日志工具 ──────────────────────────────────────────
class TaskLogger:
    def __init__(self, task_id: str, log_dir: Path) -> None:
        self.task_id = task_id
        self.log_dir = log_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = log_dir / f"kimi-task-{task_id}.log"
        self._fh = self.log_file.open("w", encoding="utf-8")
        self.start_time = time.monotonic()

    def write(self, line: str) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted = f"[{timestamp}] {line}"
        # Windows 控制台可能为 gbk 编码，直接写 utf-8 bytes 避免编码异常
        try:
            import sys

            out = (formatted + "\n").encode("utf-8", errors="replace")
            sys.stdout.buffer.write(out)
            sys.stdout.buffer.flush()
        except Exception:
            pass
        self._fh.write(formatted + "\n")
        self._fh.flush()

    def close(self) -> None:
        elapsed = time.monotonic() - self.start_time
        self.write(f"任务结束，耗时: {elapsed:.1f}s")
        self._fh.close()

    def __enter__(self) -> TaskLogger:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


# ── 核心执行 ──────────────────────────────────────────
def run_single_task(
    *,
    kimi_bin: Path,
    prompt: str,
    timeout: float,
    yolo: bool,
    auto: bool,
    output_format: str,
    output_dir: Path,
    task_id: str | None = None,
    log_dir: Path | None = None,
    env_extra: dict[str, str] | None = None,
) -> dict[str, Any]:
    """执行单个 kimi 长任务，返回结果字典。"""

    task_id = task_id or f"kt{uuid.uuid4().hex[:12]}"
    log_dir = log_dir or DEFAULT_LOG_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result_file = output_dir / f"{task_id}.json"

    with TaskLogger(task_id, log_dir) as log:
        log.write(f"任务ID: {task_id}")
        log.write(f"Kimi: {kimi_bin}")
        log.write(f"超时: {timeout}s | Yolo: {yolo} | Auto: {auto} | Format: {output_format}")
        log.write(f"Prompt 长度: {len(prompt)} 字符")

        cmd = [str(kimi_bin), "-p", prompt]
        # 注意: -y/--auto 与 -p 不兼容（kimi 0.6+）
        if output_format:
            cmd.extend(["--output-format", output_format])

        log.write(f"命令: {' '.join(cmd)}")

        env = os.environ.copy()
        env["PATH"] = f"{kimi_bin.parent}{os.pathsep}{env.get('PATH', '')}"

        # Windows 下 kimi 需要 Git Bash；若未设置则自动检测
        bash_path = discover_bash()
        if bash_path:
            env["KIMI_SHELL_PATH"] = str(bash_path)

        if env_extra:
            env.update(env_extra)

        # 设置工作目录为项目根目录，确保 kimi 能读取项目上下文
        cwd = str(PROJECT_ROOT)

        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # 合并 stderr 到 stdout 便于统一捕获
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )

        # 设置硬超时定时器：超时后强制 kill 整个进程树
        import threading

        killed_by_timer = False

        def _kill_after_timeout() -> None:
            nonlocal killed_by_timer
            if proc.poll() is None:
                killed_by_timer = True
                log.write(f"[TIMEOUT] 超过 {timeout}s，强制终止进程")
                try:
                    proc.kill()
                except Exception:
                    pass

        timer = threading.Timer(timeout, _kill_after_timeout)
        timer.start()

        stdout_lines: list[str] = []
        returncode: int | None = None
        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                stripped = line.rstrip("\n")
                stdout_lines.append(stripped)
                log.write(f"[OUT] {stripped}")

            returncode = proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            log.write("进程未正常退出，强制终止")
            proc.kill()
            returncode = proc.wait()
        except Exception as exc:
            log.write(f"执行异常: {exc}")
            proc.kill()
            returncode = -1
        finally:
            timer.cancel()
            # 确保进程已结束
            if proc.poll() is None:
                try:
                    proc.kill()
                    proc.wait(timeout=5)
                except Exception:
                    pass

        if killed_by_timer:
            returncode = 124  # 标准 timeout exit code

        stdout_text = "\n".join(stdout_lines)
        result = {
            "task_id": task_id,
            "ok": returncode == 0,
            "returncode": returncode,
            "prompt": prompt,
            "command": cmd,
            "stdout": stdout_text,
            "stdout_lines": stdout_lines,
            "result_file": str(result_file),
            "log_file": str(log.log_file),
        }

        with open(result_file, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

        log.write(f"结果已保存: {result_file}")
        return result


# ── 批量任务 ──────────────────────────────────────────
def load_batch_file(path: Path) -> list[dict[str, Any]]:
    """加载批量任务文件（JSON 或纯文本）。"""
    suffix = path.suffix.lower()
    if suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "tasks" in data:
            return data["tasks"]
        return [data]

    # 纯文本：每行一个任务，空行和 # 注释跳过
    tasks: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            tasks.append({"prompt": stripped})
    return tasks


def run_batch(
    *,
    kimi_bin: Path,
    batch_path: Path,
    timeout: float,
    yolo: bool,
    auto: bool,
    output_format: str,
    output_dir: Path,
    continue_on_error: bool,
) -> list[dict[str, Any]]:
    """批量执行 kimi 任务。"""
    tasks = load_batch_file(batch_path)
    print(f"[Batch] 共 {len(tasks)} 个任务，来源: {batch_path}")

    results: list[dict[str, Any]] = []
    for idx, task_def in enumerate(tasks, 1):
        prompt = task_def.get("prompt", "")
        task_id = task_def.get("task_id") or f"batch{idx:03d}-{uuid.uuid4().hex[:8]}"
        if not prompt:
            print(f"[Batch] 跳过空 prompt 任务 #{idx}")
            continue

        print(f"\n{'='*60}")
        print(f"[Batch] 任务 {idx}/{len(tasks)} | {task_id}")
        print(f"{'='*60}")

        try:
            res = run_single_task(
                kimi_bin=kimi_bin,
                prompt=prompt,
                timeout=task_def.get("timeout", timeout),
                yolo=task_def.get("yolo", yolo),
                auto=task_def.get("auto", auto),
                output_format=task_def.get("format", output_format),
                output_dir=output_dir,
                task_id=task_id,
            )
            results.append(res)
            if not res["ok"] and not continue_on_error:
                print("[Batch] 任务失败且设置了 --stop-on-error，中断批量执行")
                break
        except Exception as exc:
            print(f"[Batch] 任务 #{idx} 异常: {exc}")
            results.append({"task_id": task_id, "ok": False, "error": str(exc)})
            if not continue_on_error:
                break

    # 保存批量汇总报告
    summary_file = output_dir / f"batch-summary-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "batch_source": str(batch_path),
                "total": len(tasks),
                "completed": len(results),
                "success": sum(1 for r in results if r.get("ok")),
                "failed": sum(1 for r in results if not r.get("ok")),
                "results": results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"\n[Batch] 汇总报告: {summary_file}")
    return results


# ── CLI ───────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Kimi 长任务执行器 — 利用本地已登录的 kimi CLI 执行耗时任务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s -p "分析所有模板并生成统计报告" --timeout 600
  %(prog)s -f prompts/analysis.md --yolo --auto --timeout 1800
  %(prog)s --batch tasks/night_batch.json --yolo --auto --output-dir output/kimi-batch
        """,
    )
    parser.add_argument("-p", "--prompt", help="直接传入 prompt 文本（适合简短任务）")
    parser.add_argument("-f", "--file", type=Path, help="从文件读取 prompt（适合长文本/多行）")
    parser.add_argument("--batch", type=Path, help="批量任务文件（JSON 或纯文本，每行一个 prompt）")
    parser.add_argument("--yolo", action="store_true", help="自动批准所有操作（-y）")
    parser.add_argument("--auto", action="store_true", help="启动自动权限模式")
    parser.add_argument(
        "--timeout",
        type=float,
        default=600.0,
        help="单任务超时时间（秒），默认 600（10 分钟）",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=["text", "stream-json"],
        default="text",
        help="kimi 输出格式，默认 text",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"任务结果输出目录，默认 {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=DEFAULT_LOG_DIR,
        help=f"日志目录，默认 {DEFAULT_LOG_DIR}",
    )
    parser.add_argument(
        "--kimi-bin",
        type=Path,
        default=None,
        help="强制指定 kimi 可执行文件路径",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        default=True,
        help="批量模式下单个任务失败后继续（默认开启）",
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="批量模式下单个任务失败后中断",
    )

    args = parser.parse_args()

    if args.stop_on_error:
        args.continue_on_error = False

    if not args.prompt and not args.file and not args.batch:
        parser.error("至少需要指定 -p/--prompt、-f/--file 或 --batch 之一")

    # 发现 kimi
    try:
        kimi_bin = args.kimi_bin or discover_kimi()
    except RuntimeError as exc:
        print(f"[Error] {exc}", file=sys.stderr)
        return 1

    print(f"[Info] Kimi CLI: {kimi_bin}")

    # 创建输出目录
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.log_dir.mkdir(parents=True, exist_ok=True)

    # 批量模式
    if args.batch:
        run_batch(
            kimi_bin=kimi_bin,
            batch_path=args.batch,
            timeout=args.timeout,
            yolo=args.yolo,
            auto=args.auto,
            output_format=args.output_format,
            output_dir=args.output_dir,
            continue_on_error=args.continue_on_error,
        )
        return 0

    # 单任务模式
    prompt = args.prompt
    if args.file:
        if not args.file.exists():
            print(f"[Error] 文件不存在: {args.file}", file=sys.stderr)
            return 1
        prompt = args.file.read_text(encoding="utf-8")

    if not prompt:
        print("[Error] prompt 为空", file=sys.stderr)
        return 1

    result = run_single_task(
        kimi_bin=kimi_bin,
        prompt=prompt,
        timeout=args.timeout,
        yolo=args.yolo,
        auto=args.auto,
        output_format=args.output_format,
        output_dir=args.output_dir,
        log_dir=args.log_dir,
    )
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n[Abort] 用户中断", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(f"[Fatal] {exc}", file=sys.stderr)
        raise SystemExit(1)
