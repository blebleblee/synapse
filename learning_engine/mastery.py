"""
User Topic Mastery State Tracker
Tracks competence states (not_started -> studying -> lab_verified -> mastered)
and persists progress into topics/mastery.json.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
MASTERY_FILE = WORKSPACE_ROOT / "topics" / "mastery.json"

VALID_STATES = ["not_started", "studying", "lab_verified", "mastered"]

def load_mastery_data() -> Dict[str, Any]:
    if MASTERY_FILE.exists():
        try:
            return json.loads(MASTERY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_mastery_data(data: Dict[str, Any]):
    tmp_file = MASTERY_FILE.with_suffix(".tmp")
    tmp_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp_file.replace(MASTERY_FILE)

def get_subtopic_mastery(subtopic_path: str) -> str:
    data = load_mastery_data()
    val = data.get(subtopic_path.strip("/"), "not_started")
    if isinstance(val, dict):
        return val.get("state", "not_started")
    return val

def get_completed_lessons(subtopic_path: str) -> List[str]:
    data = load_mastery_data()
    val = data.get(subtopic_path.strip("/"), None)
    if isinstance(val, dict):
        return val.get("completed_lessons", [])
    return []

def set_subtopic_mastery(subtopic_path: str, state: str) -> Dict[str, Any]:
    if state not in VALID_STATES:
        raise ValueError(f"Invalid mastery state '{state}'. Must be one of {VALID_STATES}")

    data = load_mastery_data()
    clean_path = subtopic_path.strip("/")
    val = data.get(clean_path, {})
    if isinstance(val, dict):
        val["state"] = state
        data[clean_path] = val
    else:
        data[clean_path] = {"state": state, "completed_lessons": []}
    save_mastery_data(data)

    return {
        "path": clean_path,
        "state": state,
        "completed_lessons": data[clean_path].get("completed_lessons", []),
        "stats": get_mastery_summary()
    }

def toggle_lesson_completion(subtopic_path: str, lesson_id: str, completed: Optional[bool] = None) -> Dict[str, Any]:
    data = load_mastery_data()
    clean_path = subtopic_path.strip("/")
    val = data.get(clean_path, "studying")
    if isinstance(val, str):
        state = val
        completed_lessons: List[str] = []
    else:
        state = val.get("state", "studying")
        completed_lessons = list(val.get("completed_lessons", []))

    if completed is None:
        if lesson_id in completed_lessons:
            completed_lessons.remove(lesson_id)
        else:
            completed_lessons.append(lesson_id)
    elif completed:
        if lesson_id not in completed_lessons:
            completed_lessons.append(lesson_id)
    else:
        if lesson_id in completed_lessons:
            completed_lessons.remove(lesson_id)

    # If any lessons are completed and state is not_started, advance to studying
    if completed_lessons and state == "not_started":
        state = "studying"

    data[clean_path] = {
        "state": state,
        "completed_lessons": sorted(completed_lessons)
    }
    save_mastery_data(data)

    return {
        "path": clean_path,
        "state": state,
        "completed_lessons": sorted(completed_lessons),
        "stats": get_mastery_summary()
    }

def get_mastery_summary() -> Dict[str, Any]:
    data = load_mastery_data()
    counts = {s: 0 for s in VALID_STATES}
    for val in data.values():
        s = val.get("state", "not_started") if isinstance(val, dict) else val
        if s in counts:
            counts[s] += 1

    total_tracked = len(data)
    mastered_count = counts["mastered"]
    percentage = (mastered_count * 100 // total_tracked) if total_tracked > 0 else 0

    return {
        "counts": counts,
        "total_tracked": total_tracked,
        "mastered_count": mastered_count,
        "percentage": percentage
    }
