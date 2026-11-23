import json
"""
Tests for app.backend.main FastAPI Endpoints
Verifies REST API contracts, path sanitization, and error responses.
"""

import pytest
from fastapi.testclient import TestClient
from app.backend.main import app

client = TestClient(app)

def test_api_status():
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert "domains" in data
    assert data["domains"] >= 11

def test_api_tree():
    res = client.get("/api/tree")
    assert res.status_code == 200
    data = res.json()
    assert "computing" in data
    assert "engineering" in data

def test_api_tree_does_not_reveal_server_paths():
    """/api/tree sent every course's absolute path (the server's home folder) to
    the browser, which never used it. With a password and remote access that
    leaks the server layout."""
    from learning_engine.topic_manager import WORKSPACE_ROOT
    text = client.get("/api/tree").text
    assert "full_path" not in text
    assert str(WORKSPACE_ROOT) not in text


def test_api_graph():
    res = client.get("/api/graph")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "edges" in data
    assert data["node_count"] >= 500

def test_api_topic_dependencies():
    res = client.get("/api/topic/dependencies?query=computing/ai/large_language_models")
    assert res.status_code == 200
    data = res.json()
    assert "prerequisites" in data
    assert "unlocks" in data

def test_api_topic_valid():
    res = client.get("/api/topic?query=computing/infrastructure/kubernetes")
    assert res.status_code == 200
    data = res.json()
    assert "domain" in data
    assert data["domain"] == "computing"
    assert "lesson" in data
    assert "available_levels" not in data

def test_api_quiz_validation():
    # Verify 404 on invalid topic
    res = client.post("/api/quiz", json={"query": "non_existent_topic_xyz"})
    assert res.status_code == 404

def test_api_quiz_forwards_model_and_host(monkeypatch):
    """
    FIND-08: /api/quiz must forward the configured model and cluster host
    to its generation provider. (/api/summary/regenerate was removed.)
    """
    captured_quiz = {}
    class MockQuizProvider:
        def generate(self, prompt, **kwargs):
            return '[{"id": 1, "question": "Q?", "options": ["A", "B"], "correctIndex": 0, "explanation": "E"}]'

    def mock_get_provider(**kwargs):
        captured_quiz.update(kwargs)
        return MockQuizProvider()

    monkeypatch.setattr("app.backend.main.get_provider", mock_get_provider)

    quiz_res = client.post("/api/quiz", json={
        "query": "computing/data/postgresql",
        "model": "qwen2.5-coder:32b",
        "host": "http://192.168.1.50:11434"
    })
    assert quiz_res.status_code == 200
    assert captured_quiz.get("model") == "qwen2.5-coder:32b"
    assert captured_quiz.get("host") == "http://192.168.1.50:11434"

def test_api_generate(monkeypatch):
    # Mock get_provider to bypass Ollama cluster checks
    class MockProvider:
        def generate(self, prompt, **kwargs):
            return "Mocked generated curriculum content"
            
    monkeypatch.setattr("app.backend.main.get_provider", lambda **kwargs: MockProvider())
    
    # Mock generation function to prevent real LLM calls
    monkeypatch.setattr("app.backend.main.generate_subtopic_content", lambda **kwargs: "Mocked generated curriculum content")

    
    # Test valid query
    res = client.post("/api/generate", json={
        "query": "computing/data/postgresql",
        "force": False,
        "provider": "ollama",
        "model": "dummy-model"
    })
    
    assert res.status_code == 200
    data = res.json()
    assert data["domain"] == "computing"
    assert data["category"] == "data"
    assert data["subtopic"] == "postgresql"
    assert data["results"] == "Mocked generated curriculum content"

    # Test invalid query (404 Not Found)
    res_404 = client.post("/api/generate", json={"query": "non_existent/fake/topic"})
    assert res_404.status_code == 404

def test_api_topic_not_found():
    res = client.get("/api/topic?query=fake_non_existent_topic_123")
    assert res.status_code == 404

def test_api_search():
    res = client.get("/api/search?q=kernel")
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert len(data["results"]) > 0

def test_api_mastery_get_and_post():
    test_path = "computing/infrastructure/kubernetes"
    get_res = client.get("/api/mastery")
    assert get_res.status_code == 200

    # Test update
    post_res = client.post("/api/mastery", json={"path": test_path, "state": "studying"})
    assert post_res.status_code == 200
    assert post_res.json()["state"] == "studying"

def test_api_flashcards_deck(monkeypatch):
    """A topic without a deck gets one generated on first open."""
    import app.backend.main as backend
    test_path = "computing/infrastructure/kubernetes"
    target = backend.resolve_subtopic(test_path)
    assert target, "fixture topic missing"
    csv_file = target[3] / "flashcards.csv"
    if csv_file.exists():
        csv_file.unlink()

    def fake_generate(query, **kwargs):
        csv_file.write_text("What schedules pods?,The kube-scheduler,core\n", encoding="utf-8")
        return csv_file

    monkeypatch.setattr(backend, "generate_flashcards", fake_generate)
    res = client.get(f"/api/flashcards/deck?query={test_path}")
    assert res.status_code == 200
    cards = res.json()["cards"]
    assert cards == [{"id": 0, "front": "What schedules pods?", "back": "The kube-scheduler", "tag": "core"}]


def test_api_flashcards_deck_generation_failure_is_reported(monkeypatch):
    """When the AI cannot make a deck, say so (503) instead of returning an
    empty deck that the UI blames on the lesson content."""
    import app.backend.main as backend
    test_path = "computing/infrastructure/kubernetes"
    target = backend.resolve_subtopic(test_path)
    csv_file = target[3] / "flashcards.csv"
    if csv_file.exists():
        csv_file.unlink()

    def failing_generate(query, **kwargs):
        raise ConnectionError("no AI provider reachable")

    monkeypatch.setattr(backend, "generate_flashcards", failing_generate)
    res = client.get(f"/api/flashcards/deck?query={test_path}")
    assert res.status_code == 503
    assert "no AI provider reachable" in res.json()["detail"]

def test_api_translate_en_passthrough():
    res = client.post("/api/translate", json={"text": "# Hello World", "target_lang": "en"})
    assert res.status_code == 200
    data = res.json()
    assert data["translated"] == "# Hello World"

def test_api_translate_failure_does_not_cache_english_fallback(monkeypatch):
    """
    FIND-04: When an AI provider fails or is blocked during translation,
    the endpoint returns the English fallback but MUST NOT cache it to disk.
    A subsequent request must still attempt translation (cached=False).
    """
    from unittest.mock import MagicMock
    import app.backend.main as be_main
    failing = MagicMock(spec=["generate"])
    failing.generate.side_effect = RuntimeError("provider rejected the request")
    monkeypatch.setattr(be_main, "get_translation_provider", lambda **kwargs: (failing, "mock-translator"))

    raw_text = "# Microservices Architecture\nService mesh proxies intercept traffic."
    res1 = client.post("/api/translate", json={"text": raw_text, "target_lang": "cs"})
    assert res1.status_code == 200
    data1 = res1.json()
    assert failing.generate.called
    assert data1["cached"] is False
    assert data1["fallback"] is True
    assert data1["translated"] == raw_text

    res2 = client.post("/api/translate", json={"text": raw_text, "target_lang": "cs"})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["cached"] is False, "Failed translation was incorrectly cached to disk!"
    assert data2["fallback"] is True

def test_api_translate_without_provider_returns_503():
    """No reachable or configured AI provider: a clear 503, not a server error."""
    res = client.post("/api/translate", json={"text": "# Title\nBody.", "target_lang": "cs"})
    assert res.status_code == 503
    assert "active LLM provider" in res.json()["detail"]

def test_api_translate_successful_translation_caches_result(monkeypatch):
    """
    FIND-04: When translation succeeds, the translated text is cached to disk.
    Subsequent requests return cached=True.
    """
    from unittest.mock import MagicMock
    mock_provider = MagicMock()
    mock_provider.generate.return_value = "# Architektura mikroslužeb\nProxy proxy sítě zachycují provoz."

    import app.backend.main as be_main
    monkeypatch.setattr(be_main, "get_translation_provider", lambda **kwargs: (mock_provider, "mock-translator"))

    raw_text = "# Microservices Architecture\nProxies intercept network traffic."
    res1 = client.post("/api/translate", json={"text": raw_text, "target_lang": "cs"})
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["cached"] is False
    assert data1["fallback"] is False
    assert "mikroslužeb" in data1["translated"]

    # Second request should be served from disk cache
    res2 = client.post("/api/translate", json={"text": raw_text, "target_lang": "cs"})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["cached"] is True
    assert "mikroslužeb" in data2["translated"]

def test_api_translate_stream_reports_progress(monkeypatch):
    """With stream=true the endpoint reports per-section progress, then the result."""
    from unittest.mock import MagicMock
    mock_provider = MagicMock()
    mock_provider.generate.side_effect = lambda prompt: "# Přeložená sekce s dostatečnou délkou textu"

    import app.backend.main as be_main
    monkeypatch.setattr(be_main, "get_translation_provider", lambda **kwargs: (mock_provider, "mock-translator"))

    raw_text = "# One\nFirst section text.\n## Two\nSecond section text.\n## Three\nThird section text."
    res = client.post("/api/translate", json={"text": raw_text, "target_lang": "cs", "stream": True})
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("application/x-ndjson")
    events = [json.loads(line) for line in res.text.splitlines() if line.strip()]

    assert events[0] == {"progress": 0, "total": 3, "model": "mock-translator"}
    assert [e["progress"] for e in events[1:-1]] == [1, 2, 3]
    final = events[-1]
    assert final["cached"] is False
    assert final["fallback"] is False
    assert "Přeložená" in final["translated"]


def test_api_translate_stream_cached_result_is_single_event(monkeypatch):
    from unittest.mock import MagicMock
    mock_provider = MagicMock()
    mock_provider.generate.return_value = "# Nadpis a dostatečně dlouhý přeložený text"
    import app.backend.main as be_main
    monkeypatch.setattr(be_main, "get_translation_provider", lambda **kwargs: (mock_provider, "m"))

    body = {"text": "# Heading\nSome text to translate.", "target_lang": "de"}
    assert client.post("/api/translate", json=body).status_code == 200
    res = client.post("/api/translate", json={**body, "stream": True})
    events = [json.loads(line) for line in res.text.splitlines() if line.strip()]
    assert len(events) == 1 and events[0]["cached"] is True


def test_path_traversal_prevention():
    res = client.get("/api/topic?query=../../etc/passwd")
    assert res.status_code in [400, 404]

def test_api_multi_lesson_discovery_and_selection():
    # Test multi-lesson discovery on PostgreSQL
    res = client.get("/api/topic?query=postgresql")
    assert res.status_code == 200
    data = res.json()
    assert "lessons" in data
    assert len(data["lessons"]) >= 6
    assert data["active_lesson_id"] == "lesson_01_foundations_and_invariants"
    assert "Lesson 1: Foundations" in data["lessons"][0]["title"]
    assert data["course_title"] is None
    assert data["discipline_title"] == "Data"
    assert data["domain_title"] == "Computing"
    assert data["display_title"] == "PostgreSQL Internals"
    assert "full_content" in data
    assert len(data["full_content"]) > 1000

    # Test selecting specific lesson
    res_l3 = client.get("/api/topic?query=postgresql&lesson_id=lesson_03_mvcc_wal_and_vacuum")
    assert res_l3.status_code == 200
    data_l3 = res_l3.json()
    assert data_l3["active_lesson_id"] == "lesson_03_mvcc_wal_and_vacuum"
    assert "MVCC" in data_l3["lesson"] or "Multiversion" in data_l3["lesson"] or "Multi-Version" in data_l3["lesson"]

def test_api_four_segment_path_and_lesson_resolution():
    # Test 4-segment pathway link from Skills Graph
    res = client.get("/api/topic?query=computing/ai/deep_learning/04_transformer_attention_mechanisms")
    assert res.status_code == 200
    data = res.json()
    assert data["domain"] == "computing"
    assert data["category"] == "ai"
    assert data["subtopic"] == "deep_learning"
    assert data["active_lesson_id"] == "lesson_04_optimization_techniques"

def test_api_cluster_status():
    res = client.get("/api/settings/cluster-status")
    assert res.status_code == 200
    data = res.json()
    local_key = "http://127.0.0.1:11434" if "http://127.0.0.1:11434" in data else "http://localhost:11434"
    assert local_key in data
    assert isinstance(data[local_key]["online"], bool)

def test_api_get_and_set_cluster_hosts():
    # 1. Get initial hosts
    res_get = client.get("/api/settings/cluster")
    assert res_get.status_code == 200
    initial_hosts = res_get.json()["hosts"]
    assert len(initial_hosts) >= 1

    # 2. Update with custom node
    test_hosts = ["http://localhost:11434", "http://custom-node.local:11434"]
    res_post = client.post("/api/settings/cluster", json={"hosts": test_hosts})
    assert res_post.status_code == 200
    assert res_post.json()["saved"] is True
    assert res_post.json()["hosts"] == test_hosts

    # 3. Verify persistence on GET
    res_verify = client.get("/api/settings/cluster")
    assert res_verify.json()["hosts"] == test_hosts

    # 4. Clean up / restore original hosts
    client.post("/api/settings/cluster", json={"hosts": initial_hosts})
    from learning_engine.models import CLUSTER_CONFIG_PATH
    if CLUSTER_CONFIG_PATH.exists():
        CLUSTER_CONFIG_PATH.unlink()

def test_api_packages_endpoints():
    # 1. List packages
    res = client.get("/api/packages")
    assert res.status_code == 200
    data = res.json()
    assert "installed" in data
    assert "available_domains" in data
    assert len(data["available_domains"]) == 12

    # Verify domain enrichment fields
    first_domain = data["available_domains"][0]
    assert "lesson_count" in first_domain
    assert "lab_count" in first_domain
    assert "is_installed" in first_domain

    # 2. Export package
    res_exp = client.post("/api/packages/export?domain=arts")
    assert res_exp.status_code == 200
    assert len(res_exp.content) > 0

    # 3. Install by domain parameter
    res_inst = client.post("/api/packages/install?domain=arts")
    assert res_inst.status_code == 200
    assert res_inst.json()["status"] == "installed"
    assert res_inst.json()["domain"] == "arts"

    # 4. Verify listed in installed
    res_list = client.get("/api/packages")
    assert any(p.get("domain") == "arts" for p in res_list.json()["installed"])

    try:
        # 5. Uninstall domain package
        res_del = client.delete("/api/packages/arts")
        assert res_del.status_code == 200
        assert res_del.json()["status"] == "uninstalled"
    finally:
        # Restore arts domain for subsequent test isolation
        client.post("/api/packages/install?domain=arts")

def test_dangerous_command_detection():
    from learning_engine.security import is_dangerous_host_command

    # Destructive commands that MUST be blocked
    assert is_dangerous_host_command("rm -rf /")
    assert is_dangerous_host_command("rm -rf ~")
    assert is_dangerous_host_command("rm -rf *")
    assert is_dangerous_host_command("rm -rf /Users/test/workspace")
    assert is_dangerous_host_command("sudo rm -rf /etc")
    assert is_dangerous_host_command("mkfs.ext4 /dev/disk1s1")
    assert is_dangerous_host_command("dd if=/dev/zero of=/dev/rdisk2")
    assert is_dangerous_host_command("> /dev/disk2")
    assert is_dangerous_host_command(":(){ :|:& };:")
    assert is_dangerous_host_command("shutdown -h now")
    assert is_dangerous_host_command("sudo reboot")
    assert is_dangerous_host_command("chmod -R 777 /")
    assert is_dangerous_host_command("git reset --hard")
    assert is_dangerous_host_command("git clean -fd")

    # Safe commands that MUST be allowed
    assert not is_dangerous_host_command("ls -la")
    assert not is_dangerous_host_command("git status")
    assert not is_dangerous_host_command("git diff HEAD")
    assert not is_dangerous_host_command("pytest tests/")
    assert not is_dangerous_host_command("python main.py")
    assert not is_dangerous_host_command("cat file.txt")
    assert not is_dangerous_host_command("echo 'hello world'")

def test_api_lesson_completion_prefixed_and_canonical_sync():
    """
    API-level regression test exercising the completion endpoint, warm-cache invalidation,
    and subsequent topic/tree reads using the actual request formats:
    1. GET /api/tree BEFORE initial completion to warm the cache and assert initial incomplete state.
    2. POST /api/mastery/lesson with path='topics/computing/data/postgresql' (as sent by LessonViewer) to toggle ON.
    3. Assert updated tree state (cache was invalidated) and topic-detail state.
    4. POST /api/mastery/lesson with completed=false to toggle OFF.
    5. Assert updated tree state (cache was invalidated again) and topic-detail state.
    """
    prefixed_path = "topics/computing/data/postgresql"
    canonical_query = "computing/data/postgresql"
    test_lesson = "lesson_01_foundations_and_invariants"

    # 1. Warm cache: GET /api/tree BEFORE initial completion and assert initial incomplete state
    tree_warm = client.get("/api/tree")
    assert tree_warm.status_code == 200
    pg_unit_warm = tree_warm.json()["computing"]["disciplines"]["data"]["courses"]["postgresql"]["units"]["core"]
    assert test_lesson not in pg_unit_warm.get("completed_lessons", []), (
        f"Expected {test_lesson} to not be completed initially in /api/tree"
    )

    # 2. Mark lesson completed (toggle ON) using prefixed path from LessonViewer
    post_res = client.post("/api/mastery/lesson", json={
        "path": prefixed_path,
        "lesson_id": test_lesson,
        "completed": True
    })
    assert post_res.status_code == 200
    assert test_lesson in post_res.json()["completed_lessons"]

    # 3. Assert updated tree state and topic-detail state (warm cache was invalidated!)
    tree_res = client.get("/api/tree")
    assert tree_res.status_code == 200
    pg_unit = tree_res.json()["computing"]["disciplines"]["data"]["courses"]["postgresql"]["units"]["core"]
    assert test_lesson in pg_unit["completed_lessons"], (
        f"Expected {test_lesson} in /api/tree unit completed_lessons after cache invalidation"
    )

    topic_res = client.get(f"/api/topic?query={canonical_query}")
    assert topic_res.status_code == 200
    topic_data = topic_res.json()
    assert test_lesson in topic_data["completed_lessons"], (
        f"Expected {test_lesson} in /api/topic completed_lessons, got: {topic_data.get('completed_lessons')}"
    )

    # 4. Toggle completion OFF via API
    off_res = client.post("/api/mastery/lesson", json={
        "path": canonical_query,
        "lesson_id": test_lesson,
        "completed": False
    })
    assert off_res.status_code == 200
    assert test_lesson not in off_res.json()["completed_lessons"]

    # 5. Assert updated tree state and topic-detail state again (cache invalidated on toggle OFF!)
    tree_res2 = client.get("/api/tree")
    assert tree_res2.status_code == 200
    pg_unit2 = tree_res2.json()["computing"]["disciplines"]["data"]["courses"]["postgresql"]["units"]["core"]
    assert test_lesson not in pg_unit2["completed_lessons"], (
        f"Expected {test_lesson} to not be in /api/tree completed_lessons after toggle OFF"
    )

    topic_res2 = client.get(f"/api/topic?query={canonical_query}")
    assert topic_res2.status_code == 200
    assert test_lesson not in topic_res2.json()["completed_lessons"]

def test_api_mastery_independent_of_sql_row_order():
    """
    Verifies that /api/mastery returns the exact same resolved state and merged lessons
    independent of SQL row order when canonical and legacy rows coexist.
    """
    from learning_engine.database import get_connection
    import json

    canonical_path = "computing/data/postgresql"
    legacy_path = f"topics/{canonical_path}"

    # Scenario A: Canonical row inserted first, Legacy row inserted second
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

    res_a = client.get("/api/mastery")
    assert res_a.status_code == 200
    data_a = res_a.json()["topics"][canonical_path]
    assert data_a["state"] == "mastered"
    assert data_a["completed_lessons"] == ["lesson_01", "lesson_02", "lesson_03"]

    # Scenario B: Legacy row inserted first, Canonical row inserted second
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM mastery WHERE path = ? OR path = ?", (canonical_path, legacy_path))
        conn.execute(
            "INSERT INTO mastery (path, state, completed_lessons) VALUES (?, ?, ?)",
            (legacy_path, "studying", json.dumps(["lesson_02", "lesson_03"]))
        )
        conn.execute(
            "INSERT INTO mastery (path, state, completed_lessons) VALUES (?, ?, ?)",
            (canonical_path, "mastered", json.dumps(["lesson_01", "lesson_03"]))
        )
    conn.close()

    res_b = client.get("/api/mastery")
    assert res_b.status_code == 200
    data_b = res_b.json()["topics"][canonical_path]
    assert data_b["state"] == "mastered"
    assert data_b["completed_lessons"] == ["lesson_01", "lesson_02", "lesson_03"]

    # Clean up
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM mastery WHERE path = ? OR path = ?", (canonical_path, legacy_path))
    conn.close()






def test_find_sandbox_tool_searches_rancher_desktop_bin(tmp_path, monkeypatch):
    """Rancher Desktop installs docker/kubectl in ~/.rd/bin, which a Dock-launched app's PATH lacks."""
    import app.backend.main as be_main
    rd_bin = tmp_path / ".rd" / "bin"
    rd_bin.mkdir(parents=True)
    tool = rd_bin / "docker"
    tool.write_text("#!/bin/sh\nexit 0\n")
    tool.chmod(0o755)
    monkeypatch.setattr(be_main.Path, "home", classmethod(lambda cls: tmp_path))
    # Only an empty directory on PATH: a docker installed on the host (CI
    # runners have /usr/bin/docker) must not be found before ~/.rd/bin.
    empty = tmp_path / "empty-path"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))

    assert be_main.find_sandbox_tool("docker") == str(tool)

    import subprocess
    seen = {}
    def fake_run(cmd, **kwargs):
        seen["cmd"], seen["path"] = cmd, kwargs["env"]["PATH"]
        return subprocess.CompletedProcess(cmd, 0)
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert be_main.sandbox_tool_responds([str(tool), "info"]) is True
    assert seen["cmd"] == [str(tool), "info"]
    assert str(rd_bin) in seen["path"].split(":")


def test_api_system_shutdown_localhost_only(monkeypatch):
    """Verifies that /api/system/shutdown is accepted from localhost and rejected for remote hosts."""
    import app.backend.main as backend
    scheduled = []
    monkeypatch.setattr(backend, "_schedule_shutdown", lambda: scheduled.append(1))

    local_client = TestClient(app, client=("127.0.0.1", 50000))
    res = local_client.post("/api/system/shutdown")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "shutting_down"
    assert scheduled == [1]

    # Non-localhost remote client (e.g. from LAN)
    remote_client = TestClient(app, client=("192.168.1.100", 50000))
    res_remote = remote_client.post("/api/system/shutdown")
    assert res_remote.status_code == 403
    assert "restricted to localhost" in res_remote.json()["detail"]
    assert scheduled == [1]


def test_api_flashcards_queue_and_review():
    """Verifies that GET /api/flashcards/queue and POST /api/flashcards/review respond correctly."""
    res_queue = client.get("/api/flashcards/queue")
    assert res_queue.status_code == 200
    assert "queue" in res_queue.json()
    assert isinstance(res_queue.json()["queue"], list)

    res_review = client.post("/api/flashcards/review", json={"path": "computing/systems/bash", "interval_days": 3})
    assert res_review.status_code == 200
    data = res_review.json()
    assert data["path"] == "computing/systems/bash"
    assert data["interval_days"] == 3


@pytest.mark.parametrize("reply", [
    "Error: could not connect to http://127.0.0.1:9",
    "Sure! Here are some questions about Bash.",
    '[{"question": "Q?", "options": ["A", "B"], "correctIndex": 5}]',
])
def test_quiz_without_usable_questions_is_an_error_not_a_canned_quiz(monkeypatch, reply):
    """With no model reachable the quiz showed a hard-coded generic question
    ("what is the primary architectural trade-off?") as if it were real."""
    class Fake:
        def generate(self, prompt, **kwargs):
            return reply
    monkeypatch.setattr("app.backend.main.get_provider", lambda **k: Fake())
    res = client.post("/api/quiz", json={"query": "computing/data/postgresql"})
    assert res.status_code == 502
    assert "quiz" in res.json()["detail"]


def test_quiz_failing_model_is_an_error(monkeypatch):
    class Down:
        def generate(self, prompt, **kwargs):
            raise ConnectionError("connection refused")
    monkeypatch.setattr("app.backend.main.get_provider", lambda **k: Down())
    res = client.post("/api/quiz", json={"query": "computing/data/postgresql"})
    assert res.status_code == 502
    assert "connection refused" in res.json()["detail"]


def test_quiz_keeps_valid_questions_from_a_chatty_reply(monkeypatch):
    class Fake:
        def generate(self, prompt, **kwargs):
            return ('Here you go:\n```json\n[{"question": "Q1?", "options": ["A", "B", "C"], "correctIndex": 2, "explanation": "E"},'
                    ' {"question": "", "options": ["A"], "correctIndex": 0}]\n```')
    monkeypatch.setattr("app.backend.main.get_provider", lambda **k: Fake())
    res = client.post("/api/quiz", json={"query": "computing/data/postgresql"})
    assert res.status_code == 200
    qs = res.json()["questions"]
    assert [q["question"] for q in qs] == ["Q1?"]
    assert qs[0]["correctIndex"] == 2


def test_quiz_keeps_the_questions_a_broken_one_would_have_taken_down():
    """qwen2.5-coder put unescaped quotes in one question (a shell command), so
    the whole array failed to parse and the learner got no quiz at all."""
    from app.backend.main import parse_quiz_questions
    raw = """[
  {"id": 1, "question": "Which file does a login shell read first?", "options": ["/etc/profile", "~/.bashrc"], "correctIndex": 0, "explanation": "E1"},
  {"id": 2, "question": "Scenario: `var=$(echo "Hello World" | tr ' ' '_')`. Value?", "options": ["Hello_World", "x"], "correctIndex": 0, "explanation": "E2"},
  {"id": 3, "question": "What does `bash -c 'echo $0'` print?", "options": ["bash", "-c"], "correctIndex": 0, "explanation": "E3 uses ${HOME}"}
]"""
    qs = parse_quiz_questions(raw)
    assert [q["explanation"] for q in qs] == ["E1", "E3 uses ${HOME}"]
    assert [q["id"] for q in qs] == [1, 2]
