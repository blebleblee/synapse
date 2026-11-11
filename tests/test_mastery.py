"""
Tests for learning_engine.mastery
Verifies competence state transitions and atomic file persistence.
"""

import pytest
from learning_engine.mastery import (
    load_mastery_data,
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
        data = load_mastery_data()
        clean_path = test_path.strip("/")
        if clean_path in data and isinstance(data[clean_path], dict):
            data[clean_path]["completed_lessons"] = orig_lessons
            from learning_engine.mastery import save_mastery_data
            save_mastery_data(data)
