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

def test_chat_with_disk_lesson_content_fallback():
    """
    When the client does not send lesson_content in payload, chat_with_tutor
    must read the lesson markdown from disk and inject it into the prompt.
    """
    captured = {}
    class InspectingProvider:
        def generate_stream(self, prompt, **kwargs):
            captured["prompt"] = prompt
            captured["system_instruction"] = kwargs.get("system_instruction", "")
            yield "Understood from disk."

    with patch("app.backend.main.get_chat_provider", return_value=(InspectingProvider(), "mock-model")):
        payload = {
            "query": "computing/data/postgresql",
            "lesson_id": "lesson_01_foundations_and_invariants",
            "message": "Explain this lesson from disk",
            "stream": True
        }
        res = client.post("/api/chat", json=payload)
        assert res.status_code == 200
        assert "Active Lesson in Reader Window" in captured.get("prompt", "")
        assert "Postgresql" in captured.get("system_instruction", "")

def test_chat_neutral_workspace_instruction_when_no_topic():
    """
    When no topic query is provided, mentor uses neutral workspace instruction.
    """
    captured = {}
    class InspectingProvider:
        def generate(self, prompt, **kwargs):
            captured["system_instruction"] = kwargs.get("system_instruction", "")
            return "General guidance."

    with patch("app.backend.main.get_chat_provider", return_value=(InspectingProvider(), "mock-model")):
        payload = {
            "query": "",
            "message": "What should I study?",
            "stream": False
        }
        res = client.post("/api/chat", json=payload)
        assert res.status_code == 200
        assert "Synapse Polymath Workspace" in captured.get("system_instruction", "")

def test_chat_streaming_provider_failure_returns_sse_error():
    """
    When the provider fails mid-stream, the stream yields an SSE error frame
    rather than crashing or returning an unhandled 500 error.
    """
    class CrashingStreamProvider:
        def generate_stream(self, prompt, **kwargs):
            yield "Initial tokens..."
            raise RuntimeError("Mid-stream connection to LLM host dropped")

    with patch("app.backend.main.get_chat_provider", return_value=(CrashingStreamProvider(), "mock-crasher")):
        payload = {
            "query": "computing/data/postgresql",
            "message": "Cause mid-stream crash",
            "stream": True
        }
        res = client.post("/api/chat", json=payload)
        assert res.status_code == 200
        text = res.text
        assert "Initial tokens" in text
        assert "Socratic Mentor stream error" in text
        assert "Mid-stream connection to LLM host dropped" in text

def test_save_chat_session_real_disk_persistence(tmp_path):
    """
    Verifies that save_chat_session creates active_session.md and chat_history.json
    with proper timestamping and serialized message history.
    """
    from app.backend.main import save_chat_session
    import json

    sub_dir = tmp_path / "course_dir"
    sub_dir.mkdir(parents=True, exist_ok=True)

    save_chat_session(sub_dir, "What is WAL?", "Write-ahead logging guarantees durability.", [])

    session_file = sub_dir / "sessions" / "active_session.md"
    history_file = sub_dir / "sessions" / "chat_history.json"

    assert session_file.exists()
    assert history_file.exists()

    md_text = session_file.read_text(encoding="utf-8")
    assert "What is WAL?" in md_text
    assert "Write-ahead logging guarantees durability." in md_text

    history_data = json.loads(history_file.read_text(encoding="utf-8"))
    assert len(history_data) == 2
    assert history_data[0]["role"] == "student"
    assert history_data[1]["role"] == "tutor"

