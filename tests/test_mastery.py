"""
Tests for learning_engine.mastery
Verifies competence state transitions and atomic file persistence.
"""

import pytest
from learning_engine.mastery import (
    set_subtopic_mastery,
    get_subtopic_mastery,
    get_completed_lessons,
    toggle_lesson_completion,
    get_mastery_summary,
    VALID_STATES
)

def test_mastery_valid_states():
    assert "not_started" in VALID_STATES
    assert "studying" in VALID_STATES
    assert "lab_verified" in VALID_STATES
    assert "mastered" in VALID_STATES

def test_set_and_get_mastery():
    test_path = "computing/infrastructure/kubernetes/01_control_plane_and_etcd"
    orig_state = get_subtopic_mastery(test_path)

    try:
        # Transition to studying
        res = set_subtopic_mastery(test_path, "studying")
        assert res["state"] == "studying"
        assert get_subtopic_mastery(test_path) == "studying"

        # Transition to mastered
        res = set_subtopic_mastery(test_path, "mastered")
        assert res["state"] == "mastered"
        assert get_subtopic_mastery(test_path) == "mastered"

        summary = get_mastery_summary()
        assert summary["total_tracked"] >= 1
    finally:
        # Restore original state
        set_subtopic_mastery(test_path, orig_state)

def test_set_invalid_mastery_state():
    with pytest.raises(ValueError):
        set_subtopic_mastery("some/topic", "invalid_state_123")

def test_lesson_mastery_toggle():
    test_path = "computing/data/postgresql"
    orig_lessons = get_completed_lessons(test_path)
    orig_state = get_subtopic_mastery(test_path)

    try:
        # Mark lesson 1 complete
        res1 = toggle_lesson_completion(test_path, "lesson_01", completed=True)
        assert "lesson_01" in res1["completed_lessons"]
        assert "lesson_01" in get_completed_lessons(test_path)

        # Mark lesson 2 complete
        res2 = toggle_lesson_completion(test_path, "lesson_02", completed=True)
        assert "lesson_01" in res2["completed_lessons"]
        assert "lesson_02" in res2["completed_lessons"]

        # Toggle lesson 1 (turns off)
        res3 = toggle_lesson_completion(test_path, "lesson_01")
        assert "lesson_01" not in res3["completed_lessons"]
        assert "lesson_02" in res3["completed_lessons"]
    finally:
        set_subtopic_mastery(test_path, orig_state)
        # Restore lessons
        from learning_engine.database import get_connection
        import json
        conn = get_connection()
        with conn:
            conn.execute("UPDATE mastery SET completed_lessons = ? WHERE path = ?", (json.dumps(orig_lessons), test_path.strip("/")))
        conn.close()

def test_mastery_path_normalization_topics_prefix():
    """
    Demonstrates the reported defect:
    When a path with a 'topics/' prefix is passed (as sent by LessonViewer),
    it must refer to the exact same completion state as the canonical path
    without that prefix, for both reading and writing, including toggling off.
    """
    prefixed_path = "topics/computing/data/postgresql"
    canonical_path = "computing/data/postgresql"
    test_lesson = "lesson_01_foundations_and_invariants"

    # 1. Mark completed using prefixed path
    res = toggle_lesson_completion(prefixed_path, test_lesson, completed=True)
    assert test_lesson in res["completed_lessons"]

    # 2. Read back using canonical path (used by /api/tree and /api/topic)
    canonical_completed = get_completed_lessons(canonical_path)
    assert test_lesson in canonical_completed, (
        f"Expected {test_lesson} to be readable via canonical path '{canonical_path}', "
        f"but got {canonical_completed}"
    )

    # 3. Read back using prefixed path
    prefixed_completed = get_completed_lessons(prefixed_path)
    assert test_lesson in prefixed_completed

    # 4. Toggle completion off using canonical path
    res_off = toggle_lesson_completion(canonical_path, test_lesson, completed=False)
    assert test_lesson not in res_off["completed_lessons"]
    assert test_lesson not in get_completed_lessons(prefixed_path)
    assert test_lesson not in get_completed_lessons(canonical_path)

def test_mastery_legacy_only_row_behavior():
    """
    Verifies that when only a legacy 'topics/' row exists:
    1. Read operations do not modify the database.
    2. Reads return the legacy state and completed lessons via canonical path.
    3. Setting mastery uses the new state while preserving existing completed lessons.
    4. Successful writes consolidate into the canonical row and remove the legacy row atomically.
    """
    from learning_engine.database import get_connection
    import json

    canonical_path = "computing/data/postgresql"
    legacy_path = f"topics/{canonical_path}"

    # Insert legacy row directly via SQL
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM mastery WHERE path = ? OR path = ?", (canonical_path, legacy_path))
        conn.execute(
            "INSERT INTO mastery (path, state, completed_lessons) VALUES (?, ?, ?)",
            (legacy_path, "studying", json.dumps(["lesson_01", "lesson_02"]))
        )
    conn.close()

    # 1. Read operations: verify state and lessons resolve via canonical path
    conn = get_connection()
    before_rows = conn.execute("SELECT path, state, completed_lessons FROM mastery").fetchall()
    conn.close()
    assert len(before_rows) == 1
    assert before_rows[0]["path"] == legacy_path

    assert get_subtopic_mastery(canonical_path) == "studying"
    assert get_completed_lessons(canonical_path) == ["lesson_01", "lesson_02"]

    # Verify read operations did NOT modify the database
    conn = get_connection()
    after_read_rows = conn.execute("SELECT path, state, completed_lessons FROM mastery").fetchall()
    conn.close()
    assert len(after_read_rows) == 1
    assert after_read_rows[0]["path"] == legacy_path

    # 2. Setting mastery: uses new requested state while preserving merged completed lessons
    res = set_subtopic_mastery(canonical_path, "mastered")
    assert res["state"] == "mastered"
    assert res["completed_lessons"] == ["lesson_01", "lesson_02"]

    # Verify atomic consolidation: legacy row removed, canonical row persisted
    conn = get_connection()
    db_rows = conn.execute("SELECT path, state, completed_lessons FROM mastery").fetchall()
    conn.close()
    assert len(db_rows) == 1
    assert db_rows[0]["path"] == canonical_path
    assert db_rows[0]["state"] == "mastered"
    assert json.loads(db_rows[0]["completed_lessons"]) == ["lesson_01", "lesson_02"]

def test_mastery_both_rows_coexist_merging_and_consolidation():
    """
    Verifies that when both canonical and legacy 'topics/' rows coexist:
    1. Reads use the canonical state and merge completed lessons without duplicates.
    2. Read operations do not modify the database.
    3. Toggling completion preserves unrelated lessons and the resolved mastery state.
    4. Successful writes consolidate into the canonical row and remove the legacy row atomically.
    """
    from learning_engine.database import get_connection
    import json

    canonical_path = "computing/data/postgresql"
    legacy_path = f"topics/{canonical_path}"

    # Insert both canonical and legacy rows directly via SQL
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM mastery WHERE path = ? OR path = ?", (canonical_path, legacy_path))
        conn.execute(
            "INSERT INTO mastery (path, state, completed_lessons) VALUES (?, ?, ?)",
            (canonical_path, "mastered", json.dumps(["lesson_01", "lesson_03"]))
        )
        conn.execute(
            "INSERT INTO mastery (path, state, completed_lessons) VALUES (?, ?, ?)",
            (legacy_path, "studying", json.dumps(["lesson_02", "lesson_03"]))
        )
    conn.close()

    # 1. Reads: canonical state takes precedence, lessons merged without duplicates
    conn = get_connection()
    before_rows = conn.execute("SELECT path FROM mastery").fetchall()
    conn.close()
    assert len(before_rows) == 2

    assert get_subtopic_mastery(canonical_path) == "mastered"
    assert get_completed_lessons(canonical_path) == ["lesson_01", "lesson_02", "lesson_03"]

    # Verify read operations did not modify DB
    conn = get_connection()
    after_read_rows = conn.execute("SELECT path FROM mastery").fetchall()
    conn.close()
    assert len(after_read_rows) == 2

    # 2. Toggling completion: preserves unrelated lessons and resolved state
    toggle_res = toggle_lesson_completion(canonical_path, "lesson_04", completed=True)
    assert toggle_res["state"] == "mastered"
    assert toggle_res["completed_lessons"] == ["lesson_01", "lesson_02", "lesson_03", "lesson_04"]

    # Verify atomic consolidation into canonical row
    conn = get_connection()
    consolidated_rows = conn.execute("SELECT path, state, completed_lessons FROM mastery").fetchall()
    conn.close()
    assert len(consolidated_rows) == 1
    assert consolidated_rows[0]["path"] == canonical_path
    assert consolidated_rows[0]["state"] == "mastered"
    assert json.loads(consolidated_rows[0]["completed_lessons"]) == ["lesson_01", "lesson_02", "lesson_03", "lesson_04"]

def test_mastery_concurrent_lesson_updates_preserve_progress():
    """
    Verifies that concurrent updates to different lessons on separate connections
    to the same database do not lose progress, using BEGIN IMMEDIATE transactions.
    Synchronized using a threading.Barrier with a bounded timeout.
    """
    import threading
    from learning_engine.database import get_connection

    test_path = "computing/data/postgresql"
    # Ensure a clean slate for test_path
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM mastery WHERE path = ? OR path = ?", (test_path, f"topics/{test_path}"))
    conn.close()

    barrier = threading.Barrier(2)
    thread_exceptions = []

    def update_worker(lesson_id):
        try:
            # Synchronize threads so they attempt the read-modify-write simultaneously
            barrier.wait(timeout=5.0)
            toggle_lesson_completion(test_path, lesson_id, completed=True)
        except Exception as e:
            thread_exceptions.append(e)

    t1 = threading.Thread(target=update_worker, args=("lesson_01",))
    t2 = threading.Thread(target=update_worker, args=("lesson_02",))

    t1.start()
    t2.start()

    t1.join(timeout=5.0)
    t2.join(timeout=5.0)

    assert not t1.is_alive(), "Thread 1 timed out (potential deadlock)"
    assert not t2.is_alive(), "Thread 2 timed out (potential deadlock)"
    assert len(thread_exceptions) == 0, f"Concurrent worker raised exception: {thread_exceptions}"

    # Verify both updates persisted and neither progress was lost
    completed = get_completed_lessons(test_path)
    assert "lesson_01" in completed
    assert "lesson_02" in completed

def test_mastery_toggle_off_directly_seeded_legacy_progress():
    """
    Verifies toggling OFF a lesson present in a directly seeded legacy row
    BEFORE any earlier write has consolidated that row.
    - Start with canonical and legacy rows inserted via raw SQL.
    - Toggle OFF a lesson present in the legacy row.
    - Assert that lesson stays absent on subsequent reads, unrelated lessons remain,
      and only the canonical row remains after the write.
    """
    from learning_engine.database import get_connection
    import json

    canonical_path = "computing/data/postgresql"
    legacy_path = f"topics/{canonical_path}"

    # Directly insert both canonical and legacy rows via raw SQL
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM mastery WHERE path = ? OR path = ?", (canonical_path, legacy_path))
        conn.execute(
            "INSERT INTO mastery (path, state, completed_lessons) VALUES (?, ?, ?)",
            (canonical_path, "studying", json.dumps(["lesson_01", "lesson_02"]))
        )
        conn.execute(
            "INSERT INTO mastery (path, state, completed_lessons) VALUES (?, ?, ?)",
            (legacy_path, "studying", json.dumps(["lesson_02", "lesson_03"]))
        )
    conn.close()

    # Toggle OFF lesson_03 (which exists in the legacy row) BEFORE any prior consolidation
    res = toggle_lesson_completion(canonical_path, "lesson_03", completed=False)
    assert "lesson_03" not in res["completed_lessons"]
    assert "lesson_01" in res["completed_lessons"]
    assert "lesson_02" in res["completed_lessons"]

    # Assert lesson_03 stays absent on subsequent reads
    assert "lesson_03" not in get_completed_lessons(canonical_path)
    assert "lesson_03" not in get_completed_lessons(legacy_path)
    assert get_completed_lessons(canonical_path) == ["lesson_01", "lesson_02"]

    # Assert only the canonical row remains after the write
    conn = get_connection()
    rows = conn.execute("SELECT path, state, completed_lessons FROM mastery").fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0]["path"] == canonical_path
    assert json.loads(rows[0]["completed_lessons"]) == ["lesson_01", "lesson_02"]


def test_flashcard_spaced_repetition_review_workflow():
    from learning_engine.mastery import (
        record_flashcard_review,
        get_flashcard_review_status,
        get_due_flashcard_reviews,
        set_subtopic_mastery,
    )

    test_path = "computing/data/postgresql"
    set_subtopic_mastery(test_path, "studying")

    # Record first review with interval of 3 days
    res1 = record_flashcard_review(test_path, interval_days=3)
    assert res1["path"] == test_path
    assert res1["interval_days"] == 3
    assert "next_review_at" in res1

    status1 = get_flashcard_review_status(test_path)
    assert status1 is not None
    assert status1["review_count"] == 1
    assert status1["interval_days"] == 3

    # Record second review with interval of 7 days
    res2 = record_flashcard_review(test_path, interval_days=7)
    assert res2["interval_days"] == 7

    status2 = get_flashcard_review_status(test_path)
    assert status2["review_count"] == 2
    assert status2["interval_days"] == 7

    # Queue check returns a list of due items
    queue = get_due_flashcard_reviews()
    assert isinstance(queue, list)


