"""
User Topic Mastery State Tracker
Tracks competence states (not_started -> studying -> lab_verified -> mastered)
and persists progress into data/synapse.db.
"""

import json
from typing import Dict, Any, List, Optional
from .database import get_connection

VALID_STATES = ["not_started", "studying", "lab_verified", "mastered"]

def get_subtopic_mastery(subtopic_path: str) -> str:
    clean_path = subtopic_path.strip("/")
    conn = get_connection()
    row = conn.execute("SELECT state FROM mastery WHERE path = ?", (clean_path,)).fetchone()
    conn.close()
    return row["state"] if row else "not_started"

def get_completed_lessons(subtopic_path: str) -> List[str]:
    clean_path = subtopic_path.strip("/")
    conn = get_connection()
    row = conn.execute("SELECT completed_lessons FROM mastery WHERE path = ?", (clean_path,)).fetchone()
    conn.close()
    if row and row["completed_lessons"]:
        return json.loads(row["completed_lessons"])
    return []

def set_subtopic_mastery(subtopic_path: str, state: str) -> Dict[str, Any]:
    if state not in VALID_STATES:
        raise ValueError(f"Invalid mastery state '{state}'. Must be one of {VALID_STATES}")

    clean_path = subtopic_path.strip("/")
    conn = get_connection()
    with conn:
        conn.execute("""
            INSERT INTO mastery (path, state, completed_lessons)
            VALUES (?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET state=excluded.state
        """, (clean_path, state, json.dumps([])))
    
    # Get updated row
    row = conn.execute("SELECT * FROM mastery WHERE path = ?", (clean_path,)).fetchone()
    conn.close()

    return {
        "path": row["path"],
        "state": row["state"],
        "completed_lessons": json.loads(row["completed_lessons"]),
        "stats": get_mastery_summary()
    }

def toggle_lesson_completion(subtopic_path: str, lesson_id: str, completed: Optional[bool] = None) -> Dict[str, Any]:
    clean_path = subtopic_path.strip("/")
    conn = get_connection()
    row = conn.execute("SELECT state, completed_lessons FROM mastery WHERE path = ?", (clean_path,)).fetchone()
    
    if row:
        state = row["state"]
        completed_lessons = json.loads(row["completed_lessons"])
    else:
        state = "studying"
        completed_lessons = []

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

    if completed_lessons and state == "not_started":
        state = "studying"

    with conn:
        conn.execute("""
            INSERT INTO mastery (path, state, completed_lessons)
            VALUES (?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET state=excluded.state, completed_lessons=excluded.completed_lessons
        """, (clean_path, state, json.dumps(sorted(completed_lessons))))
    conn.close()

    return {
        "path": clean_path,
        "state": state,
        "completed_lessons": sorted(completed_lessons),
        "stats": get_mastery_summary()
    }

def get_mastery_summary() -> Dict[str, Any]:
    conn = get_connection()
    rows = conn.execute("SELECT state FROM mastery").fetchall()
    conn.close()
    
    counts = {s: 0 for s in VALID_STATES}
    for row in rows:
        s = row["state"]
        if s in counts:
            counts[s] += 1

    total_tracked = len(rows)
    mastered_count = counts["mastered"]
    percentage = (mastered_count * 100 // total_tracked) if total_tracked > 0 else 0

    return {
        "counts": counts,
        "total_tracked": total_tracked,
        "mastered_count": mastered_count,
        "percentage": percentage
    }
