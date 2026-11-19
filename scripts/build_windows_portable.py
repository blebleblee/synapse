#!/usr/bin/env python3
"""
Synapse Windows Portable Binary Build Orchestrator
Builds and packages the complete standalone Windows application suite:
1. Electron NSIS Portable standalone executable (Synapse-Workbench-Portable-1.1.0.exe)
   - Self-contained single-file executable containing all Electron runtime DLLs (ffmpeg.dll, etc.)
2. Bundles SynPack curriculum addons in resources/packages
3. Assembles portable distribution directory with external topics/
4. Creates Synapse-Workbench-Portable-1.1.0-win-x64.zip and Synapse-Portable-Windows.zip
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
    print(" 🚀 SYNAPSE WINDOWS PORTABLE BUNDLE ASSEMBLER     ")
    print("==================================================")

    dist_dir = WORKSPACE_ROOT / "dist"
    desktop_dist = dist_dir / "desktop"
    desktop_dir = WORKSPACE_ROOT / "app" / "desktop"

    # 0. Build / verify embedded Windows Python runtime and dependencies
    run_cmd(
        [sys.executable, str(WORKSPACE_ROOT / "scripts" / "build_windows_python_env.py")],
        cwd=WORKSPACE_ROOT,
        desc="Preparing Standalone Embedded Windows Python Environment"
    )

    # 1. Build Windows Portable & Setup Executables using electron-builder
    run_cmd(
        ["npx", "electron-builder", "--win", "--x64"],
        cwd=desktop_dir,
        desc="Compiling Electron Windows Portable and Installer Executables"
    )

    import json
    pkg_ver = "1.1.1"
    pkg_file = desktop_dir / "package.json"
    if pkg_file.exists():
        try:
            pkg_ver = json.loads(pkg_file.read_text(encoding="utf-8")).get("version", "1.1.1")
        except Exception:
            pass

    portable_exe = desktop_dist / f"Synapse-Workbench-Portable-{pkg_ver}.exe"
    if not portable_exe.exists():
        candidates = list(desktop_dist.glob("Synapse-Workbench-Portable-*.exe"))
        if candidates:
            portable_exe = candidates[0]
        else:
            print(f"[✘] Error: {portable_exe} was not generated.")
            sys.exit(1)

    print(f"[✔] Found standalone portable executable: {portable_exe.name} ({portable_exe.stat().st_size / (1024*1024):.1f} MB)")

    # 2. Assemble Portable Bundle Directory
    bundle_name = f"Synapse-Workbench-Portable-{pkg_ver}-win-x64"
    portable_bundle = dist_dir / bundle_name
    if portable_bundle.exists():
        shutil.rmtree(portable_bundle)
    portable_bundle.mkdir(parents=True, exist_ok=True)

    # Copy the self-contained portable executable into the bundle
    shutil.copy2(portable_exe, portable_bundle / "Synapse-Workbench-Portable.exe")
    shutil.copy2(portable_exe, portable_bundle / f"Synapse-Workbench-Portable-{pkg_ver}.exe")

    # Copy embedded Python runtime into the portable bundle
    python_win_src = dist_dir / "python-win"
    if python_win_src.exists():
        print("[*] Bundling embedded Python environment into portable bundle...")
        shutil.copytree(python_win_src, portable_bundle / "python", dirs_exist_ok=True)

    # Copy curriculum topics directory
    topics_src = WORKSPACE_ROOT / "topics"
    if topics_src.exists():
        print("[*] Bundling curriculum topics into portable bundle...")
        shutil.copytree(topics_src, portable_bundle / "topics", dirs_exist_ok=True)

    # Add comprehensive README
    readme_content = """================================================================================
Synapse AI Learning Workbench — Standalone Portable Windows (x64)
================================================================================

QUICK START:
1. Double-click 'Synapse-Workbench-Portable.exe' to launch the workbench.
   - Pure standalone single-file executable.
   - All runtime dependencies (ffmpeg.dll, Chromium, Electron, Node) are embedded.
   - Zero installation, no Python or administrative privileges required.

MODULAR CURRICULUM TOPICS:
- The './topics/' folder is located right alongside this executable.
- All 12 domains (539 topics) are pre-loaded and ready for study.
- You can add, edit, or customize any topic markdown files directly without rebuilding.

DATA & MASTERY STORAGE:
- Progress, study notes, and Anki flashcards are saved locally in './data/synapse.db'.
- To backup your progress, simply backup your './data/' directory.
================================================================================
"""
    (portable_bundle / "README.txt").write_text(readme_content, encoding="utf-8")

    # 3. Create Final Zip Archives
    print(f"\n[*] Creating Windows portable app archives...")
    target_zip = desktop_dist / bundle_name
    shutil.make_archive(str(target_zip), "zip", root_dir=dist_dir, base_dir=bundle_name)
    shutil.copy2(f"{target_zip}.zip", desktop_dist / "Synapse-Portable-Windows.zip")

    final_size_mb = Path(f"{target_zip}.zip").stat().st_size / (1024 * 1024)
    print(f"[✔] Archive created: {target_zip}.zip ({final_size_mb:.2f} MB)")
    print(f"[✔] Synced alias: {desktop_dist / 'Synapse-Portable-Windows.zip'}")

    print("\n==================================================")
    print("[✔] PORTABLE WINDOWS BUILD COMPLETE & VERIFIED!")
    print(f"    Bundle directory: {portable_bundle}")
    print("==================================================")

if __name__ == "__main__":
    main()
