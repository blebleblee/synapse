"""
Daemon and Service Management
Runs the Web Workbench as a background daemon and generates systemd/launchd services.
"""

import os
import sys
import signal
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
PID_FILE = WORKSPACE_ROOT / ".workbench.pid"
DEPLOY_DIR = WORKSPACE_ROOT / "deploy"

def start_daemon(host: str = "0.0.0.0", port: int = 8000) -> int:
    if PID_FILE.exists():
        old_pid = int(PID_FILE.read_text().strip())
        try:
            os.kill(old_pid, 0)
            print(f"[!] Workbench daemon is already running (PID: {old_pid}).")
            return old_pid
        except OSError:
            PID_FILE.unlink(missing_ok=True)

    python_bin = WORKSPACE_ROOT / ".venv" / "bin" / "python3"
    if not python_bin.exists():
        python_bin = sys.executable

    cmd = [
        str(python_bin),
        "-m", "uvicorn",
        "app.backend.main:app",
        "--host", host,
        "--port", str(port)
    ]

    log_path = WORKSPACE_ROOT / "workbench.log"
    log_file = open(log_path, "a", encoding="utf-8")
    proc = subprocess.Popen(
        cmd,
        cwd=str(WORKSPACE_ROOT),
        stdin=subprocess.DEVNULL,
        stdout=log_file,
        stderr=log_file,
        start_new_session=True
    )

    PID_FILE.write_text(str(proc.pid))
    print(f"[✔] Workbench daemon started (PID: {proc.pid}) on http://{host}:{port}")
    print(f"[*] Logs: {log_path.relative_to(WORKSPACE_ROOT)}")
    return proc.pid

def stop_daemon() -> bool:
    if not PID_FILE.exists():
        print("[!] No active daemon PID file found.")
        return False

    pid = int(PID_FILE.read_text().strip())
    try:
        os.kill(pid, signal.SIGTERM)
        PID_FILE.unlink(missing_ok=True)
        print(f"[✔] Stopped Workbench daemon (PID: {pid}).")
        return True
    except ProcessLookupError:
        PID_FILE.unlink(missing_ok=True)
        print(f"[!] Process {pid} was not running. Removed stale PID file.")
        return False

def generate_service_files():
    DEPLOY_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Systemd Service (Linux Homelab)
    systemd_content = f"""[Unit]
Description=AI Learning Workbench Service
After=network.target

[Service]
Type=simple
User={os.environ.get('USER', 'synapse')}
WorkingDirectory={WORKSPACE_ROOT}
ExecStart={sys.executable} -m uvicorn app.backend.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment=PATH={WORKSPACE_ROOT}/.venv/bin:/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target
"""
    (DEPLOY_DIR / "learning-workbench.service").write_text(systemd_content, encoding="utf-8")

    # 2. Launchd Plist (macOS)
    launchd_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.synapse.workbench</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>-m</string>
        <string>uvicorn</string>
        <string>app.backend.main:app</string>
        <string>--host</string>
        <string>127.0.0.1</string>
        <string>--port</string>
        <string>8000</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{WORKSPACE_ROOT}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{WORKSPACE_ROOT}/workbench.log</string>
    <key>StandardErrorPath</key>
    <string>{WORKSPACE_ROOT}/workbench.log</string>
</dict>
</plist>
"""
    plist_path = DEPLOY_DIR / "com.synapse.workbench.plist"
    plist_path.write_text(launchd_content, encoding="utf-8")
    print(f"[✔] Generated service files in {DEPLOY_DIR.relative_to(WORKSPACE_ROOT)}/")
