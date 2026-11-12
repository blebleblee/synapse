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

def scan_subtopic_status(unit_dir: Path) -> Dict[str, Any]:
    all_unit_lessons = get_unit_lessons(unit_dir)
    sequential_lessons = [l for l in all_unit_lessons if l["id"].startswith("lesson_")]
    has_multi_lessons = len(sequential_lessons) >= 1
    has_labs = (unit_dir / "labs.md").exists() or (unit_dir / "LABS.md").exists()

    is_masterclass_complete = has_multi_lessons and has_labs

    all_files = [f.name for f in unit_dir.iterdir() if f.is_file() and not f.name.startswith(".")] if unit_dir.exists() else []

    return {
        "has_lesson": has_multi_lessons,
        "has_labs": has_labs,
        "complete": is_masterclass_complete,
        "is_legacy": False,
        "is_masterclass": is_masterclass_complete,
        "lesson_count": len(sequential_lessons),
        "lessons": [l["id"] for l in sequential_lessons],
        "file_count": len(all_files),
        "files": all_files
    }
