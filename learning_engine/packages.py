"""
Synapse Curriculum Package Manager (SynPack)
Handles packaging, verification, installation, and management of modular topic addons.
"""

import os
import sys
import json
import tarfile
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from .security import validate_workspace_path, WORKSPACE_ROOT, TOPICS_DIR
from .database import get_db_connection

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
    Exports an entire domain or the complete global curriculum into a modular .synpack distribution archive.
    """
    out_dir = output_dir or PACKS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    if domain.lower() in ["all", "complete", "global"]:
        pack_path = out_dir / "synapse_complete_curriculum.synpack"
        lesson_count = len(list(TOPICS_DIR.rglob("lesson_*.md")))
        lab_count = len(list(TOPICS_DIR.rglob("labs.md")))
        topic_dirs = [p for p in TOPICS_DIR.glob("*/*/*") if (p / "labs.md").exists()]

        manifest = {
            "format": "synpack/v1",
            "domain": "complete",
            "title": "Synapse Master Global Curriculum (All 12 Domains)",
            "topic_count": len(topic_dirs),
            "lesson_count": lesson_count,
            "lab_count": lab_count,
            "domains": [d.name for d in TOPICS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]
        }

        manifest_path = out_dir / "complete_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        with tarfile.open(pack_path, "w:gz") as tar:
            for d in TOPICS_DIR.iterdir():
                if d.is_dir() and not d.name.startswith("."):
                    tar.add(d, arcname=f"topics/{d.name}")
            tar.add(manifest_path, arcname="manifest.json")

        manifest_path.unlink(missing_ok=True)
        return pack_path

    domain_dir = validate_workspace_path(TOPICS_DIR, TOPICS_DIR / domain)
    if not domain_dir.exists() or not domain_dir.is_dir():
        raise ValueError(f"Domain '{domain}' does not exist.")

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
    Extracts directly into TOPICS_DIR, preserving directory structure.
    Backs up existing domains prior to extraction to prevent data loss.
    """
    if not pack_path.exists():
        raise FileNotFoundError(f"Package file '{pack_path}' not found.")

    TOPICS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}

    with tarfile.open(pack_path, "r:gz") as tar:
        # Security: verify no path traversal in tar members
        for member in tar.getmembers():
            if member.name.startswith("/") or ".." in member.name:
                raise ValueError(f"Malicious package detected with path traversal member: {member.name}")

        try:
            manifest_member = tar.extractfile("manifest.json")
            if manifest_member:
                manifest = json.loads(manifest_member.read().decode("utf-8"))
        except KeyError:
            pass
            
        domain = manifest.get("domain") or pack_path.stem.replace(".synpack", "")
        
        # Backup existing domain if it exists
        target_domain_dir = TOPICS_DIR / domain
        if target_domain_dir.exists() and target_domain_dir.is_dir():
            import time, shutil
            backup_dir = WORKSPACE_ROOT / "exports" / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = backup_dir / f"{domain}_backup_{int(time.time())}"
            shutil.copytree(target_domain_dir, backup_path)
            print(f"[i] Backed up existing domain '{domain}' to {backup_path}")

        # Extract topics directly into TOPICS_DIR
        for member in tar.getmembers():
            if member.name == "manifest.json":
                continue

            # Strip leading "topics/" prefix if present in the archive
            rel_name = member.name
            if rel_name.startswith("topics/"):
                rel_name = rel_name[len("topics/"):]

            if not rel_name:
                continue

            target_path = TOPICS_DIR / rel_name

            if member.isdir():
                target_path.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                src = tar.extractfile(member)
                if src:
                    with src, open(target_path, "wb") as dst:
                        import shutil
                        shutil.copyfileobj(src, dst)

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

def resolve_or_download_pack(domain: str) -> Path:
    """
    Finds or downloads a .synpack archive for the given domain.
    1. Checks local PACKS_DIR / f"{domain}.synpack".
    2. Checks bundled Electron resources/packages directory.
    3. If domain is already on disk, exports it.
    4. Downloads from GitHub / Gitea v1.1.0 release.
    """
    out_dir = PACKS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    local_pack = out_dir / f"{domain}.synpack"
    if local_pack.exists() and local_pack.stat().st_size > 1000:
        return local_pack

    # Check Electron resources directory
    env_res = os.environ.get("SYNAPSE_RESOURCES_PATH")
    candidate_res = [
        Path(env_res) / "packages" if env_res else None,
        Path(sys.executable).resolve().parent.parent / "packages" if getattr(sys, "frozen", False) else None,
        WORKSPACE_ROOT / "exports" / "packages",
    ]
    for res_dir in candidate_res:
        if res_dir and res_dir.exists():
            bundled = res_dir / f"{domain}.synpack"
            if bundled.exists() and bundled.stat().st_size > 1000:
                return bundled

    # If domain directory already exists in TOPICS_DIR, export it
    if (TOPICS_DIR / domain).exists() and (TOPICS_DIR / domain).is_dir():
        return export_topic_pack(domain, output_dir=out_dir)

    # Download from remote release (GitHub primary, Gitea fallback)
    remote_urls = []
    custom_registry = os.environ.get("SYNAPSE_PACKAGE_REGISTRY")
    if custom_registry:
        remote_urls.append(f"{custom_registry.rstrip('/')}/{domain}.synpack")
        
    remote_urls.extend([
        f"https://github.com/blebleblee/synapse/releases/download/v1.1.1/{domain}.synpack",
        f"https://gitea.2464.cz/ai/synapse/releases/download/v1.1.1/{domain}.synpack",
    ])

    import urllib.request
    last_err = None
    for url in remote_urls:
        try:
            print(f"[*] Downloading curriculum pack for '{domain}' from {url}...")
            req = urllib.request.Request(url, headers={"User-Agent": "Synapse-Workbench/1.1.1"})
            
            # Allow basic token auth for private registries if provided
            if "github.com" not in url.lower() and os.environ.get("SYNAPSE_PACKAGE_TOKEN"):
                req.add_header("Authorization", f"Bearer {os.environ.get('SYNAPSE_PACKAGE_TOKEN')}")
                
            with urllib.request.urlopen(req, timeout=120) as resp:
                if resp.status == 200:
                    with open(local_pack, "wb") as f_out:
                        import shutil
                        shutil.copyfileobj(resp, f_out)
                    print(f"[✔] Downloaded {domain}.synpack ({local_pack.stat().st_size / 1024:.1f} KB)")
                    return local_pack
        except Exception as e:
            last_err = e
            print(f"[!] Failed to download from {url}: {e}")

    raise FileNotFoundError(f"Could not locate or download curriculum pack for domain '{domain}': {last_err}")

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
    Uninstalls a topic package by removing its files from TOPICS_DIR
    and unregistering it from the database.
    """
    import shutil
    domain_dir = TOPICS_DIR / domain

    # Safely remove domain directory from disk
    if domain_dir.exists() and domain_dir.is_dir():
        validate_workspace_path(TOPICS_DIR, domain_dir)
        shutil.rmtree(domain_dir)

    # Clean up settings and mastery tracking
    with get_db_connection() as conn:
        conn.execute("DELETE FROM settings WHERE key = ?", (f"pack:{domain}",))
        conn.execute("DELETE FROM mastery WHERE path LIKE ? OR path LIKE ?", (f"{domain}/%", f"topics/{domain}/%"))

    return {
        "status": "uninstalled",
        "domain": domain
    }

def seed_starter_curriculum():
    """
    If TOPICS_DIR is completely empty, attempts to seed it from
    synapse_complete_curriculum.synpack if found in bundled resources or PACKS_DIR.
    """
    from .topic_manager import list_domains
    if list_domains():
        return  # Already populated

    env_res = os.environ.get("SYNAPSE_RESOURCES_PATH")
    candidate_paths = [
        Path(env_res) / "packages" / "synapse_complete_curriculum.synpack" if env_res else None,
        Path(sys.executable).resolve().parent.parent / "packages" / "synapse_complete_curriculum.synpack" if getattr(sys, "frozen", False) else None,
        PACKS_DIR / "synapse_complete_curriculum.synpack",
        WORKSPACE_ROOT / "exports" / "packages" / "synapse_complete_curriculum.synpack",
    ]
    for p in candidate_paths:
        if p and p.exists() and p.stat().st_size > 1000:
            print(f"[*] Seeding starter curriculum from {p}...")
            try:
                install_topic_pack(p)
                print("[✔] Starter curriculum successfully seeded!")
                return
            except Exception as e:
                print(f"[!] Warning: Failed to auto-seed starter curriculum: {e}")

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

