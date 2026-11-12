import re
from pathlib import Path
from typing import Union

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
