"""
Topic and Curriculum Management
Scans, navigates, and modifies the learning workspace filesystem hierarchy.
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
TOPICS_DIR = WORKSPACE_ROOT / "topics"

def get_topics_dir() -> Path:
    return TOPICS_DIR

def list_domains() -> List[str]:
    return [d.name for d in TOPICS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]

def get_domain_persona(domain: str) -> str:
    gemini_md = TOPICS_DIR / domain / "GEMINI.md"
    if gemini_md.exists():
        return gemini_md.read_text(encoding="utf-8")
    return "You are an expert educator and technical mentor."

def scan_subtopic_status(subtopic_dir: Path) -> Dict[str, Any]:
    levels = ["beginner", "intermediate", "advanced"]
    level_status = {}

    for lvl in levels:
        lvl_dir = subtopic_dir / lvl
        f = (lvl_dir / "FOUNDATION.md").exists()
        l = (lvl_dir / "LESSON.md").exists()
        b = (lvl_dir / "LABS.md").exists()
        level_status[lvl] = {
            "has_foundation": f,
            "has_lesson": l,
            "has_labs": b,
            "complete": (f and l and b)
        }

    # Backward compatibility with root files
    root_f = (subtopic_dir / "FOUNDATION.md").exists()
    root_l = (subtopic_dir / "LESSON.md").exists()
    root_b = (subtopic_dir / "LABS.md").exists()

    has_foundation = any(s["has_foundation"] for s in level_status.values()) or root_f
    has_lesson = any(s["has_lesson"] for s in level_status.values()) or root_l
    has_labs = any(s["has_labs"] for s in level_status.values()) or root_b

    is_leveled_complete = all(s["complete"] for s in level_status.values())
    is_root_complete = (root_f and root_l and root_b)

    all_files = [f.name for f in subtopic_dir.iterdir() if f.is_file() and not f.name.startswith(".")]

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
            "categories": {}
        }

        if not syllabus_file.exists():
            continue

        content = syllabus_file.read_text(encoding="utf-8")
        pattern = r"-\s+\*\*(.*?)\*\*\s+\(\`(.*?)/\`\)"
        matches = re.findall(pattern, content)

        for display_name, rel_path in matches:
            parts = rel_path.split("/")
            if len(parts) == 2:
                cat, sub = parts[0], parts[1]
            elif len(parts) == 1:
                cat, sub = "general", parts[0]
            else:
                cat, sub = parts[0], "/".join(parts[1:])

            if cat not in tree[domain]["categories"]:
                tree[domain]["categories"][cat] = {}

            sub_path = domain_dir / rel_path
            status = scan_subtopic_status(sub_path) if sub_path.exists() else {
                "has_foundation": False,
                "has_lesson": False,
                "has_labs": False,
                "complete": False,
                "file_count": 0,
                "files": []
            }

            tree[domain]["categories"][cat][sub] = {
                "display_name": display_name,
                "rel_path": f"{domain}/{rel_path}",
                "full_path": str(sub_path),
                "status": status
            }

    return tree

def resolve_subtopic(query: str) -> Optional[Tuple[str, str, str, Path]]:
    """
    Resolves a search query to (domain, category, subtopic, full_path).
    Supports:
      - Full path: computing_and_engineering/infrastructure_and_ops/linux
      - Category path: infrastructure_and_ops/linux
      - Subtopic name: linux
    """
    query = query.strip("/").lower()
    tree = get_topic_tree()

    # Exact full match
    for domain, ddata in tree.items():
        for cat, cdata in ddata["categories"].items():
            for sub, sdata in cdata.items():
                full_rel = sdata["rel_path"].lower()
                cat_rel = f"{cat}/{sub}".lower()
                if query == full_rel or query == cat_rel or query == sub.lower():
                    return domain, cat, sub, Path(sdata["full_path"])

    # Fuzzy endswith match
    for domain, ddata in tree.items():
        for cat, cdata in ddata["categories"].items():
            for sub, sdata in cdata.items():
                if sub.lower().startswith(query) or query in sub.lower():
                    return domain, cat, sub, Path(sdata["full_path"])

    return None

def add_subtopic(domain: str, category: str, subtopic_id: str, display_name: Optional[str] = None) -> Path:
    domain_dir = TOPICS_DIR / domain
    if not domain_dir.exists():
        raise ValueError(f"Domain '{domain}' does not exist.")

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
            # Check if category section exists
            cat_header = f"### {category_slug.replace('_', ' ').title()}"
            if cat_header in content:
                # Insert under category header
                parts = content.split(cat_header)
                new_content = parts[0] + cat_header + f"\n{syllabus_entry}" + parts[1]
                syllabus_file.write_text(new_content, encoding="utf-8")
            else:
                # Append new category section
                content += f"\n\n{cat_header}\n\n{syllabus_entry}\n"
                syllabus_file.write_text(content, encoding="utf-8")
    else:
        syllabus_file.write_text(f"# Syllabus: {domain.replace('_', ' ').title()}\n\n### {category_slug.replace('_', ' ').title()}\n\n{syllabus_entry}\n", encoding="utf-8")

    return target_dir
