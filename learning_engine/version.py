"""
Synapse Single Source of Truth Version Management
Reads the root VERSION file dynamically or falls back to package metadata.
"""

from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_VERSION_FILE = _ROOT / "VERSION"

if _VERSION_FILE.exists():
    __version__ = _VERSION_FILE.read_text(encoding="utf-8").strip()
else:
    __version__ = "1.2.0"
