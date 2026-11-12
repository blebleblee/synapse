import re
from pathlib import Path
from typing import Union, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
TOPICS_DIR = WORKSPACE_ROOT / "topics"

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
        
        if not str(resolved_target).startswith(str(resolved_base)):
            raise ValueError(f"Security Violation: Path traversal attempt blocked: {target_path}")
            
        return resolved_target
    except Exception as e:
        raise ValueError(f"Invalid path structure: {e}")

def validate_canonical_topic_path(target_path: Path, base_topics_dir: Optional[Path] = None) -> Path:
    """
    Guarantees that any topic directory strictly adheres to the canonical 3-level taxonomy:
    topics/{domain}/{discipline}/{topic}
    Rejects any path deeper or shallower than 3 levels under topics/,
    or containing numbered prefixes (e.g. 01_*), or containing legacy level names.
    """
    base = (base_topics_dir or TOPICS_DIR).resolve()
    resolved = target_path.resolve()
    
    if not str(resolved).startswith(str(base)):
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


