"""
Unit and Functional Tests for Curriculum Search and Search API
"""

import pytest
from learning_engine.search import search_curriculum
from learning_engine.flashcards import generate_flashcards
from fastapi.testclient import TestClient
from app.backend.main import app

client = TestClient(app)

def test_search_curriculum_matches():
    results = search_curriculum("kernel")
    assert isinstance(results, list)
    assert len(results) > 0

    first = results[0]
    assert "domain" in first
    assert "category" in first
    assert "subtopic" in first
    assert "level" in first
    assert isinstance(first["level"], str)
    assert "score" in first
    assert "snippet" in first
    assert "section" in first

def test_search_curriculum_two_character_queries():
    """
    Direct regression test for two-character search queries (e.g. 'os', 'db', 'ai', 'io').
    Ensures queries of length >= 2 execute cleanly without errors or crashes.
    """
    for query in ["os", "db", "ai", "io"]:
        results = search_curriculum(query)
        assert isinstance(results, list)
        for r in results:
            assert "domain" in r
            assert "category" in r
            assert "subtopic" in r
            assert "level" in r
            assert isinstance(r["level"], str)
            # Ensure level can be safely uppercased as required by frontend tags
            assert r["level"].upper() == "MASTERCLASS"

def test_search_curriculum_single_character():
    """Queries under 2 characters should return empty list without searching."""
    assert search_curriculum("a") == []
    assert search_curriculum(" ") == []
    assert search_curriculum("") == []

def test_search_curriculum_no_match():
    results = search_curriculum("xyzqwertyuiop123456789nonexistent")
    assert results == []

def test_api_search_endpoint_functional():
    """Functional test for /api/search with two-character query."""
    res = client.get("/api/search?q=os")
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) > 0

    first = data["results"][0]
    assert first.get("level") == "masterclass"
    assert "domain" in first
    assert "subtopic" in first
    assert "snippet" in first

def test_api_search_endpoint_validation():
    """Functional test verifying single-character query triggers 422 validation error."""
    res = client.get("/api/search?q=a")
    assert res.status_code == 422

from unittest.mock import MagicMock

def test_generate_flashcards_csv(monkeypatch):
    mock_provider = MagicMock()
    mock_provider.generate.return_value = '{"flashcards": [{"front": "What is etcd?", "back": "Distributed linearizable key-value store using Raft."}]}'
    monkeypatch.setattr("learning_engine.flashcards.get_provider", lambda **kwargs: mock_provider)

    csv_path = generate_flashcards("computing/infrastructure/kubernetes")
    assert csv_path.exists()
    content = csv_path.read_text(encoding="utf-8")
    assert "#separator:Comma" in content
    assert "What is etcd?" in content
