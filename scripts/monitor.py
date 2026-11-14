#!/usr/bin/env python3
"""
Detailed Live Progress Monitor for Synapse Curriculum Enhancement & Generation
Usage:
  python3 scripts/monitor.py           # Snapshot overview
  python3 scripts/monitor.py --watch   # Live auto-updating terminal dashboard
  python3 scripts/monitor.py --tail    # Follow generator.log directly
"""

import sys
import re
import time
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = WORKSPACE_ROOT / "generator.log"
GIT_CWD = str(WORKSPACE_ROOT)

def strip_ansi(text: str) -> str:
    """Removes terminal escape sequences to prevent terminal injection."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def get_process_status():
    try:
        res = subprocess.run(["pgrep", "-fl", "generate_all.py"], capture_output=True, text=True, timeout=5)
        return [l.strip() for l in res.stdout.strip().splitlines() if l.strip()]
    except Exception:
        return []

def get_recent_commits(limit=5):
    try:
        res = subprocess.run(
            ["git", "log", "--grep=^enhance(", f"-n{limit}", "--format=%h | %cr | %s"],
            capture_output=True, text=True, cwd=GIT_CWD, timeout=5
        )
        return [l for l in res.stdout.strip().splitlines() if l.strip()]
    except Exception:
        return []

def get_current_diff_stat():
    try:
        res = subprocess.run(
            ["git", "diff", "--stat", "topics/"],
            capture_output=True, text=True, cwd=GIT_CWD, timeout=5
        )
        return res.stdout.strip()
    except Exception:
        return ""

def get_batch_progress():
    if not LOG_FILE.exists():
        return 0, 0, "Initializing pipeline..."
    try:
        content = LOG_FILE.read_text(encoding="utf-8", errors="replace")
        matches = re.findall(r"\[\*\] \[(\d+)/(\d+)\] (?:Enhancing|Generating): (.+)", content)
        if matches:
            curr, total, topic = matches[-1]
            return int(curr), int(total), topic.strip(" .")
    except Exception:
        pass
    return 0, 0, "Scanning queue..."

def get_latest_log_lines(n=8):
    if not LOG_FILE.exists():
        return ["(No generator.log found yet)"]
    try:
        lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        sanitized = [strip_ansi(line) for line in lines[-n:]]
        return sanitized if sanitized else ["(Waiting for log output...)"]
    except Exception as e:
        return [f"(Log read error: {type(e).__name__})"]

def render():
    procs = get_process_status()
    curr, total, topic_from_log = get_batch_progress()
    target_count = total if total > 0 else 45
    enhanced_count = curr if total > 0 else 0

    active_topic = topic_from_log if procs else "Pipeline complete & pushed to remote!"
    diff_stat = get_current_diff_stat()
    commits = get_recent_commits()
    log_tail = get_latest_log_lines(8)

    output = []
    output.append("=" * 70)
    output.append(" 🧠 SYNAPSE CURRICULUM PIPELINE MONITOR (LIVE DETAIL)")
    output.append("=" * 70)

    if procs:
        pid = procs[0].split()[0]
        output.append(f" Engine Status:  🟢 ACTIVE (PID: {pid}) - 3 Parallel Claude Opus Workers")
    else:
        output.append(" Engine Status:  🏁 COMPLETE / IDLE")

    pct = min(100.0, (enhanced_count / target_count) * 100) if target_count > 0 else 0
    bar_len = 25
    filled = int(bar_len * (enhanced_count / target_count)) if target_count > 0 else 0
    bar = "█" * filled + "░" * (bar_len - filled)
    output.append(f" Progress:       [{bar}] {enhanced_count}/{target_count} ({pct:.1f}%)")
    output.append(f" Current Topic:  {active_topic}")
    output.append("-" * 70)

    output.append(" 📡 Live Engine Output (generator.log):")
    for line in log_tail:
        output.append(f"   │ {line}")

    output.append("-" * 70)
    output.append(" 📝 Live File Insertions & Line Expansion:")
    if diff_stat:
        for line in diff_stat.splitlines()[-5:]:
            output.append(f"   │ {line}")
    else:
        output.append("   │ (No unstaged modifications right now)")

    output.append("-" * 70)
    output.append(" 🏆 Published Enhanced Topics:")
    if commits:
        for c in commits:
            output.append(f"   ✔ {c}")
    else:
        output.append("   (Awaiting first topic completion...)")

    output.append("=" * 70)
    output.append(" Tip: Run 'tail -f generator.log' in any terminal for raw stream.")
    return "\n".join(output)

def main():
    if "--tail" in sys.argv:
        if not LOG_FILE.exists():
            LOG_FILE.touch()
        subprocess.run(["tail", "-f", str(LOG_FILE)])
        return

    watch_mode = "--watch" in sys.argv or "-w" in sys.argv
    if not watch_mode:
        print(render())
        return

    try:
        while True:
            print("\033[2J\033[H", end="")
            print(render())
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nExiting monitor.")

if __name__ == "__main__":
    main()
