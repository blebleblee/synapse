"""
Regression tests for the Settings > Workspace Maintenance buttons (/api/clean).

"Clear Transient Cache" promised to clear audio and translation caches but
deleted every chat session; "Vacuum SQLite Database" did nothing yet reported
success.
"""
import sqlite3

from fastapi.testclient import TestClient

from app.backend.main import app
from learning_engine.security import get_topics_dir, get_workspace_root
from learning_engine.utils import perform_cleanup

client = TestClient(app)


def _seed_workspace():
    ws = get_workspace_root()
    session = get_topics_dir() / "computing" / "systems" / "bash" / "sessions" / "active_session.md"
    session.parent.mkdir(parents=True, exist_ok=True)
    session.write_text("chat", encoding="utf-8")
    translation = ws / ".cache" / "translations" / "abc.de.md"
    translation.parent.mkdir(parents=True, exist_ok=True)
    translation.write_text("Hallo", encoding="utf-8")
    audio = ws / "data" / "audio_cache" / "abc.mp3"
    audio.parent.mkdir(parents=True, exist_ok=True)
    audio.write_bytes(b"ID3")
    return session, translation, audio


def test_clear_caches_keeps_chat_sessions():
    session, translation, audio = _seed_workspace()
    res = client.post("/api/clean", json={"sessions": False, "exports": False, "caches": True})
    assert res.status_code == 200
    assert res.json()["cleaned"] == 2
    assert session.exists()
    assert not translation.exists()
    assert not audio.exists()
    # The cache directories stay, so later writes still work.
    assert translation.parent.is_dir()
    assert audio.parent.is_dir()


def test_default_cleanup_does_not_touch_caches():
    """Existing callers (chat 'Clear conversation') keep their behavior."""
    session, translation, audio = _seed_workspace()
    perform_cleanup(clean_sessions=True, clean_exports=False)
    assert not session.exists()
    assert translation.exists()
    assert audio.exists()


def test_vacuum_database_runs():
    from learning_engine import database
    res = client.post("/api/clean", json={"sessions": False, "exports": False, "db": True})
    assert res.status_code == 200
    data = res.json()
    assert data["vacuumed"] is True
    # The database is still usable afterwards.
    conn = sqlite3.connect(database.DB_PATH)
    try:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        conn.close()


def test_clean_without_db_flag_does_not_vacuum():
    res = client.post("/api/clean", json={"sessions": False, "exports": False})
    assert res.json()["vacuumed"] is False


def test_vacuum_failure_is_reported(monkeypatch):
    import app.backend.main as backend

    def broken():
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(backend, "vacuum_database", broken)
    res = client.post("/api/clean", json={"sessions": False, "exports": False, "db": True})
    assert res.status_code == 500
    assert "database is locked" in res.json()["detail"]


def test_vacuum_truncates_wal():
    from learning_engine import database
    from learning_engine.utils import vacuum_database
    conn = database.get_connection()
    conn.execute("CREATE TABLE IF NOT EXISTS vacuum_probe (x TEXT)")
    conn.executemany("INSERT INTO vacuum_probe VALUES (?)", [("x" * 500,)] * 200)
    conn.commit()
    # Keep a connection open, as the running server does; otherwise SQLite
    # checkpoints on the last close and hides the bug.
    try:
        wal = database.DB_PATH.with_name(database.DB_PATH.name + "-wal")
        vacuum_database()
        assert wal.stat().st_size == 0
    finally:
        conn.close()


def _session(rel):
    s = get_topics_dir() / rel / "sessions" / "active_session.md"
    s.parent.mkdir(parents=True, exist_ok=True)
    s.write_text("chat", encoding="utf-8")
    return s


def test_mentor_clear_removes_only_the_current_topics_session():
    """Owner decision: "Clear conversation" in the mentor window clears that
    topic's chat; Settings clears everything. The mentor button used to delete
    every topic's saved sessions."""
    bash = _session("computing/systems/bash")
    k8s = _session("computing/infrastructure/kubernetes")
    res = client.delete("/api/chat/session", params={"query": "computing/systems/bash"})
    assert res.status_code == 200
    assert not bash.exists()
    assert k8s.exists()


def test_mentor_clear_without_a_topic_clears_the_workspace_session_only():
    k8s = _session("computing/infrastructure/kubernetes")
    ws = get_topics_dir() / ".workspace_sessions" / "active_session.md"
    ws.parent.mkdir(parents=True, exist_ok=True)
    ws.write_text("chat", encoding="utf-8")
    assert client.delete("/api/chat/session").status_code == 200
    assert not ws.exists() and k8s.exists()


def test_mentor_clear_rejects_an_unknown_topic():
    k8s = _session("computing/infrastructure/kubernetes")
    assert client.delete("/api/chat/session", params={"query": "../../etc"}).status_code in (400, 404)
    assert k8s.exists()
