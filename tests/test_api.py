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

def test_api_flashcards_deck():
    test_path = "computing/infrastructure/kubernetes"
    res = client.get(f"/api/flashcards/deck?query={test_path}")
    assert res.status_code == 200
    data = res.json()
    assert "cards" in data
    assert isinstance(data["cards"], list)

def test_api_translate_en_passthrough():
    res = client.post("/api/translate", json={"text": "# Hello World", "target_lang": "en"})
    assert res.status_code == 200
    data = res.json()
    assert data["translated"] == "# Hello World"

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




