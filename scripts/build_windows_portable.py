#!/usr/bin/env python3
"""
Synapse Windows Portable Binary Build Orchestrator
Builds:
1. Frontend static SPA assets (app/frontend/dist)
2. Standalone PyInstaller sidecar binary (dist/bin/synapse.exe)
3. Portable Electron Desktop shell (dist/desktop/Synapse-Workbench-Portable-1.0.0.exe)
4. Assembles the standalone portable distribution bundle where topics remain an external addon.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

def run_cmd(cmd: list, cwd: Path, desc: str):
    print(f"\n[*] {desc}...")
    print(f"    Running: {' '.join(cmd)} in {cwd}")
    res = subprocess.run(cmd, cwd=str(cwd))
    if res.returncode != 0:
        print(f"[✘] Error: {desc} failed with exit code {res.returncode}")
        sys.exit(res.returncode)
    print(f"[✔] {desc} succeeded.")

def main():
    print("==================================================")
    print(" 🚀 SYNAPSE WINDOWS PORTABLE BINARY BUILDER       ")
    print("==================================================")

    dist_bin = WORKSPACE_ROOT / "dist" / "bin"
    dist_bin.mkdir(parents=True, exist_ok=True)

    # 1. Build Frontend Static Assets
    frontend_dir = WORKSPACE_ROOT / "app" / "frontend"
    if (frontend_dir / "package.json").exists():
        run_cmd(["npm", "run", "build"], cwd=frontend_dir, desc="Building React Frontend SPA")

    # 2. Build Python Standalone Sidecar with PyInstaller
    run_cmd(
        [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            "--distpath", str(dist_bin),
            "synapse.spec"
        ],
        cwd=WORKSPACE_ROOT,
        desc="Compiling Standalone Backend Sidecar (synapse.exe)"
    )

    # 3. Build Portable Electron Desktop Application
    desktop_dir = WORKSPACE_ROOT / "app" / "desktop"
    if (desktop_dir / "package.json").exists():
        run_cmd(
            ["npm", "run", "build:win"],
            cwd=desktop_dir,
            desc="Packaging Electron Portable Windows Desktop App"
        )

    # 4. Assemble Final Portable Distribution Folder
    portable_bundle = WORKSPACE_ROOT / "dist" / "Synapse-Portable-Windows"
    portable_bundle.mkdir(parents=True, exist_ok=True)

    readme_content = """==================================================
Synapse AI Learning Workbench — Portable Windows
==================================================

USAGE:
1. Double-click 'Synapse-Workbench-Portable.exe' to launch.
2. The curriculum 'topics/' directory is located directly alongside this executable.
   You can add, edit, or update curriculum topics without reinstalling or modifying the binary.
3. Your mastery progress and settings are saved locally in 'data/synapse.db'.

PORTABLE ADDON TOPICS:
- Add any domain or topic folder into './topics/'
- Synapse will immediately detect and index new courses upon startup.
"""
    (portable_bundle / "README.txt").write_text(readme_content, encoding="utf-8")

    # Copy built portable executable if available
    desktop_dist = WORKSPACE_ROOT / "dist" / "desktop"
    for exe_file in desktop_dist.glob("*.exe"):
        target_dest = portable_bundle / exe_file.name
        shutil.copy2(exe_file, target_dest)
        print(f"[✔] Bundled: {target_dest.name}")

    print("\n==================================================")
    print(f"[✔] PORTABLE WINDOWS BUILD COMPLETE!")
    print(f"    Bundle directory: {portable_bundle}")
    print("==================================================")

if __name__ == "__main__":
    main()
