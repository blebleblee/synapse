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
