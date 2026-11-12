from pathlib import Path
from typing import Dict, Any, List

def get_unit_lessons(unit_dir: Path) -> List[Dict[str, str]]:
    if not unit_dir.exists():
        return []

    lessons = []
    # 1. Check for lesson_*.md in root of unit_dir
    files = sorted(list(unit_dir.glob("lesson_*.md")))
    # 2. Check for lessons/ directory
    lessons_subdir = unit_dir / "lessons"
    if lessons_subdir.exists():
        files.extend(sorted(list(lessons_subdir.glob("*.md"))))

    # 3. Fallback to artifacts/
    artifacts_dir = unit_dir / "artifacts"
    if not files and artifacts_dir.exists():
        files.extend(sorted(list(artifacts_dir.glob("lesson_*.md"))))

    for f in files:
        title = ""
        try:
            for line in f.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("# "):
                    title = line.lstrip("# ").strip()
                    break
        except Exception:
            pass
        if not title:
            # Prettify stem e.g. lesson_01_introduction -> Lesson 01: Introduction
            cleaned = f.stem.replace("lesson_", "Lesson ").replace("_", " ").title()
            title = cleaned

        lessons.append({
            "id": f.stem,
            "title": title,
            "filename": f.name,
            "path": str(f)
        })

    # If no sequential lessons, check for single LESSON.md
    if not lessons and (unit_dir / "LESSON.md").exists():
        f = unit_dir / "LESSON.md"
        title = "Technical Lesson"
        try:
            for line in f.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("# "):
                    title = line.lstrip("# ").strip()
                    break
        except Exception:
            pass
        lessons.append({
            "id": "lesson",
            "title": title,
            "filename": "LESSON.md",
            "path": str(f)
        })

    return lessons

def scan_subtopic_status(unit_dir: Path, levels: List[str]) -> Dict[str, Any]:
    level_status = {}
    for lvl in levels:
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

    root_f = (unit_dir / "FOUNDATION.md").exists() or (unit_dir / "foundation.md").exists()
    root_l = (unit_dir / "LESSON.md").exists() or (unit_dir / "lesson.md").exists()
    root_b = (unit_dir / "LABS.md").exists() or (unit_dir / "labs.md").exists()

    all_unit_lessons = get_unit_lessons(unit_dir)
    sequential_lessons = [l for l in all_unit_lessons if l["id"].startswith("lesson_")]
    has_multi_lessons = len(sequential_lessons) >= 1
    has_labs = (unit_dir / "labs.md").exists() or (unit_dir / "LABS.md").exists()

    has_foundation = any(s["has_foundation"] for s in level_status.values()) or root_f or has_multi_lessons
    has_lesson = any(s["has_lesson"] for s in level_status.values()) or root_l or has_multi_lessons

    is_leveled_complete = all(s["complete"] for s in level_status.values()) if level_status else False
    is_root_complete = (root_f and (root_l or has_multi_lessons) and root_b)
    is_masterclass_complete = has_multi_lessons and has_labs
    has_legacy_content = (is_leveled_complete or is_root_complete) and not is_masterclass_complete

    all_files = [f.name for f in unit_dir.iterdir() if f.is_file() and not f.name.startswith(".")] if unit_dir.exists() else []

    return {
        "has_foundation": has_foundation,
        "has_lesson": has_multi_lessons or has_lesson,
        "has_labs": has_labs,
        "complete": is_masterclass_complete,
        "is_legacy": has_legacy_content,
        "is_masterclass": is_masterclass_complete,
        "levels": level_status,
        "lesson_count": len(sequential_lessons),
        "lessons": [l["id"] for l in sequential_lessons],
        "file_count": len(all_files),
        "files": all_files
    }
