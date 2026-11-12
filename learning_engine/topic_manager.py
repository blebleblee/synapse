"""
Topic and Curriculum Management (4-Level Architecture)
Domain (L1) -> Discipline (L2) -> Course (L3) -> Unit (L4)
Scans, navigates, and modifies the learning workspace filesystem hierarchy.
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from learning_engine.mastery import get_completed_lessons
from learning_engine.security import sanitize_topic_path, validate_workspace_path
from learning_engine.services import TaxonomyService
from learning_engine.utils import scan_subtopic_status as utils_scan, get_unit_lessons as utils_get_lessons
from learning_engine.constants import LEVELS

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
TOPICS_DIR = validate_workspace_path(WORKSPACE_ROOT, WORKSPACE_ROOT / "topics")
TAXONOMY = TaxonomyService(TOPICS_DIR, WORKSPACE_ROOT)

LEVELS = ["beginner", "intermediate", "advanced"]

def get_topics_dir() -> Path:
    return TOPICS_DIR

def sanitize_rel_path(rel_path: str) -> Path:
    """Deprecated: Use validate_workspace_path instead."""
    return validate_workspace_path(TOPICS_DIR, TOPICS_DIR / rel_path)

DOMAIN_ORDER = [
    "computing",
    "engineering",
    "motorsports",
    "crafts",
    "formal_sciences",
    "natural_sciences",
    "health_sciences",
    "arts",
    "languages",
    "humanities",
    "business",
    "economics"
]

def list_domains() -> List[str]:
    raw = [d.name for d in TOPICS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]
    return sorted(raw, key=lambda d: DOMAIN_ORDER.index(d) if d in DOMAIN_ORDER else 999)

def get_domain_persona(domain: str) -> str:
    gemini_md = TOPICS_DIR / domain / "GEMINI.md"
    if gemini_md.exists():
        return gemini_md.read_text(encoding="utf-8")
    return "You are an expert educator and technical mentor."

def get_unit_lessons(unit_dir: Path) -> List[Dict[str, str]]:
    return utils_get_lessons(unit_dir)

def scan_subtopic_status(unit_dir: Path) -> Dict[str, Any]:
    return utils_scan(unit_dir, LEVELS)

def get_topic_tree() -> Dict[str, Any]:
    """Wraps TaxonomyService to maintain API compatibility."""
    return TAXONOMY.get_topic_tree()

def resolve_subtopic(query: str) -> Optional[Tuple[str, str, str, Path]]:
    """
    Resolves a search query to (domain, discipline, unit_slug, full_path).
    Supports:
      - 4-level path: computing/infrastructure/kubernetes/01_control_plane
      - 2-level path: kubernetes/01_control_plane
      - Slug: 01_control_plane or kubernetes
    """
    query = query.strip("/").lower()
    tree = get_topic_tree()

    # 1. Exact relative match or exact course/unit slug match
    for domain, ddata in tree.items():
        for disc, disc_data in ddata["disciplines"].items():
            for course, c_data in disc_data["courses"].items():
                for unit, u_data in c_data["units"].items():
                    full_rel = u_data["rel_path"].lower()
                    course_unit = f"{course}/{unit}".lower()
                    if (query == full_rel or
                        query == course_unit or
                        query == unit.lower() or
                        query == course.lower() or
                        query == f"{disc}/{course}".lower()):
                        target_p = validate_workspace_path(TOPICS_DIR, Path(u_data["full_path"]))
                        cat_val = disc if unit == "core" else f"{disc}/{course}"
                        sub_val = course if unit == "core" else unit
                        return domain, cat_val, sub_val, target_p

    # 2. Fuzzy match
    for domain, ddata in tree.items():
        for disc, disc_data in ddata["disciplines"].items():
            for course, c_data in disc_data["courses"].items():
                for unit, u_data in c_data["units"].items():
                    if query in u_data["rel_path"].lower() or query in u_data["display_name"].lower():
                        target_p = validate_workspace_path(TOPICS_DIR, Path(u_data["full_path"]))
                        cat_val = disc if unit == "core" else f"{disc}/{course}"
                        sub_val = course if unit == "core" else unit
                        return domain, cat_val, sub_val, target_p

    return None

def add_subtopic(domain: str, category: str, subtopic_id: str, display_name: Optional[str] = None) -> Path:
    # 1. Sanitize components
    domain, category, subtopic_id = sanitize_topic_path(domain, category, subtopic_id)
    
    # 2. Construct and validate absolute path
    domain_dir = TOPICS_DIR / domain
    target_dir = validate_workspace_path(TOPICS_DIR, domain_dir / category / subtopic_id)
    
    target_dir.mkdir(parents=True, exist_ok=True)

    rel_entry = f"{category}/{subtopic_id}"
    display_title = display_name or subtopic_id.replace("_", " ").title()
    syllabus_file = domain_dir / "SYLLABUS.md"
    syllabus_entry = f"- **{display_title}** (`{rel_entry}/`)"

    if syllabus_file.exists():
        content = syllabus_file.read_text(encoding="utf-8")
        if rel_entry not in content:
            parts = category.split("/")
            header_name = parts[-1].replace("_", " ").title()
            cat_header = f"### {header_name}"
            if cat_header in content:
                p = content.split(cat_header)
                new_content = p[0] + cat_header + f"\n{syllabus_entry}" + p[1]
                syllabus_file.write_text(new_content, encoding="utf-8")
            else:
                content += f"\n\n{cat_header}\n\n{syllabus_entry}\n"
                syllabus_file.write_text(content, encoding="utf-8")
    else:
        syllabus_file.write_text(f"# Syllabus: {domain.replace('_', ' ').title()}\n\n### {category.replace('_', ' ').title()}\n\n{syllabus_entry}\n", encoding="utf-8")

    return target_dir

def delete_subtopic(rel_path: str) -> bool:
    # Strict validation
    target_dir = validate_workspace_path(TOPICS_DIR, TOPICS_DIR / rel_path)
    
    clean_rel = rel_path.strip("/")
    parts = clean_rel.split("/")
    if len(parts) < 2:
        return False

    domain = parts[0]
    sub_rel = "/".join(parts[1:])

    import shutil
    if target_dir.exists():
        shutil.rmtree(target_dir)

    # Clean from SYLLABUS.md
    syllabus_file = TOPICS_DIR / domain / "SYLLABUS.md"
    if syllabus_file.exists():
        lines = syllabus_file.read_text(encoding="utf-8").splitlines()
        filtered = [l for l in lines if f"`{sub_rel}/`" not in l and f"`{sub_rel}`" not in l]
        syllabus_file.write_text("\n".join(filtered) + "\n", encoding="utf-8")

    # Clean from mastery.json
    try:
        from .mastery import load_mastery_data, save_mastery_data
        mdata = load_mastery_data()
        if clean_rel in mdata:
            del mdata[clean_rel]
            save_mastery_data(mdata)
    except Exception:
        pass

    # Git commit and push
    try:
        import subprocess
        subprocess.run(["git", "add", "-A"], check=True, cwd=str(WORKSPACE_ROOT), capture_output=True)
        subprocess.run(["git", "commit", "-m", f"chore(topics): remove topic {clean_rel}"], check=True, cwd=str(WORKSPACE_ROOT), capture_output=True)
        subprocess.run(["git", "push", "origin", "main"], check=False, cwd=str(WORKSPACE_ROOT), capture_output=True)
    except Exception:
        pass

    return True

def rename_subtopic(rel_path: str, new_title: str) -> bool:
    try:
        sanitize_rel_path(rel_path)
    except ValueError:
        return False

    clean_rel = rel_path.strip("/")
    parts = clean_rel.split("/")
    if len(parts) < 2:
        return False

    domain = parts[0]
    sub_rel = "/".join(parts[1:])
    syllabus_file = TOPICS_DIR / domain / "SYLLABUS.md"
    if not syllabus_file.exists():
        return False

    lines = syllabus_file.read_text(encoding="utf-8").splitlines()
    new_lines = []
    pattern = f"`{sub_rel}/`"
    for l in lines:
        if pattern in l:
            new_lines.append(f"- **{new_title}** (`{sub_rel}/`)")
        else:
            new_lines.append(l)

    syllabus_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    # Git commit and push
    try:
        import subprocess
        subprocess.run(["git", "add", str(syllabus_file)], check=True, cwd=str(WORKSPACE_ROOT), capture_output=True)
        subprocess.run(["git", "commit", "-m", f"chore(topics): rename topic {clean_rel} to '{new_title}'"], check=True, cwd=str(WORKSPACE_ROOT), capture_output=True)
        subprocess.run(["git", "push", "origin", "main"], check=False, cwd=str(WORKSPACE_ROOT), capture_output=True)
    except Exception:
        pass

    return True
