"""
Regression tests for the security audit fixes:
- path containment (sibling-prefix bypass, '..' segments) in topic delete/rename
- localhost-only guard for password-less instances (LAN access, DNS rebinding)
- Origin/Host checks on the terminal WebSocket (cross-site WebSocket hijacking)
- unforgeable fallback token secret
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.backend.main import app
import learning_engine.topic_manager as tm
from learning_engine import auth
from learning_engine.security import (
    validate_workspace_path,
    validate_canonical_topic_path,
    is_allowed_host,
    is_allowed_origin,
)


# --- Path containment -------------------------------------------------------

def test_validate_workspace_path_rejects_sibling_prefix(tmp_path):
    base = tmp_path / "topics"
    (tmp_path / "topics_backup").mkdir(parents=True)
    base.mkdir()
    with pytest.raises(ValueError):
        validate_workspace_path(base, base / "x" / ".." / ".." / "topics_backup")


def test_validate_canonical_topic_path_rejects_sibling_prefix(tmp_path):
    base = tmp_path / "topics"
    base.mkdir()
    with pytest.raises(ValueError):
        validate_canonical_topic_path(tmp_path / "topics_evil" / "a" / "b", base_topics_dir=base)


@pytest.mark.parametrize("bad", [
    "computing/..",
    "computing/.",
    "computing/../..",
    "computing/../../topics_backup",
    "computing//x",
    "computing",
    "",
    "/",
    "computing/x/../../..",
])
def test_delete_subtopic_rejects_traversal(bad):
    topics = Path(tm.TOPICS_DIR).resolve()
    sibling = topics.parent / "topics_backup"
    sibling.mkdir(exist_ok=True)
    before = sorted(p.name for p in topics.iterdir())

    assert tm.delete_subtopic(bad) is False

    assert topics.exists()
    assert sibling.exists()
    assert sorted(p.name for p in topics.iterdir()) == before
    assert (topics / "computing").exists()


def test_delete_api_cannot_wipe_topics_dir():
    client = TestClient(app)
    res = client.delete("/api/topic", params={"path": "computing/.."})
    assert res.status_code == 400
    assert Path(tm.TOPICS_DIR).exists()
    assert (Path(tm.TOPICS_DIR) / "computing").exists()


def test_delete_subtopic_still_deletes_valid_topic():
    target = Path(tm.TOPICS_DIR) / "computing" / "sec_cat" / "sec_topic"
    target.mkdir(parents=True)
    assert tm.delete_subtopic("computing/sec_cat/sec_topic") is True
    assert not target.exists()
    assert (Path(tm.TOPICS_DIR) / "computing").exists()


def test_rename_strips_markdown_breaking_characters():
    domain_dir = Path(tm.TOPICS_DIR) / "computing"
    syllabus = domain_dir / "SYLLABUS.md"
    original = syllabus.read_text(encoding="utf-8") if syllabus.exists() else None
    try:
        syllabus.write_text("# Syllabus\n- **Old** (`cat/topic/`)\n", encoding="utf-8")
        assert tm.rename_subtopic("computing/cat/topic", "New\n# Injected `x` **y**") is True
        lines = syllabus.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 2
        assert lines[1].startswith("- **New # Injected x y** (`cat/topic/`)")
        assert tm.rename_subtopic("computing/cat/..", "x") is False
    finally:
        if original is None:
            syllabus.unlink(missing_ok=True)
        else:
            syllabus.write_text(original, encoding="utf-8")


# --- Host guard (no password => localhost only) ------------------------------

@pytest.mark.parametrize("host,ok", [
    ("localhost:8000", True),
    ("127.0.0.1:8000", True),
    ("[::1]:8000", True),
    ("localhost", True),
    ("192.168.1.20:8000", False),
    ("evil.example:8000", False),
    ("localhost.evil.example", False),
    ("", False),
    (None, False),
])
def test_is_allowed_host(monkeypatch, host, ok):
    monkeypatch.delenv("SYNAPSE_ALLOWED_HOSTS", raising=False)
    assert is_allowed_host(host) is ok


def test_open_instance_rejects_non_local_host():
    client = TestClient(app)
    res = client.get("/api/status", headers={"Host": "evil.example:8000"})
    assert res.status_code == 403
    res = client.get("/api/status", headers={"Host": "127.0.0.1:8000"})
    assert res.status_code == 200


def test_password_protected_instance_allows_remote_host_with_auth(monkeypatch):
    monkeypatch.setenv("SYNAPSE_PASSWORD", "pw-for-remote")
    client = TestClient(app)
    res = client.get("/api/status", headers={"Host": "synapse.example.com"})
    assert res.status_code == 401  # reaches auth instead of host guard
    token = auth.generate_auth_token()
    res = client.get("/api/status", headers={"Host": "synapse.example.com", "Authorization": f"Bearer {token}"})
    assert res.status_code == 200


# --- Origin guard / terminal WebSocket ---------------------------------------

@pytest.mark.parametrize("origin,host,ok", [
    (None, "127.0.0.1:8000", True),
    ("http://127.0.0.1:8000", "127.0.0.1:8000", True),
    ("http://localhost:5173", "127.0.0.1:8000", True),
    ("https://evil.example", "127.0.0.1:8000", False),
    ("http://127.0.0.1:8000.evil.example", "127.0.0.1:8000", False),
    ("null", "127.0.0.1:8000", False),
])
def test_is_allowed_origin(monkeypatch, origin, host, ok):
    monkeypatch.delenv("SYNAPSE_ALLOWED_ORIGINS", raising=False)
    assert is_allowed_origin(origin, host) is ok


def test_terminal_ws_rejects_cross_site_origin():
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws/terminal", headers={"Origin": "https://evil.example"}):
            pass
    assert exc.value.code == 1008


def test_terminal_ws_rejects_non_local_host_when_open():
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(
            "/ws/terminal",
            headers={"Host": "attacker.example:8000", "Origin": "http://attacker.example:8000"},
        ):
            pass
    assert exc.value.code == 1008


def test_cors_does_not_reflect_arbitrary_origin():
    client = TestClient(app)
    res = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert res.headers.get("access-control-allow-origin") not in ("*", "https://evil.example")


# --- Token secret fallback ---------------------------------------------------

def test_fallback_secret_is_random_not_hardcoded(monkeypatch):
    monkeypatch.delenv("SYNAPSE_SECRET_KEY", raising=False)

    def _boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(auth, "get_db_connection", _boom)
    monkeypatch.setattr(auth, "_EPHEMERAL_SECRET", None)
    secret = auth.get_server_secret()
    assert secret != "synapse-instance-ephemeral-secret-key"
    assert len(secret) >= 64
    assert auth.get_server_secret() == secret  # stable within the process
