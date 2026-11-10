"""
User Topic Mastery State Tracker
Tracks competence states (not_started -> studying -> lab_verified -> mastered)
and persists progress into topics/mastery.json.
"""

import json
from pathlib import Path
from typing import Dict, Any

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
    MASTERY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def get_subtopic_mastery(subtopic_path: str) -> str:
    data = load_mastery_data()
    return data.get(subtopic_path.strip("/"), "not_started")

def set_subtopic_mastery(subtopic_path: str, state: str) -> Dict[str, Any]:
    if state not in VALID_STATES:
        raise ValueError(f"Invalid mastery state '{state}'. Must be one of {VALID_STATES}")

    data = load_mastery_data()
    clean_path = subtopic_path.strip("/")
    data[clean_path] = state
    save_mastery_data(data)

    return {
        "path": clean_path,
        "state": state,
        "stats": get_mastery_summary()
    }

def get_mastery_summary() -> Dict[str, Any]:
    data = load_mastery_data()
    counts = {s: 0 for s in VALID_STATES}
    for s in data.values():
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
