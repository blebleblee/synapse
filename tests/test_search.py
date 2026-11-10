"""
Tests for learning_engine.search and learning_engine.flashcards
"""

import pytest
from learning_engine.search import search_curriculum
from learning_engine.flashcards import generate_flashcards

def test_search_curriculum_matches():
    results = search_curriculum("kernel")
    assert isinstance(results, list)
    assert len(results) > 0

    first = results[0]
    assert "domain" in first
    assert "category" in first
    assert "subtopic" in first
    assert "score" in first

def test_search_curriculum_no_match():
    results = search_curriculum("xyzqwertyuiop123456789nonexistent")
    assert results == []

from unittest.mock import MagicMock

def test_generate_flashcards_csv(monkeypatch):
    mock_provider = MagicMock()
    mock_provider.generate.return_value = '{"flashcards": [{"front": "What is etcd?", "back": "Distributed linearizable key-value store using Raft."}]}'
    monkeypatch.setattr("learning_engine.flashcards.get_provider", lambda **kwargs: mock_provider)

    csv_path = generate_flashcards("computing/infrastructure/kubernetes/01_control_plane_and_etcd")
    assert csv_path.exists()
    content = csv_path.read_text(encoding="utf-8")
    assert "#separator:Comma" in content
    assert "What is etcd?" in content
