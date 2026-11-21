"""
Topic and Curriculum Management (3-Level Architecture)
Domain (L1) -> Discipline (L2) -> Topic (L3)
Scans, navigates, and modifies the learning workspace filesystem hierarchy.
"""

import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from learning_engine.mastery import get_completed_lessons
from learning_engine.security import sanitize_topic_path, validate_workspace_path, WORKSPACE_ROOT, TOPICS_DIR, get_topics_dir
from learning_engine.utils import scan_subtopic_status as utils_scan, get_unit_lessons as utils_get_lessons

_TOPIC_TREE_CACHE: Dict[str, Any] = {}
_TOPIC_TREE_CACHE_TS: float = 0.0
TOPIC_TREE_CACHE_TTL = 60.0  # Cache topic tree for 60 seconds

def invalidate_topic_tree_cache():
    """Invalidates the in-memory topic tree cache so next query reads fresh disk state."""
    global _TOPIC_TREE_CACHE, _TOPIC_TREE_CACHE_TS
    _TOPIC_TREE_CACHE = {}
    _TOPIC_TREE_CACHE_TS = 0.0

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
    if not TOPICS_DIR.exists():
        TOPICS_DIR.mkdir(parents=True, exist_ok=True)
        return []
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
    return utils_scan(unit_dir)

def get_topic_tree(force_refresh: bool = False) -> Dict[str, Any]:
    """Generates the full canonical 3-level taxonomy hierarchy (with in-memory cache)."""
    global _TOPIC_TREE_CACHE, _TOPIC_TREE_CACHE_TS
    now = time.time()
    if not force_refresh and _TOPIC_TREE_CACHE and (now - _TOPIC_TREE_CACHE_TS < TOPIC_TREE_CACHE_TTL):
        return _TOPIC_TREE_CACHE

    tree = {}
    for domain in list_domains():
        domain_dir = TOPICS_DIR / domain
        syllabus_file = domain_dir / "SYLLABUS.md"

        try:
            rel_domain_path = str(domain_dir.relative_to(WORKSPACE_ROOT))
        except ValueError:
            rel_domain_path = f"topics/{domain}"

        tree[domain] = {
            "path": rel_domain_path,
            "disciplines": {},
            "categories": {}
        }

        found_courses = set()
        course_display_names = {}

        if syllabus_file.exists():
            try:
                content = syllabus_file.read_text(encoding="utf-8", errors="replace")
            except Exception:
                content = ""
                
            pattern = r"-\s+\*\*(.*?)\*\*\s+\(\`(.*?)/\`\)"
            matches = re.findall(pattern, content)

            current_section = ""
            for line in content.splitlines():
                line_str = line.strip()
                if line_str.startswith("### "):
                    current_section = line_str.lstrip("#").strip()
                elif line_str.startswith("- **"):
                    m = re.match(r"-\s+\*\*(.*?)\*\*\s+\(\`(.*?)/\`\)", line_str)
                    if m:
                        _, u_rel = m.groups()
                        u_parts = u_rel.split("/")
                        u_disc = u_parts[0] if len(u_parts) >= 2 else "general"
                        u_course = u_parts[1] if len(u_parts) >= 2 else u_parts[0]

                        if current_section and (u_disc, u_course) not in course_display_names:
                            c_title = current_section.split(":", 1)[1].strip() if ":" in current_section else current_section
                            course_display_names[(u_disc, u_course)] = c_title if c_title.lower() != u_disc.lower() else u_course.replace("_", " ").title()

            for display_name, rel_path in matches:
                parts = rel_path.split("/")
                disc = parts[0] if len(parts) >= 1 else "general"
                course = parts[1] if len(parts) >= 2 else parts[0]
                unit = "core"
                clean_rel = f"{disc}/{course}"
                found_courses.add((disc, course))

                if disc not in tree[domain]["disciplines"]:
                    tree[domain]["disciplines"][disc] = {"courses": {}}
                    tree[domain]["categories"][disc] = {}

                c_display_title = display_name if len(parts) <= 2 else course_display_names.get((disc, course), course.replace("_", " ").title())

                if course not in tree[domain]["disciplines"][disc]["courses"]:
                    tree[domain]["disciplines"][disc]["courses"][course] = {
                        "display_name": c_display_title,
                        "units": {}
                    }

                full_path = TOPICS_DIR / domain / disc / course
                status = utils_scan(full_path)

                node_data = {
                    "display_name": c_display_title,
                    "domain": domain,
                    "discipline": disc,
                    "course": course,
                    "course_title": course_display_names.get((disc, course), course.replace("_", " ").title()),
                    "unit": unit,
                    "rel_path": f"{domain}/{clean_rel}",
                    "full_path": str(full_path),
                    "status": status,
                    "lessons": utils_get_lessons(full_path),
                    "completed_lessons": get_completed_lessons(f"{domain}/{clean_rel}"),
                    "has_summary": (full_path / "SUMMARY.md").exists()
                }

                tree[domain]["disciplines"][disc]["courses"][course]["units"][unit] = node_data
                flat_key = f"{course}_{unit}" if unit != "core" else course
                tree[domain]["categories"][disc][flat_key] = node_data

        # Dynamic filesystem discovery for topics not listed in SYLLABUS.md (or if SYLLABUS.md is missing)
        if domain_dir.exists():
            for disc_dir in sorted(domain_dir.iterdir(), key=lambda p: p.name):
                if not disc_dir.is_dir() or disc_dir.name.startswith("."):
                    continue

                # Check if disc_dir is directly a course (has lesson_*.md or labs.md)
                direct_lessons = list(disc_dir.glob("lesson_*.md")) or ((disc_dir / "labs.md").exists())
                if direct_lessons:
                    disc = "general"
                    course = disc_dir.name
                    if (disc, course) not in found_courses:
                        found_courses.add((disc, course))
                        if disc not in tree[domain]["disciplines"]:
                            tree[domain]["disciplines"][disc] = {"courses": {}}
                            tree[domain]["categories"][disc] = {}

                        c_display_title = course.replace("_", " ").title()
                        tree[domain]["disciplines"][disc]["courses"][course] = {
                            "display_name": c_display_title,
                            "units": {}
                        }
                        clean_rel = f"{disc}/{course}"
                        node_data = {
                            "display_name": c_display_title,
                            "domain": domain,
                            "discipline": disc,
                            "course": course,
                            "course_title": c_display_title,
                            "unit": "core",
                            "rel_path": f"{domain}/{clean_rel}",
                            "full_path": str(disc_dir),
                            "status": utils_scan(disc_dir),
                            "lessons": utils_get_lessons(disc_dir),
                            "completed_lessons": get_completed_lessons(f"{domain}/{clean_rel}"),
                            "has_summary": (disc_dir / "SUMMARY.md").exists()
                        }
                        tree[domain]["disciplines"][disc]["courses"][course]["units"]["core"] = node_data
                        tree[domain]["categories"][disc][course] = node_data
                    continue

                disc = disc_dir.name
                for course_dir in sorted(disc_dir.iterdir(), key=lambda p: p.name):
                    if not course_dir.is_dir() or course_dir.name.startswith("."):
                        continue
                    course = course_dir.name
                    if (disc, course) in found_courses:
                        continue

                    has_lessons = any(course_dir.glob("lesson_*.md")) or (course_dir / "labs.md").exists()
                    if not has_lessons:
                        continue

                    found_courses.add((disc, course))
                    if disc not in tree[domain]["disciplines"]:
                        tree[domain]["disciplines"][disc] = {"courses": {}}
                        tree[domain]["categories"][disc] = {}

                    c_display_title = course.replace("_", " ").title()
                    if course not in tree[domain]["disciplines"][disc]["courses"]:
                        tree[domain]["disciplines"][disc]["courses"][course] = {
                            "display_name": c_display_title,
                            "units": {}
                        }

                    clean_rel = f"{disc}/{course}"
                    node_data = {
                        "display_name": c_display_title,
                        "domain": domain,
                        "discipline": disc,
                        "course": course,
                        "course_title": c_display_title,
                        "unit": "core",
                        "rel_path": f"{domain}/{clean_rel}",
                        "full_path": str(course_dir),
                        "status": utils_scan(course_dir),
                        "lessons": utils_get_lessons(course_dir),
                        "completed_lessons": get_completed_lessons(f"{domain}/{clean_rel}"),
                        "has_summary": (course_dir / "SUMMARY.md").exists()
                    }

                    tree[domain]["disciplines"][disc]["courses"][course]["units"]["core"] = node_data
                    tree[domain]["categories"][disc][course] = node_data

    _TOPIC_TREE_CACHE = tree
    _TOPIC_TREE_CACHE_TS = now
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

    # 0. Support 4+ segment queries (e.g. domain/discipline/topic/lesson_id)
    q_parts = query.split("/")
    if len(q_parts) >= 4:
        trimmed_query = "/".join(q_parts[:3])
        match = resolve_subtopic(trimmed_query)
        if match:
            return match

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

    invalidate_topic_tree_cache()
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

    # Clean from mastery.db
    try:
        from .database import get_connection
        conn = get_connection()
        with conn:
            conn.execute("DELETE FROM mastery WHERE path = ?", (clean_rel,))
        conn.close()
    except Exception:
        pass

    invalidate_topic_tree_cache()
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

    invalidate_topic_tree_cache()
    return True
