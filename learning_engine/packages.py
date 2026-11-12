"""
Synapse Curriculum Package Manager (SynPack)
Handles packaging, verification, installation, and management of modular topic addons.
"""

import json
import tarfile
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from .security import validate_workspace_path
from .database import get_db_connection

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
TOPICS_DIR = WORKSPACE_ROOT / "topics"
PACKS_DIR = WORKSPACE_ROOT / "exports" / "packages"

def compute_checksum(file_path: Path) -> str:
    """Computes SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def export_topic_pack(domain: str, output_dir: Optional[Path] = None) -> Path:
    """
    Exports an entire domain or discipline into a modular .synpack distribution archive.
    """
    domain_dir = validate_workspace_path(TOPICS_DIR, TOPICS_DIR / domain)
    if not domain_dir.exists() or not domain_dir.is_dir():
        raise ValueError(f"Domain '{domain}' does not exist.")

    out_dir = output_dir or PACKS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    pack_path = out_dir / f"{domain}.synpack"

    # Count topics and lessons in this domain
    lesson_count = len(list(domain_dir.rglob("lesson_*.md")))
    lab_count = len(list(domain_dir.rglob("labs.md")))

    manifest = {
        "format": "synpack/v1",
        "domain": domain,
        "title": domain.replace("_", " ").title(),
        "lesson_count": lesson_count,
        "lab_count": lab_count,
    }

    manifest_path = out_dir / f"{domain}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    with tarfile.open(pack_path, "w:gz") as tar:
        tar.add(domain_dir, arcname=f"topics/{domain}")
        tar.add(manifest_path, arcname="manifest.json")

    manifest_path.unlink(missing_ok=True)
    return pack_path

def install_topic_pack(pack_path: Path) -> Dict[str, Any]:
    """
    Installs a .synpack archive into the local topics workspace.
    """
    if not pack_path.exists():
        raise FileNotFoundError(f"Package file '{pack_path}' not found.")

    manifest = {}
    with tarfile.open(pack_path, "r:gz") as tar:
        # Security: verify no path traversal in tar members
        for member in tar.getmembers():
            if member.name.startswith("/") or ".." in member.name:
                raise ValueError(f"Malicious package detected with path traversal member: {member.name}")

        manifest_member = tar.extractfile("manifest.json")
        if manifest_member:
            manifest = json.loads(manifest_member.read().decode("utf-8"))

        # Extract safely into workspace root
        tar.extractall(path=WORKSPACE_ROOT)

    domain = manifest.get("domain", pack_path.stem)
    # Record installed package in database
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """, (f"pack:{domain}", json.dumps(manifest)))

    return {
        "status": "installed",
        "domain": domain,
        "manifest": manifest
    }

def list_installed_packs() -> List[Dict[str, Any]]:
    """
    Lists all installed topic packages tracked in database or disk.
    """
    packs = []
    with get_db_connection() as conn:
        rows = conn.execute("SELECT key, value FROM settings WHERE key LIKE 'pack:%'").fetchall()
        for r in rows:
            try:
                packs.append(json.loads(r["value"]))
            except Exception:
                pass
    return packs

def uninstall_topic_pack(domain: str) -> Dict[str, Any]:
    """
    Unregisters an installed topic package from the database.
    """
    with get_db_connection() as conn:
        conn.execute("DELETE FROM settings WHERE key = ?", (f"pack:{domain}",))
    return {"status": "uninstalled", "domain": domain}

def get_domain_pack_info(domain: str) -> Dict[str, int]:
    """
    Calculates lesson and lab statistics for a given domain.
    """
    domain_dir = TOPICS_DIR / domain
    if not domain_dir.exists() or not domain_dir.is_dir():
        return {"lesson_count": 0, "lab_count": 0}
    lesson_count = len(list(domain_dir.rglob("lesson_*.md")))
    lab_count = len(list(domain_dir.rglob("labs.md")))
    return {"lesson_count": lesson_count, "lab_count": lab_count}

