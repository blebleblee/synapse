import os
import sys
import re
from pathlib import Path
from typing import Union, Optional

def get_workspace_root() -> Path:
    """
    Returns the root directory for the workspace.
    Supports:
    1. SYNAPSE_WORKSPACE environment variable override.
    2. Local development mode: Path(__file__).parent.parent if 'topics' or 'app' exists there.
    3. Safe user fallback for installed desktop/binary: ~/.synapse
    """
    if os.environ.get("SYNAPSE_WORKSPACE"):
        ws = Path(os.environ["SYNAPSE_WORKSPACE"]).resolve()
        ws.mkdir(parents=True, exist_ok=True)
        return ws

    # If running from source (development), use the repo root
    dev_root = Path(__file__).resolve().parent.parent
    if (dev_root / "topics").exists() or (dev_root / "app").exists():
        if not getattr(sys, "frozen", False):
            return dev_root

    # Default to ~/.synapse for all standalone, packaged, and desktop runtimes
    fallback = Path.home() / ".synapse"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback

def get_topics_dir() -> Path:
    """
    Returns the external, platform-independent topics addon directory.
    Supports:
    1. SYNAPSE_TOPICS_DIR environment variable override.
    2. Addon directory './topics' in workspace root.
    3. Addon directory './topics' in current working directory.
    """
    if os.environ.get("SYNAPSE_TOPICS_DIR"):
        t_dir = Path(os.environ["SYNAPSE_TOPICS_DIR"]).resolve()
        t_dir.mkdir(parents=True, exist_ok=True)
        return t_dir

    ws = get_workspace_root()
    if (ws / "topics").exists():
        return (ws / "topics").resolve()

    cwd_topics = Path.cwd() / "topics"
    if cwd_topics.exists():
        return cwd_topics.resolve()

    target = ws / "topics"
    target.mkdir(parents=True, exist_ok=True)
    return target.resolve()

WORKSPACE_ROOT = get_workspace_root()
TOPICS_DIR = get_topics_dir()

def sanitize_topic_path(domain: str, category: str, subtopic_id: str) -> tuple[str, str, str]:
    """Strict whitelist validation for topic path components."""
    pattern = re.compile(r"^[a-zA-Z0-9_\-]+$")
    
    for name, val in [("domain", domain), ("category", category), ("subtopic_id", subtopic_id)]:
        if not pattern.match(val):
            raise ValueError(f"Security Violation: Invalid {name} '{val}'. Use alphanumeric/underscore/hyphen only.")
            
    return domain, category, subtopic_id

def sanitize_query(query: str) -> str:
    """Validate and sanitize API query strings."""
    if not query:
        raise ValueError("Empty query")
    if len(query) > 256:
        raise ValueError("Query too long (max 256 characters)")
    if ".." in query or query.startswith("/"):
        raise ValueError("Path traversal detected")
    if not re.match(r'^[a-zA-Z0-9_/.-]+$', query):
        raise ValueError("Query contains forbidden characters")
    return query.strip()

def validate_workspace_path(base_dir: Path, target_path: Path) -> Path:
    """Ensure target_path resolves strictly within base_dir."""
    try:
        resolved_base = base_dir.resolve()
        resolved_target = target_path.resolve()
        
    except Exception as e:
        raise ValueError(f"Invalid path structure: {e}")

    # Component-wise containment check (a string prefix check would accept
    # sibling directories such as 'topics_backup' for base 'topics').
    if not resolved_target.is_relative_to(resolved_base):
        raise ValueError(f"Security Violation: Path traversal attempt blocked: {target_path}")

    return resolved_target

def validate_canonical_topic_path(target_path: Path, base_topics_dir: Optional[Path] = None) -> Path:
    """
    Guarantees that any topic directory strictly adheres to the canonical 3-level taxonomy:
    topics/{domain}/{discipline}/{topic}
    Rejects any path deeper or shallower than 3 levels under topics/,
    or containing numbered prefixes (e.g. 01_*), or containing legacy level names.
    """
    base = (base_topics_dir or TOPICS_DIR).resolve()
    resolved = target_path.resolve()
    
    if not resolved.is_relative_to(base):
        raise ValueError(f"Security Violation: Path traversal attempt: {target_path}")

    rel = resolved.relative_to(base)
    parts = rel.parts
    if len(parts) != 3:
        raise ValueError(
            f"Taxonomy violation: path '{rel}' has {len(parts)} levels. "
            f"Synapse curriculum strictly requires exactly 3 levels: topics/{{domain}}/{{discipline}}/{{topic}}"
        )

    for part in parts:
        if re.match(r"^\d{2}_", part):
            raise ValueError(
                f"Taxonomy violation: segment '{part}' in '{rel}' contains numbered prefix. "
                f"Lessons belong inside the canonical topic folder, not in numbered subdirectories."
            )
        if part.lower() in ("beginner", "intermediate", "advanced", "lessons"):
            raise ValueError(
                f"Taxonomy violation: segment '{part}' in '{rel}' is a legacy level directory."
            )

    return resolved

_LOOPBACK_HOSTNAMES = {"localhost", "127.0.0.1", "::1"}

# Browser origins of the bundled frontends (Vite dev server and Electron dev mode).
_DEFAULT_ALLOWED_ORIGINS = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}


def _split_env_list(name: str) -> set[str]:
    raw = os.environ.get(name, "")
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def _hostname_of(host_header: str) -> str:
    """Strips the port from a Host header value, handling bracketed IPv6."""
    h = (host_header or "").strip().lower()
    if h.startswith("["):
        return h[1:h.find("]")] if "]" in h else h
    if h.count(":") == 1:
        return h.split(":", 1)[0]
    return h


def is_allowed_host(host_header: Optional[str]) -> bool:
    """
    True if the request's Host header names this machine's loopback interface,
    or a host explicitly allowed via SYNAPSE_ALLOWED_HOSTS (comma-separated).

    Used when instance password protection is disabled, so that an
    unauthenticated instance is only reachable as localhost. This blocks
    LAN access to an open instance and DNS-rebinding attacks from websites.
    """
    if not host_header:
        return False
    name = _hostname_of(host_header)
    return name in _LOOPBACK_HOSTNAMES or name in _split_env_list("SYNAPSE_ALLOWED_HOSTS")


def is_allowed_origin(origin: Optional[str], host_header: Optional[str]) -> bool:
    """
    Validates a browser Origin header for state-changing / shell endpoints.
    Non-browser clients send no Origin and are allowed (they are still subject
    to Host and token checks). Browser requests must be same-origin with the
    backend, or come from a known frontend origin / SYNAPSE_ALLOWED_ORIGINS.
    """
    if origin is None:
        return True
    o = origin.strip().lower().rstrip("/")
    if o in _DEFAULT_ALLOWED_ORIGINS or o in _split_env_list("SYNAPSE_ALLOWED_ORIGINS"):
        return True
    if host_header:
        h = host_header.strip().lower()
        if o in (f"http://{h}", f"https://{h}"):
            return True
    return False


DANGEROUS_HOST_PATTERNS = [
    # Recursive deletion of root, home, current dir, wildcards, system dirs
    r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive)\s+.*(/|~|\*|\.\.|\.env|topics|app)",
    # Raw block device formatting and writing
    r"mkfs.*",
    r"dd\s+.*of=/dev/(r?disk|sd|nvme|zero|null)",
    r">\s*/dev/(r?disk|sd|nvme)",
    # Fork bombs
    r":\(\)\s*{\s*:\|:&\s*};\s*:",
    # System shutdown / reboot
    r"^(sudo\s+)?(shutdown|reboot|halt|init\s+0|poweroff)\b",
    # Global permissions destruction
    r"chmod\s+(-[a-zA-Z]*R)\s+(777|000)\s+(/|~)",
    # Destructive git operations on host
    r"git\s+reset\s+--hard\b",
    r"git\s+clean\s+(-[a-zA-Z]*f)",
]

def is_dangerous_host_command(cmd: str) -> bool:
    """
    Detects potentially destructive host system commands before they execute in host terminal mode.
    """
    clean = cmd.strip()
    if not clean:
        return False
    for pat in DANGEROUS_HOST_PATTERNS:
        if re.search(pat, clean, re.IGNORECASE):
            return True
    return False


