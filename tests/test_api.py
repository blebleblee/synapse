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
    assert data["node_count"] >= 700

def test_api_topic_dependencies():
    res = client.get("/api/topic/dependencies?query=computing/ai/large_language_models/02_instruction_tuning_and_rlhf")
    assert res.status_code == 200
    data = res.json()
    assert "prerequisites" in data
    assert "unlocks" in data

def test_api_topic_valid():
    res = client.get("/api/topic?query=computing/infrastructure/kubernetes/01_control_plane_and_etcd&level=beginner")
    assert res.status_code == 200
    data = res.json()
    assert "domain" in data
    assert data["domain"] == "computing"
    assert "lesson" in data

def test_api_topic_not_found():
    res = client.get("/api/topic?query=fake_non_existent_topic_123&level=beginner")
    assert res.status_code == 404

def test_api_search():
    res = client.get("/api/search?q=kernel")
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert len(data["results"]) > 0

def test_api_mastery_get_and_post():
    test_path = "computing/infrastructure/kubernetes/01_control_plane_and_etcd"
    get_res = client.get("/api/mastery")
    assert get_res.status_code == 200

    # Test update
    post_res = client.post("/api/mastery", json={"path": test_path, "state": "studying"})
    assert post_res.status_code == 200
    assert post_res.json()["state"] == "studying"

def test_api_flashcards_deck():
    test_path = "computing/infrastructure/kubernetes/01_control_plane_and_etcd"
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
    res = client.get("/api/topic?query=../../etc/passwd&level=beginner")
    assert res.status_code in [400, 404]

def test_api_multi_lesson_discovery_and_selection():
    # Test multi-lesson discovery on PostgreSQL
    res = client.get("/api/topic?query=postgresql")
    assert res.status_code == 200
    data = res.json()
    assert "lessons" in data
    assert len(data["lessons"]) == 4
    assert data["active_lesson_id"] == "lesson_01_architecture_and_process_model"
    assert "Lesson 1: Architecture" in data["lessons"][0]["title"]

    # Test selecting specific lesson
    res_l2 = client.get("/api/topic?query=postgresql&lesson_id=lesson_02_mvcc_wal_and_vacuum")
    assert res_l2.status_code == 200
    data_l2 = res_l2.json()
    assert data_l2["active_lesson_id"] == "lesson_02_mvcc_wal_and_vacuum"
    assert "Multiversion Concurrency Control" in data_l2["lesson"]

def test_api_cluster_status():
    res = client.get("/api/settings/cluster-status")
    assert res.status_code == 200
    data = res.json()
    assert "http://localhost:11434" in data
    assert "http://studio.2464.cz:11434" in data
    assert "http://maxi.2464.cz:11434" in data
    assert "http://192.168.200.60:8080" in data
    assert isinstance(data["http://localhost:11434"]["online"], bool)

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
