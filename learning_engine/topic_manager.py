"""
Topic and Curriculum Management (4-Level Architecture)
Domain (L1) -> Discipline (L2) -> Course (L3) -> Unit (L4)
Scans, navigates, and modifies the learning workspace filesystem hierarchy.
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
TOPICS_DIR = WORKSPACE_ROOT / "topics"

LEVELS = ["beginner", "intermediate", "advanced"]

def get_topics_dir() -> Path:
    return TOPICS_DIR

DOMAIN_ORDER = [
    "computing",
    "engineering",
    "motorsports",
    "crafts",
    "formal_sciences",
    "natural_sciences",
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

def scan_subtopic_status(unit_dir: Path) -> Dict[str, Any]:
    level_status = {}

    for lvl in LEVELS:
        lvl_dir = unit_dir / lvl
        f = (lvl_dir / "FOUNDATION.md").exists()
        l = (lvl_dir / "LESSON.md").exists()
        b = (lvl_dir / "LABS.md").exists()
        level_status[lvl] = {
            "has_foundation": f,
            "has_lesson": l,
            "has_labs": b,
            "complete": (f and l and b)
        }

    # Root file support
    root_f = (unit_dir / "FOUNDATION.md").exists()
    root_l = (unit_dir / "LESSON.md").exists()
    root_b = (unit_dir / "LABS.md").exists()

    has_foundation = any(s["has_foundation"] for s in level_status.values()) or root_f
    has_lesson = any(s["has_lesson"] for s in level_status.values()) or root_l
    has_labs = any(s["has_labs"] for s in level_status.values()) or root_b

    is_leveled_complete = all(s["complete"] for s in level_status.values())
    is_root_complete = (root_f and root_l and root_b)

    all_files = [f.name for f in unit_dir.iterdir() if f.is_file() and not f.name.startswith(".")] if unit_dir.exists() else []

    return {
        "has_foundation": has_foundation,
        "has_lesson": has_lesson,
        "has_labs": has_labs,
        "complete": is_leveled_complete or is_root_complete,
        "levels": level_status,
        "file_count": len(all_files),
        "files": all_files
    }

def get_topic_tree() -> Dict[str, Any]:
    tree = {}
    for domain in list_domains():
        domain_dir = TOPICS_DIR / domain
        syllabus_file = domain_dir / "SYLLABUS.md"
        tree[domain] = {
            "path": str(domain_dir.relative_to(WORKSPACE_ROOT)),
            "disciplines": {},
            "categories": {} # Backward-compatible alias
        }

        if not syllabus_file.exists():
            continue

        content = syllabus_file.read_text(encoding="utf-8")
        pattern = r"-\s+\*\*(.*?)\*\*\s+\(\`(.*?)/\`\)"
        matches = re.findall(pattern, content)

        for display_name, rel_path in matches:
            parts = rel_path.split("/")
            if len(parts) >= 3:
                disc = parts[0]
                course = parts[1]
                unit = "/".join(parts[2:])
            elif len(parts) == 2:
                disc = parts[0]
                course = parts[1]
                unit = "core"
            else:
                disc = "general"
                course = parts[0]
                unit = "core"

            if disc not in tree[domain]["disciplines"]:
                tree[domain]["disciplines"][disc] = {"courses": {}}
                tree[domain]["categories"][disc] = {}

            if course not in tree[domain]["disciplines"][disc]["courses"]:
                tree[domain]["disciplines"][disc]["courses"][course] = {"units": {}}

            unit_path = domain_dir / rel_path
            status = scan_subtopic_status(unit_path) if unit_path.exists() else {
                "has_foundation": False,
                "has_lesson": False,
                "has_labs": False,
                "complete": False,
                "levels": {},
                "file_count": 0,
                "files": []
            }

            node_data = {
                "display_name": display_name,
                "domain": domain,
                "discipline": disc,
                "course": course,
                "unit": unit,
                "rel_path": f"{domain}/{rel_path}",
                "full_path": str(unit_path),
                "status": status
            }

            tree[domain]["disciplines"][disc]["courses"][course]["units"][unit] = node_data
            # Backward-compatible flat mapping under categories
            flat_key = f"{course}_{unit}" if unit != "core" else course
            tree[domain]["categories"][disc][flat_key] = node_data

    return tree

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

    # 1. Exact relative match
    for domain, ddata in tree.items():
        for disc, disc_data in ddata["disciplines"].items():
            for course, c_data in disc_data["courses"].items():
                for unit, u_data in c_data["units"].items():
                    full_rel = u_data["rel_path"].lower()
                    course_unit = f"{course}/{unit}".lower()
                    if query == full_rel or query == course_unit or query == unit.lower():
                        return domain, f"{disc}/{course}", unit, Path(u_data["full_path"])

    # 2. Fuzzy match
    for domain, ddata in tree.items():
        for disc, disc_data in ddata["disciplines"].items():
            for course, c_data in disc_data["courses"].items():
                for unit, u_data in c_data["units"].items():
                    if query in u_data["rel_path"].lower() or query in u_data["display_name"].lower():
                        return domain, f"{disc}/{course}", unit, Path(u_data["full_path"])

    return None

def add_subtopic(domain: str, category: str, subtopic_id: str, display_name: Optional[str] = None) -> Path:
    domain_dir = TOPICS_DIR / domain
    if not domain_dir.exists():
        domain_dir.mkdir(parents=True, exist_ok=True)

    category_slug = category.lower().replace(" ", "_").replace("-", "_")
    subtopic_slug = subtopic_id.lower().replace(" ", "_").replace("-", "_")
    display_title = display_name or subtopic_id.replace("_", " ").title()

    target_dir = domain_dir / category_slug / subtopic_slug
    target_dir.mkdir(parents=True, exist_ok=True)

    # Update SYLLABUS.md
    syllabus_file = domain_dir / "SYLLABUS.md"
    rel_entry = f"{category_slug}/{subtopic_slug}"
    syllabus_entry = f"- **{display_title}** (`{rel_entry}/`)"

    if syllabus_file.exists():
        content = syllabus_file.read_text(encoding="utf-8")
        if rel_entry not in content:
            cat_header = f"### {category_slug.replace('_', ' ').title()}"
            if cat_header in content:
                parts = content.split(cat_header)
                new_content = parts[0] + cat_header + f"\n{syllabus_entry}" + parts[1]
                syllabus_file.write_text(new_content, encoding="utf-8")
            else:
                content += f"\n\n{cat_header}\n\n{syllabus_entry}\n"
                syllabus_file.write_text(content, encoding="utf-8")
    else:
        syllabus_file.write_text(f"# Syllabus: {domain.replace('_', ' ').title()}\n\n### {category_slug.replace('_', ' ').title()}\n\n{syllabus_entry}\n", encoding="utf-8")

    return target_dir
