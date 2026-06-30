#!/usr/bin/env python3
"""watch_face.py — 智能 face/ 目录监控 + 自动导入引擎

工作模式:
  ┌─────────┬──────────────┐
  │ 周一到五 │ 每 4 小时检查 │
  │ 周六到日 │ 每 8 小时检查 │
  └─────────┴──────────────┘

  每次检测到有新文件时 → 自动执行 import_face_gen.py

用法:
  # 单次检查（给 Windows 计划任务用）
  python scripts/watch_face.py --once

  # 单次检查 + OneDrive 同步
  python scripts/watch_face.py --once --sync-onedrive

  # 持续运行（每 60 秒轮询）
  python scripts/watch_face.py --sync-onedrive

  # 查看上次运行时间
  python scripts/watch_face.py --status
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ── 路径 ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent
FACE_DIR = PROJECT_DIR / "face"
IMPORT_SCRIPT = SCRIPT_DIR / "import_face_gen.py"
STATE_FILE = PROJECT_DIR / "local_cache" / "watch_face_state.json"
LOG_FILE = PROJECT_DIR / "logs" / "watch_face.log"

# ── 间隔配置 ──────────────────────────────────────────────────────────
INTERVAL_WEEKDAY = 4 * 3600   # 4 小时（秒）
INTERVAL_WEEKEND = 8 * 3600   # 8 小时（秒）
POLL_INTERVAL = 60            # 轮询间隔（秒）

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


# ── 工具函数 ──────────────────────────────────────────────────────────

def get_today_interval() -> int:
    """根据今天星期几返回检测间隔"""
    wd = datetime.now().weekday()  # 0=周一, 6=周日
    return INTERVAL_WEEKDAY if wd < 5 else INTERVAL_WEEKEND


def load_state() -> dict:
    """加载运行状态"""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_run": 0, "total_runs": 0, "total_imported": 0}


def save_state(state: dict):
    """保存运行状态"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def has_pending_images() -> bool:
    """检查 face/ 有没有待处理的图片"""
    if not FACE_DIR.exists():
        return False
    for f in FACE_DIR.rglob("*"):
        if f.is_file() and f.suffix.lower() in IMAGE_EXTS and ".processed" not in f.parts:
            return True
    return False


# ── 日志 ──────────────────────────────────────────────────────────────

def setup_logging():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(LOG_FILE),
        level=logging.INFO,
        format="%(asctime)s  [%(levelname)s]  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # 控制台也输出
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(asctime)s  [%(levelname)s]  %(message)s", datefmt="%H:%M:%S"))
    logging.getLogger().addHandler(console)


# ── 核心逻辑 ──────────────────────────────────────────────────────────

def should_run(state: dict) -> tuple[bool, str]:
    """判断是否应该执行导入

    返回: (应该运行?, 原因)
    """
    now = time.time()
    interval = get_today_interval()
    elapsed = now - state.get("last_run", 0)

    day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    today = day_names[datetime.now().weekday()]

    if elapsed < interval:
        remaining_h = (interval - elapsed) / 3600
        return False, (f"{today}，距下次检测还有 {remaining_h:.1f} 小时"
                       f"（间隔: {interval//3600}h），跳过")

    if not has_pending_images():
        return False, f"{today}，face/ 没有新图片，跳过"

    return True, f"{today}，距上次 {(elapsed/3600):.1f}h，检测到新文件 → 执行导入"


def run_import(sync_onedrive: bool) -> int:
    """执行 import_face_gen.py，返回退出码"""
    cmd = [sys.executable, str(IMPORT_SCRIPT), "--non-interactive"]
    if sync_onedrive:
        cmd.append("--sync-onedrive")

    logging.info("执行: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_DIR))

    # 输出详细信息
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            logging.info("  | %s", line.strip())
    if result.stderr:
        for line in result.stderr.strip().split("\n"):
            if line.strip():
                logging.warning("  ! %s", line.strip())

    return result.returncode


def do_check(sync_onedrive: bool) -> bool:
    """执行一次检查。返回 True=导入了文件"""
    state = load_state()
    ok, reason = should_run(state)

    if ok:
        logging.info("▶ %s", reason)
        ret = run_import(sync_onedrive)
        if ret == 0:
            state["last_run"] = time.time()
            state["total_runs"] = state.get("total_runs", 0) + 1

            # 统计本次导入了多少张
            import_count = 0
            for line in open(LOG_FILE, "r", encoding="utf-8", errors="replace"):
                if "上传:" in line and "跳过" not in line:
                    try:
                        import_count = int(line.split("上传:")[1].strip().split()[0])
                    except: pass
            state["total_imported"] = state.get("total_imported", 0) + import_count
            save_state(state)
            logging.info("✓ 导入完成（本次 %d 张，累计 %d 次 %d 张）",
                         import_count, state["total_runs"], state["total_imported"])
            return True
        else:
            logging.error("✗ 导入失败（exit code: %d）", ret)
    else:
        logging.info("- %s", reason)

    return False


# ── 入口 ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="智能 face/ 目录监控")
    parser.add_argument("--once", action="store_true", help="单次检查（给计划任务用）")
    parser.add_argument("--sync-onedrive", action="store_true", help="同步到 OneDrive")
    parser.add_argument("--status", action="store_true", help="查看运行状态")
    args = parser.parse_args()

    if args.status:
        state = load_state()
        interval = get_today_interval()
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        today = day_names[datetime.now().weekday()]
        last = state.get("last_run", 0)
        if last > 0:
            last_str = datetime.fromtimestamp(last).strftime("%Y-%m-%d %H:%M:%S")
            elapsed_h = (time.time() - last) / 3600
        else:
            last_str = "从未"
            elapsed_h = 0

        print(f"watch_face 状态")
        print(f"  ├─ 今日: {today}")
        print(f"  ├─ 检测间隔: {interval//3600} 小时")
        print(f"  ├─ 上次导入: {last_str}")
        print(f"  ├─ 距上次: {elapsed_h:.1f} 小时")
        print(f"  ├─ 累计运行: {state.get('total_runs', 0)} 次")
        print(f"  ├─ 累计导入: {state.get('total_imported', 0)} 张")
        print(f"  ├─ 待处理: {'有' if has_pending_images() else '无'}")
        print(f"  └─ 状态文件: {STATE_FILE}")
        return

    setup_logging()

    if args.once:
        # 单次检查模式 — Windows 计划任务用
        logging.info("=== watch_face 单次检查 ===")
        if not FACE_DIR.exists():
            logging.warning("face/ 目录不存在: %s", FACE_DIR)
            return
        do_check(args.sync_onedrive)
        logging.info("=== 单次检查结束 ===\n")
    else:
        # 持续监控模式
        logging.info("=== watch_face 监控启动（扫描间隔: %ds）===", POLL_INTERVAL)
        logging.info("工作日(4h) / 周末(8h) | OneDrive同步: %s", args.sync_onedrive)
        logging.info("face/ 目录: %s", FACE_DIR)

        cycles = 0
        while True:
            cycles += 1
            if cycles % 60 == 0:  # 每小时输出一次心跳
                day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
                today = day_names[datetime.now().weekday()]
                state = load_state()
                last = state.get("last_run", 0)
                if last > 0:
                    elapsed_h = (time.time() - last) / 3600
                else:
                    elapsed_h = 0
                interval = get_today_interval()
                logging.info("[heartbeat] %s | 间隔: %dh | 距上次: %.1fh | 累计: %d次 %d张",
                             today, interval//3600, elapsed_h,
                             state.get("total_runs", 0), state.get("total_imported", 0))

            do_check(args.sync_onedrive)
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
