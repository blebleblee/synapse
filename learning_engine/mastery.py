"""
User Topic Mastery State Tracker
Tracks competence states (not_started -> studying -> lab_verified -> mastered)
and persists progress into data/synapse.db.
"""

import json
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from .database import get_connection

VALID_STATES = ["not_started", "studying", "lab_verified", "mastered"]

def normalize_topic_path(path_or_str: str) -> str:
    """
    Normalizes a topic path into a canonical relative topic path (domain/discipline/topic).
    Strips leading and trailing slashes and any leading 'topics/' directory prefix.
    Preserves legitimate topic path components while ensuring consistent keys.
    """
    clean = str(path_or_str).strip().replace("\\", "/").strip("/")
    if clean.startswith("topics/"):
        clean = clean[7:].lstrip("/")
    return clean

def _fetch_topic_records(conn: sqlite3.Connection, canonical_path: str) -> Tuple[Optional[sqlite3.Row], Optional[sqlite3.Row]]:
    """
    Fetches the canonical row and legacy prefixed row for a given canonical topic path.
    Returns (canonical_row, legacy_row).
    """
    c_row = conn.execute("SELECT path, state, completed_lessons FROM mastery WHERE path = ?", (canonical_path,)).fetchone()
    l_row = conn.execute("SELECT path, state, completed_lessons FROM mastery WHERE path = ?", (f"topics/{canonical_path}",)).fetchone()
    return c_row, l_row

def resolve_topic_state(canonical_row: Optional[sqlite3.Row], legacy_row: Optional[sqlite3.Row]) -> Tuple[str, List[str]]:
    """
    Resolves the effective mastery state and merged completed lessons for a topic.
    - If canonical row exists, its state takes precedence; otherwise legacy state is used.
      Defaults to 'not_started' if neither exists.
    - Completed lessons from both rows are merged without duplicates, sorted.
    """
    state = "not_started"
    lessons_set = set()

    if legacy_row:
        state = legacy_row["state"]
        if legacy_row["completed_lessons"]:
            try:
                for l in json.loads(legacy_row["completed_lessons"]):
                    lessons_set.add(l)
            except Exception:
                pass

    if canonical_row:
        state = canonical_row["state"]
        if canonical_row["completed_lessons"]:
            try:
                for l in json.loads(canonical_row["completed_lessons"]):
                    lessons_set.add(l)
            except Exception:
                pass

    return state, sorted(list(lessons_set))

def get_subtopic_mastery(subtopic_path: str) -> str:
    clean_path = normalize_topic_path(subtopic_path)
    conn = get_connection()
    c_row, l_row = _fetch_topic_records(conn, clean_path)
    conn.close()
    state, _ = resolve_topic_state(c_row, l_row)
    return state

def get_completed_lessons(subtopic_path: str) -> List[str]:
    clean_path = normalize_topic_path(subtopic_path)
    conn = get_connection()
    c_row, l_row = _fetch_topic_records(conn, clean_path)
    conn.close()
    _, completed = resolve_topic_state(c_row, l_row)
    return completed

def set_subtopic_mastery(subtopic_path: str, state: str) -> Dict[str, Any]:
    if state not in VALID_STATES:
        raise ValueError(f"Invalid mastery state '{state}'. Must be one of {VALID_STATES}")

    clean_path = normalize_topic_path(subtopic_path)
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        c_row, l_row = _fetch_topic_records(conn, clean_path)
        # Preserve all merged completed lessons from both rows
        _, merged_lessons = resolve_topic_state(c_row, l_row)

        conn.execute("""
            INSERT INTO mastery (path, state, completed_lessons)
            VALUES (?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                state = excluded.state,
                completed_lessons = excluded.completed_lessons
        """, (clean_path, state, json.dumps(merged_lessons)))

        # Consolidate atomically: remove legacy row if it existed
        if l_row:
            conn.execute("DELETE FROM mastery WHERE path = ?", (f"topics/{clean_path}",))

        row = conn.execute("SELECT path, state, completed_lessons FROM mastery WHERE path = ?", (clean_path,)).fetchone()
        row_dict = {
            "path": row["path"],
            "state": row["state"],
            "completed_lessons": json.loads(row["completed_lessons"])
        }
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    row_dict["stats"] = get_mastery_summary()
    return row_dict

def toggle_lesson_completion(subtopic_path: str, lesson_id: str, completed: Optional[bool] = None) -> Dict[str, Any]:
    clean_path = normalize_topic_path(subtopic_path)
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        c_row, l_row = _fetch_topic_records(conn, clean_path)
        current_state, merged_lessons = resolve_topic_state(c_row, l_row)

        # Mutate targeted lesson while preserving all unrelated lessons
        if completed is None:
            if lesson_id in merged_lessons:
                merged_lessons.remove(lesson_id)
            else:
                merged_lessons.append(lesson_id)
        elif completed:
            if lesson_id not in merged_lessons:
                merged_lessons.append(lesson_id)
        else:
            if lesson_id in merged_lessons:
                merged_lessons.remove(lesson_id)

        merged_lessons.sort()

        # If marking lessons complete and state is not_started, advance to studying
        new_state = current_state
        if merged_lessons and new_state == "not_started":
            new_state = "studying"

        conn.execute("""
            INSERT INTO mastery (path, state, completed_lessons)
            VALUES (?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                state = excluded.state,
                completed_lessons = excluded.completed_lessons
        """, (clean_path, new_state, json.dumps(merged_lessons)))

        # Consolidate atomically: remove legacy row if it existed
        if l_row:
            conn.execute("DELETE FROM mastery WHERE path = ?", (f"topics/{clean_path}",))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {
        "path": clean_path,
        "state": new_state,
        "completed_lessons": merged_lessons,
        "stats": get_mastery_summary()
    }

def get_mastery_summary() -> Dict[str, Any]:
    conn = get_connection()
    rows = conn.execute("SELECT path, state, completed_lessons FROM mastery").fetchall()
    conn.close()

    grouped: Dict[str, List[sqlite3.Row]] = {}
    for row in rows:
        canon_path = normalize_topic_path(row["path"])
        grouped.setdefault(canon_path, []).append(row)

    counts = {s: 0 for s in VALID_STATES}
    for canon_path, r_list in grouped.items():
        c_row = next((r for r in r_list if normalize_topic_path(r["path"]) == r["path"]), None)
        l_row = next((r for r in r_list if str(r["path"]).startswith("topics/")), None)
        state, _ = resolve_topic_state(c_row, l_row)
        if state in counts:
            counts[state] += 1

    total_tracked = len(grouped)
    mastered_count = counts["mastered"]
    percentage = (mastered_count * 100 // total_tracked) if total_tracked > 0 else 0

    return {
        "counts": counts,
        "total_tracked": total_tracked,
        "mastered_count": mastered_count,
        "percentage": percentage
    }
