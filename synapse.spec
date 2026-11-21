# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Specification for Synapse Portable Windows/Cross-Platform Binary
Compiles the Synapse CLI and FastAPI Backend into a single self-contained executable.
Topics are explicitly excluded so they remain a modular, platform-independent addon.
"""

import sys
import os
from pathlib import Path

block_cipher = None
WORKSPACE_ROOT = Path(SPECPATH)

datas = [
    (str(WORKSPACE_ROOT / "learning_engine" / "templates"), "learning_engine/templates"),
]

# Include frontend static SPA build if present
frontend_dist = WORKSPACE_ROOT / "app" / "frontend" / "dist"
if frontend_dist.exists():
    datas.append((str(frontend_dist), "app/frontend/dist"))

hiddenimports = [
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "fastapi",
    "fastapi.staticfiles",
    "pydantic",
    "pydantic_core",
    "sqlite3",
    "websockets",
    "app.backend.main",
    "learning_engine",
    "learning_engine.cli",
    "learning_engine.models",
    "learning_engine.topic_manager",
    "learning_engine.security",
    "learning_engine.database",
    "learning_engine.generator",
    "learning_engine.enhancer",
    "learning_engine.linter",
    "learning_engine.reviewer",
    "learning_engine.search",
    "learning_engine.graph",
    "learning_engine.mastery",
    "learning_engine.auth",
    "learning_engine.config_manager",
    "learning_engine.domain_strategies",
    "learning_engine.summary",
    "edge_tts",
    "learning_engine.packages",
    "learning_engine.exporter",
    "learning_engine.flashcards",
    "learning_engine.utils",
]

a = Analysis(
    ["learning_engine/cli.py"],
    pathex=[str(WORKSPACE_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "topics",
        "tests",
        "node_modules",
        "app/desktop",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="synapse",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
