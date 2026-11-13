"""
Unit and Functional Tests for AI Mentor Connectivity and Chat Endpoints
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.backend.main import app, build_chat_system_instruction

client = TestClient(app)

def test_build_chat_system_instruction_with_active_lesson():
    instruction = build_chat_system_instruction(
        domain="computing",
        category="infrastructure",
        subtopic="kubernetes",
        active_lesson="lesson_02_architecture_and_control_plane",
        active_lesson_title="Lesson 2: Architecture & Control Plane",
        terminal_context="error: connection refused to 127.0.0.1:6443"
    )
    assert "Socratic Mentor" in instruction
    assert "Kubernetes" in instruction
    assert "Lesson 2: Architecture & Control Plane" in instruction
    assert "Live Student Terminal Output" in instruction
    assert "connection refused" in instruction

def test_build_chat_system_instruction_with_language_mandate():
    """Verify non-English language parameter injects proper language directive."""
    instruction = build_chat_system_instruction(
        domain="computing",
        category="systems",
        subtopic="linux_kernel",
        language="cs"
    )
    assert "MANDATORY LANGUAGE DIRECTIVE" in instruction
    assert "Czech" in instruction
    assert "Čeština" in instruction

def test_api_check_mentor_connectivity():
    """Functional check for /api/check-mentor-connectivity endpoint."""
    res = client.post("/api/check-mentor-connectivity", json={"host": "http://127.0.0.1:11434"})
    assert res.status_code == 200
    data = res.json()
    assert "connected" in data
    assert isinstance(data["connected"], bool)

def test_api_chat_with_dictionary_history_and_lesson_content():
    """
    Direct regression test for the 500 AttributeError on history dicts.
    Verifies that dictionary objects in history (sent from frontend) do not cause
    'dict object has no attribute role' crashes.
    """
    mock_provider = MagicMock()
    mock_provider.generate_stream.return_value = ["eBPF ", "is ", "safe."]
    mock_provider.generate.return_value = "eBPF is safe."

    with patch("app.backend.main.get_chat_provider", return_value=(mock_provider, "mock-model")):
        payload = {
            "query": "computing/systems/bash",
            "lesson_id": "lesson_01_foundations_and_invariants",
            "lesson_title": "Lesson 1: Foundations & Shell Invariants",
            "lesson_content": "Bash process model, fork and exec invariants, file descriptor cloning.",
            "message": "What is process forking?",
            "history": [
                {"role": "student", "content": "hello"},
                {"role": "tutor", "content": "hi there"}
            ],
            "stream": True
        }
        res = client.post("/api/chat", json=payload)
        assert res.status_code == 200
        text = res.text
        assert "data:" in text
        assert "eBPF is safe." in text

def test_api_chat_non_streaming():
    """Tests non-streaming chat mode."""
    mock_provider = MagicMock()
    mock_provider.generate.return_value = "Process forking clones the calling process."

    with patch("app.backend.main.get_chat_provider", return_value=(mock_provider, "mock-model")):
        payload = {
            "message": "Explain forking",
            "history": [],
            "stream": False
        }
        res = client.post("/api/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "reply" in data
        assert "Process forking" in data["reply"]
