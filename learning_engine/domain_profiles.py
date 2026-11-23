"""
Per-domain generation profiles.

A domain folder may contain DOMAIN_PROFILE.json with prompt templates for
course generation. Domains that live outside this repository use it, so that
their templates (and names) are not part of the public code. Profiles are data:
templates are text with {placeholders}, never code. Public domains have none
and use the built-in templates.

    {
      "version": 1,
      "music_style": true,                        # chapters use the music template
      "outline_lesson": {"structure": "...", "relevance": "..."},   # TOPIC_OUTLINE lessons
      "outline_capstone": "...",                  # TOPIC_OUTLINE capstone lab
      "scoped_lesson": {"structure": "..."}       # AI-scoped lessons
    }
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from . import security

PROFILE_FILENAME = "DOMAIN_PROFILE.json"
_DOMAIN_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_PLACEHOLDER = re.compile(r"\{(\w+)\}")


def domain_profile(domain: str, subtopic_dir: Optional[Path] = None) -> Dict[str, Any]:
    """The domain's profile, or {} when it has none (or it is unreadable).
    Looked up next to the course (subtopic_dir/../..) first, then in TOPICS_DIR."""
    if not _DOMAIN_RE.match(domain or ""):
        return {}
    candidates = []
    if subtopic_dir is not None:
        candidates.append(Path(subtopic_dir).parent.parent / PROFILE_FILENAME)
    candidates.append(Path(security.TOPICS_DIR) / domain / PROFILE_FILENAME)
    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict):
            return data
    return {}


def render_profile_template(template: str, values: Mapping[str, Any]) -> str:
    """Fills {name} for the names in `values`; any other braces stay as written."""
    if not isinstance(template, str):
        return ""
    return _PLACEHOLDER.sub(lambda m: str(values[m.group(1)]) if m.group(1) in values else m.group(0), template)
