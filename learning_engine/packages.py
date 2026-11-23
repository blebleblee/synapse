"""
Synapse Curriculum Package Manager (SynPack)
Handles packaging, verification, installation, and management of modular topic addons.
"""

import os
import sys
import re
import json
import tarfile
from .version import __version__
import hashlib
import shutil
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from .security import validate_workspace_path, WORKSPACE_ROOT, TOPICS_DIR, get_workspace_root
from .database import get_db_connection

def get_packs_dir() -> Path:
    return get_workspace_root() / "exports" / "packages"

PACKS_DIR = get_packs_dir()

def compute_checksum(file_path: Path) -> str:
    """Computes SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

# The 12 public curriculum domains shipped with this repository. Any other
# domain under topics/ is a private sideloaded pack: it works locally but must
# never be named in, or bundled into, a public pack.
CORE_DOMAINS = (
    "arts", "business", "computing", "crafts", "economics", "engineering",
    "formal_sciences", "health_sciences", "humanities", "languages",
    "motorsports", "natural_sciences",
)

# Personal, transient or private files that never belong in any pack.
_ALWAYS_EXCLUDED_DIRS = {"sessions", ".workspace_sessions", "__pycache__"}
_ALWAYS_EXCLUDED_FILES = {"active_session.md", "chat_history.json", "CURRICULUM_BLUEPRINT.md", ".DS_Store"}


def _git_ignored(paths: List[Path]) -> set:
    """
    Returns the subset of paths that git ignores, or an empty set if TOPICS_DIR
    is not inside a git work tree. Lets public packs honour .gitignore, which
    is where private sideloaded tracks inside core domains are declared.
    """
    if not paths:
        return set()
    import subprocess
    try:
        root = subprocess.run(
            ["git", "-C", str(TOPICS_DIR), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=10,
        )
        if root.returncode != 0:
            return set()
        res = subprocess.run(
            ["git", "-C", root.stdout.strip(), "check-ignore", "--stdin", "-z"],
            input="\0".join(str(p) for p in paths), capture_output=True, text=True, timeout=120,
        )
    except Exception:
        # No usable git (installed app, sandbox): nothing is treated as ignored.
        # Release packs are still verified by scripts/check_release_packs.py.
        return set()
    return {Path(x) for x in res.stdout.split("\0") if x}


def iter_pack_files(domain: str) -> List[Path]:
    """
    Files of a domain that may go into a pack. Session/chat files and private
    blueprints are always excluded. For the public core domains, files that git
    ignores (private sideloaded tracks) are excluded as well.
    """
    domain_dir = TOPICS_DIR / domain
    files = []
    for f in sorted(domain_dir.rglob("*")):
        if not f.is_file() or f.is_symlink():
            continue
        rel_parts = f.relative_to(domain_dir).parts
        if any(part in _ALWAYS_EXCLUDED_DIRS for part in rel_parts[:-1]):
            continue
        if f.name in _ALWAYS_EXCLUDED_FILES:
            continue
        files.append(f)
    if domain in CORE_DOMAINS:
        ignored = _git_ignored(files)
        files = [f for f in files if f not in ignored]
    return files


CURRICULUM_RELEASE_TAG = "curriculum"


def pack_content_digest(pack_path: Path) -> str:
    """SHA-256 over member names and file contents, in name order.

    Timestamps, ownership and gzip headers are left out, so re-exporting
    unchanged lessons gives the same digest even though the archive bytes differ.
    """
    h = hashlib.sha256()
    with tarfile.open(pack_path, "r:gz") as tar:
        for member in sorted(tar.getmembers(), key=lambda m: m.name):
            h.update(member.name.encode("utf-8") + b"\0")
            if member.isfile():
                data = tar.extractfile(member).read()
                h.update(len(data).to_bytes(8, "big") + data)
            else:
                h.update(b"D" if member.isdir() else b"?")
    return h.hexdigest()


def _add_files(tar: tarfile.TarFile, files: List[Path]) -> None:
    for f in files:
        tar.add(f, arcname=f"topics/{f.relative_to(TOPICS_DIR).as_posix()}", recursive=False)


def export_topic_pack(domain: str, output_dir: Optional[Path] = None) -> Path:
    """
    Exports a domain, or the complete public curriculum, into a .synpack archive.
    The complete pack contains only the core domains and names only them; packs
    never contain chat sessions, blueprints, or git-ignored private tracks.
    """
    out_dir = Path(output_dir) if output_dir else get_packs_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    if domain.lower() in ["all", "complete", "global"]:
        pack_path = out_dir / "synapse_complete_curriculum.synpack"
        included = [d for d in CORE_DOMAINS if (TOPICS_DIR / d).is_dir()]
        files_by_domain = {d: iter_pack_files(d) for d in included}
        all_files = [f for fs in files_by_domain.values() for f in fs]
        file_set = set(all_files)
        topic_dirs = [p for p in TOPICS_DIR.glob("*/*/*")
                      if p.parts[-3] in included and (p / "labs.md") in file_set]

        manifest = {
            "format": "synpack/v1",
            "domain": "complete",
            "title": "Synapse Master Global Curriculum (All 12 Domains)",
            "topic_count": len(topic_dirs),
            "lesson_count": sum(1 for f in all_files if f.name.startswith("lesson_") and f.suffix == ".md"),
            "lab_count": len(topic_dirs),
            "domains": included,
        }
        manifest_path = out_dir / "complete_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        with tarfile.open(pack_path, "w:gz") as tar:
            _add_files(tar, all_files)
            tar.add(manifest_path, arcname="manifest.json")
        manifest_path.unlink(missing_ok=True)
        return pack_path

    domain_dir = validate_workspace_path(TOPICS_DIR, TOPICS_DIR / domain)
    if not domain_dir.exists() or not domain_dir.is_dir():
        raise ValueError(f"Domain '{domain}' does not exist.")

    pack_path = out_dir / f"{domain}.synpack"
    files = iter_pack_files(domain)

    manifest = {
        "format": "synpack/v1",
        "domain": domain,
        "title": domain.replace("_", " ").title(),
        "lesson_count": sum(1 for f in files if f.name.startswith("lesson_") and f.suffix == ".md"),
        "lab_count": sum(1 for f in files if f.name == "labs.md"),
    }

    manifest_path = out_dir / f"{domain}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    with tarfile.open(pack_path, "w:gz") as tar:
        _add_files(tar, files)
        tar.add(manifest_path, arcname="manifest.json")

    manifest_path.unlink(missing_ok=True)
    return pack_path

_SLUG_RE = re.compile(r'^[a-zA-Z0-9_-]+$')


def _pack_relative_name(name: str) -> Optional[str]:
    """Archive member name relative to TOPICS_DIR, or None for the manifest and the root entry."""
    rel = name[2:] if name.startswith("./") else name
    rel = rel.rstrip("/")
    if rel in ("manifest.json", "topics", "."):
        return None
    if rel.startswith("topics/"):
        rel = rel[len("topics/"):]
    return rel or None


def install_topic_pack(pack_path: Path) -> Dict[str, Any]:
    """
    Installs a .synpack archive into the local topics workspace.

    Pack files replace their counterparts; other files in the domain stay.
    Every touched domain is backed up first. The pack is extracted into a
    hidden staging folder and each domain is swapped in by rename, so a
    failure while writing leaves the existing domains as they were.
    """
    if not pack_path.exists():
        raise FileNotFoundError(f"Package file '{pack_path}' not found.")

    TOPICS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}

    with tarfile.open(pack_path, "r:gz") as tar:
        # Security: verify no path traversal, unsafe links, or device nodes in tar members
        for member in tar.getmembers():
            if member.name.startswith("/") or ".." in member.name:
                raise ValueError(f"Malicious package detected with path traversal member: {member.name}")
            if member.issym() or member.islnk() or member.isdev():
                raise ValueError(f"Malicious package detected with unsafe link or device member: {member.name}")

        try:
            manifest_member = tar.extractfile("manifest.json")
            if manifest_member:
                raw_manifest = json.loads(manifest_member.read().decode("utf-8"))
                if isinstance(raw_manifest, dict):
                    manifest = raw_manifest
        except (KeyError, json.JSONDecodeError, UnicodeDecodeError):
            pass

        raw_domain = manifest.get("domain") or pack_path.stem.replace(".synpack", "")
        if not raw_domain or not isinstance(raw_domain, str) or not _SLUG_RE.match(raw_domain):
            raise ValueError(f"Invalid domain identifier '{raw_domain}' in package manifest or filename.")

        domain = raw_domain
        target_domain_dir = TOPICS_DIR / domain
        validate_workspace_path(TOPICS_DIR, target_domain_dir)

        # A pack may only write inside the domain(s) it declares: a domain pack
        # into its own folder, a complete pack into its listed domains (any
        # slug-named domain if an older manifest has no list).
        is_complete = domain.lower() in ("complete", "all", "global")
        listed = manifest.get("domains") if is_complete else None
        allowed = None
        if isinstance(listed, list) and all(isinstance(d, str) and _SLUG_RE.match(d) for d in listed):
            allowed = set(listed)
        elif not is_complete:
            allowed = {domain}
        touched_domains = set()
        for member in tar.getmembers():
            rel = _pack_relative_name(member.name)
            if rel is None:
                continue
            parts = rel.split("/")
            top = parts[0]
            touched_domains.add(top)
            in_domain = (allowed is None and _SLUG_RE.match(top)) or (allowed is not None and top in allowed)
            if not in_domain or (len(parts) == 1 and not member.isdir()):
                raise ValueError(f"Package member '{member.name}' is outside its domain '{domain}'.")

        # Back up every existing domain this pack writes into (a complete pack
        # replaces all of them), so local edits survive the install.
        stamp = int(time.time())
        for name in sorted(touched_domains):
            existing = TOPICS_DIR / name
            if existing.is_dir():
                backup_dir = WORKSPACE_ROOT / "exports" / "backups"
                backup_dir.mkdir(parents=True, exist_ok=True)
                backup_path = backup_dir / f"{name}_backup_{stamp}"
                shutil.copytree(existing, backup_path, dirs_exist_ok=True)
                print(f"[i] Backed up existing domain '{name}' to {backup_path}")

        # Stage inside TOPICS_DIR (same filesystem, so the swap is a rename;
        # dot-folders are ignored by the topic tree).
        staging = TOPICS_DIR / f".install-{stamp}-{os.getpid()}"
        try:
            pack_root = staging / "pack"
            for member in tar.getmembers():
                rel_name = _pack_relative_name(member.name)
                if rel_name is None:
                    continue
                target_path = pack_root / rel_name
                validate_workspace_path(pack_root, target_path)
                if member.isdir():
                    target_path.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    src = tar.extractfile(member)
                    if src:
                        with src, open(target_path, "wb") as dst:
                            shutil.copyfileobj(src, dst)

            # Merge each domain in staging: current content plus the pack's files.
            merged_root = staging / "merged"
            for name in sorted(touched_domains):
                merged = merged_root / name
                if (TOPICS_DIR / name).is_dir():
                    shutil.copytree(TOPICS_DIR / name, merged)
                if (pack_root / name).is_dir():
                    shutil.copytree(pack_root / name, merged, dirs_exist_ok=True)

            # Swap the merged domains in; put the old one back if a rename fails.
            old_root = staging / "old"
            old_root.mkdir(parents=True, exist_ok=True)
            for name in sorted(touched_domains):
                merged, live, old = merged_root / name, TOPICS_DIR / name, old_root / name
                if not merged.exists():
                    continue
                had_live = live.exists()
                if had_live:
                    os.replace(live, old)
                try:
                    os.replace(merged, live)
                except OSError:
                    if had_live:
                        os.replace(old, live)
                    raise
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    # Record installed package in database
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """, (f"pack:{domain}", json.dumps(manifest)))

    try:
        from .topic_manager import invalidate_topic_tree_cache
        invalidate_topic_tree_cache()
    except Exception:
        pass

    return {
        "status": "installed",
        "domain": domain,
        "manifest": manifest
    }

def resolve_or_download_pack(domain: str) -> Path:
    """
    Finds or downloads a .synpack archive for the given domain.
    1. Checks local PACKS_DIR / pack_name.
    2. Checks bundled Electron resources/packages directory.
    3. If domain is already on disk, exports it.
    4. Downloads from GitHub / Gitea release.
    """
    pack_name = "synapse_complete_curriculum.synpack" if domain in ("complete", "all", "synapse_complete_curriculum") else f"{domain}.synpack"
    out_dir = get_packs_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    local_pack = out_dir / pack_name
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
            bundled = res_dir / pack_name
            if bundled.exists() and bundled.stat().st_size > 1000:
                return bundled

    # If domain directory already exists in TOPICS_DIR, export it
    if domain not in ("complete", "all", "synapse_complete_curriculum") and (TOPICS_DIR / domain).exists() and (TOPICS_DIR / domain).is_dir():
        return export_topic_pack(domain, output_dir=out_dir)

    # Download from remote release (GitHub primary, Gitea fallback)
    remote_urls = []
    custom_registry = os.environ.get("SYNAPSE_PACKAGE_REGISTRY")
    if custom_registry:
        remote_urls.append(f"{custom_registry.rstrip('/')}/{pack_name}")
        
    # The `curriculum` release holds the current packs. App releases up to
    # 1.2.2 carried packs too; they stay as fallbacks.
    for tag in dict.fromkeys([CURRICULUM_RELEASE_TAG, f"v{__version__}", "v1.2.0"]):
        remote_urls.extend([
            f"https://github.com/blebleblee/synapse/releases/download/{tag}/{pack_name}",
            f"https://gitea.2464.cz/ai/synapse/releases/download/{tag}/{pack_name}",
        ])

    import urllib.request
    last_err = None
    for url in remote_urls:
        try:
            print(f"[*] Downloading curriculum pack for '{domain}' from {url}...")
            req = urllib.request.Request(url, headers={"User-Agent": f"Synapse-Workbench/{__version__}"})
            
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
    tracked_domains = set()

    with get_db_connection() as conn:
        rows = conn.execute("SELECT key, value FROM settings WHERE key LIKE 'pack:%'").fetchall()
        for r in rows:
            try:
                data = json.loads(r["value"])
                packs.append(data)
                if data.get("domain"):
                    tracked_domains.add(data.get("domain"))
            except Exception:
                pass

    # Discover physical domains present in TOPICS_DIR with generated curriculum
    if TOPICS_DIR.exists():
        for d in sorted(TOPICS_DIR.iterdir()):
            if d.is_dir() and not d.name.startswith((".", "_")) and d.name not in tracked_domains:
                stats = get_domain_pack_info(d.name)
                if stats["lesson_count"] > 0:
                    packs.append({
                        "domain": d.name,
                        "title": d.name.replace("_", " ").title(),
                        "lesson_count": stats["lesson_count"],
                        "lab_count": stats["lab_count"],
                        "format": "v1.2",
                        "status": "installed"
                    })
                    tracked_domains.add(d.name)

    # Filter out master complete bundle from individual domain list
    return [p for p in packs if p.get("domain") not in ("complete", "synapse_complete_curriculum")]

def uninstall_topic_pack(domain: str) -> Dict[str, Any]:
    """
    Uninstalls a topic package by removing its files from TOPICS_DIR
    and unregistering it from the database.
    """
    import re
    import shutil
    # One folder name only. "" or "." resolve to TOPICS_DIR itself, which the
    # containment check accepts, so they used to delete every course.
    if not isinstance(domain, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", domain):
        raise ValueError(f"Invalid domain name {domain!r}: use letters, digits, '_' or '-' only.")
    domain_dir = TOPICS_DIR / domain

    # Safely remove domain directory from disk
    if domain_dir.exists() and domain_dir.is_dir():
        resolved = validate_workspace_path(TOPICS_DIR, domain_dir)
        if resolved.parent != TOPICS_DIR.resolve():
            raise ValueError(f"Refusing to remove {domain_dir}: not a domain folder.")
        shutil.rmtree(domain_dir)

    # Clean up settings and mastery tracking
    with get_db_connection() as conn:
        conn.execute("DELETE FROM settings WHERE key = ?", (f"pack:{domain}",))
        conn.execute("DELETE FROM mastery WHERE path LIKE ? OR path LIKE ?", (f"{domain}/%", f"topics/{domain}/%"))

    try:
        from .topic_manager import invalidate_topic_tree_cache
        invalidate_topic_tree_cache()
    except Exception:
        pass

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
        get_packs_dir() / "synapse_complete_curriculum.synpack",
        get_workspace_root() / "exports" / "packages" / "synapse_complete_curriculum.synpack",
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

