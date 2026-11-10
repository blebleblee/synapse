"""
Tests for learning_engine.mastery
Verifies competence state transitions and atomic file persistence.
"""

import pytest
from learning_engine.mastery import (
    load_mastery_data,
    set_subtopic_mastery,
    get_subtopic_mastery,
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
