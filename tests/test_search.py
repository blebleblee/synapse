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


def test_generate_flashcards_writes_one_anki_header_per_line(monkeypatch):
    """Anki reads one "#key:value" header per line; on a single CSV row the
    separator would be read as "Comma,#html:true,...". Column 3 holds tags."""
    mock_provider = MagicMock()
    mock_provider.generate.return_value = '[{"front": "Q", "back": "A"}]'
    monkeypatch.setattr("learning_engine.flashcards.get_provider", lambda **kwargs: mock_provider)

    lines = generate_flashcards("computing/infrastructure/kubernetes").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "#separator:Comma"
    assert lines[1] == "#html:true"
    assert "#tags column:3" in lines
    assert lines[-1] == "Q,A,computing::kubernetes"


def test_generate_flashcards_unparseable_reply_writes_nothing(monkeypatch):
    """A reply that is not a card list must fail, not cache a placeholder deck."""
    import pytest
    from learning_engine.topic_manager import resolve_subtopic
    mock_provider = MagicMock()
    mock_provider.generate.return_value = "Sorry, I cannot help with that."
    monkeypatch.setattr("learning_engine.flashcards.get_provider", lambda **kwargs: mock_provider)
    csv_file = resolve_subtopic("computing/infrastructure/kubernetes")[3] / "flashcards.csv"
    if csv_file.exists():
        csv_file.unlink()

    with pytest.raises(ValueError):
        generate_flashcards("computing/infrastructure/kubernetes")
    assert not csv_file.exists()


def test_anki_download_serves_existing_deck_without_regenerating(monkeypatch):
    """The export used to regenerate (and overwrite) the deck on every click."""
    import app.backend.main as backend
    from learning_engine.topic_manager import resolve_subtopic
    csv_file = resolve_subtopic("computing/infrastructure/kubernetes")[3] / "flashcards.csv"
    csv_file.write_text("#separator:Comma\nKeep me,Yes,t\n", encoding="utf-8")

    def must_not_generate(*a, **k):
        raise AssertionError("regenerated an existing deck")

    monkeypatch.setattr(backend, "generate_flashcards", must_not_generate)
    res = client.get("/api/flashcards?query=computing/infrastructure/kubernetes")
    assert res.status_code == 200
    assert "Keep me,Yes,t" in res.text


def test_anki_download_fixes_old_single_line_header(monkeypatch):
    from learning_engine.topic_manager import resolve_subtopic
    csv_file = resolve_subtopic("computing/infrastructure/kubernetes")[3] / "flashcards.csv"
    csv_file.write_text("#separator:Comma,#html:true,#tags:computing infrastructure kubernetes\r\nQ,A,computing::kubernetes\r\n", encoding="utf-8")
    res = client.get("/api/flashcards?query=computing/infrastructure/kubernetes")
    assert res.status_code == 200
    assert res.text.splitlines() == [
        "#separator:Comma", "#html:true", "#tags:computing infrastructure kubernetes", "#tags column:3",
        "Q,A,computing::kubernetes",
    ]
    assert 'filename="computing_infrastructure_kubernetes_flashcards.csv"' in res.headers["content-disposition"]


def test_generate_flashcards_keeps_cards_around_a_broken_one(monkeypatch):
    """One card with unescaped quotes made the whole reply invalid JSON, so
    the deck failed to generate."""
    mock_provider = MagicMock()
    mock_provider.generate.return_value = (
        '```json\n[{"front": "What does $? hold?", "back": "The last exit status."},\n'
        ' {"front": "Output of echo "hi"?", "back": "hi"},\n'
        ' {"front": "What is ${#var}?", "back": "The length of var."}]\n```')
    monkeypatch.setattr("learning_engine.flashcards.get_provider", lambda **kwargs: mock_provider)

    content = generate_flashcards("computing/infrastructure/kubernetes").read_text(encoding="utf-8")
    assert "What does $? hold?" in content
    assert "What is ${#var}?" in content
    assert "echo" not in content
