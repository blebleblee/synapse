#!/usr/bin/env python3
"""
Synapse Windows Embedded Python Packager
Downloads official Python 3.11 embeddable package for Windows x64,
installs all required runtime dependencies (fastapi, uvicorn, websockets, pydantic, etc.),
and packages the Synapse engine into dist/python-win for zero-dependency standalone bundling.
"""

import os
import sys
import shutil
import urllib.request
import zipfile
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DIST_PYTHON_WIN = WORKSPACE_ROOT / "dist" / "python-win"
EMBED_URL = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"

def main():
    print("==================================================")
    print(" 🐍 PREPARING WINDOWS STANDALONE EMBEDDED PYTHON  ")
    print("==================================================")

    DIST_PYTHON_WIN.mkdir(parents=True, exist_ok=True)
    zip_path = DIST_PYTHON_WIN / "python-embed.zip"

    # 1. Download official Python Windows x64 embeddable package if not already cached
    if not (DIST_PYTHON_WIN / "python.exe").exists():
        print(f"[*] Downloading official Python 3.11 embeddable Windows package from {EMBED_URL}...")
        req = urllib.request.Request(EMBED_URL, headers={"User-Agent": "Synapse-Builder/1.1.0"})
        with urllib.request.urlopen(req) as resp, open(zip_path, "wb") as f_out:
            shutil.copyfileobj(resp, f_out)
        print(f"[✔] Downloaded ({zip_path.stat().st_size / (1024*1024):.1f} MB)")

        print("[*] Extracting Python embeddable runtime...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(DIST_PYTHON_WIN)
        zip_path.unlink(missing_ok=True)
        print("[✔] Python runtime extracted.")

    # 2. Enable site-packages in python311._pth
    pth_file = DIST_PYTHON_WIN / "python311._pth"
    pth_content = """python311.zip
.
site-packages
import site
"""
    pth_file.write_text(pth_content, encoding="utf-8")
    print("[✔] Configured python311._pth with site-packages support.")

    # 3. Install required dependencies into site-packages using pip cross-platform install
    site_packages = DIST_PYTHON_WIN / "site-packages"
    site_packages.mkdir(parents=True, exist_ok=True)

    runtime_deps = [
        "fastapi>=0.115.0",
        "uvicorn>=0.32.0",
        "websockets>=13.0",
        "pydantic>=2.9.0",
        "requests>=2.32.0",
        "python-multipart>=0.0.12",
        "edge-tts>=7.0.0",
        "msvc-runtime>=14.40.0",
        "pywinpty>=2.0.14",
    ]

    print("[*] Cross-installing Windows x64 binary dependencies into site-packages...")
    cmd = [
        sys.executable, "-m", "pip", "install",
        "--target", str(site_packages),
        "--platform", "win_amd64",
        "--python-version", "311",
        "--only-binary=:all:",
        "--upgrade"
    ] + runtime_deps

    res = subprocess.run(cmd)
    if res.returncode != 0:
        print(f"[✘] Error installing dependencies: exit code {res.returncode}")
        sys.exit(res.returncode)
    print("[✔] Windows binary dependencies installed.")

    # Copy all MSVC runtime DLLs into root of DIST_PYTHON_WIN so all .pyd modules find them
    for dll in site_packages.rglob("*.dll"):
        if any(name in dll.name.lower() for name in ["msvcp", "vcruntime", "vcomp", "concrt"]):
            shutil.copy2(dll, DIST_PYTHON_WIN / dll.name)
            print(f"[✔] Placed MSVC runtime DLL: {dll.name}")

    # 4. Copy Synapse learning_engine and app.backend modules into site-packages
    print("[*] Bundling learning_engine and app.backend modules...")
    le_src = WORKSPACE_ROOT / "learning_engine"
    le_dst = site_packages / "learning_engine"
    if le_dst.exists():
        shutil.rmtree(le_dst)
    shutil.copytree(le_src, le_dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))

    app_pkg = site_packages / "app"
    if app_pkg.exists():
        shutil.rmtree(app_pkg)
    app_pkg.mkdir(parents=True, exist_ok=True)
    (app_pkg / "__init__.py").write_text("", encoding="utf-8")

    backend_src = WORKSPACE_ROOT / "app" / "backend"
    backend_dst = app_pkg / "backend"
    shutil.copytree(backend_src, backend_dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))

    frontend_dist = WORKSPACE_ROOT / "app" / "frontend" / "dist"
    if frontend_dist.exists():
        frontend_dst = app_pkg / "frontend" / "dist"
        shutil.copytree(frontend_dist, frontend_dst, dirs_exist_ok=True)
        print("[✔] Frontend SPA dist bundled in site-packages/app/frontend/dist.")

    print("[✔] Synapse engine modules bundled.")

    # 5. Create launcher batch script in DIST_PYTHON_WIN
    synapse_cmd = DIST_PYTHON_WIN / "synapse.cmd"
    synapse_cmd.write_text('@echo off\r\n"%~dp0python.exe" -m learning_engine.cli %*\r\n', encoding="utf-8")
    print(f"[✔] Created launcher script: {synapse_cmd}")

    total_size = sum(f.stat().st_size for f in DIST_PYTHON_WIN.rglob("*") if f.is_file()) / (1024 * 1024)
    print("==================================================")
    print(f"[✔] EMBEDDED WINDOWS PYTHON READY! ({total_size:.1f} MB)")
    print(f"    Location: {DIST_PYTHON_WIN}")
    print("==================================================")

if __name__ == "__main__":
    main()
