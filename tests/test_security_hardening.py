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


# --- #9: no tokens in URLs; one-time WebSocket tickets -----------------------

def test_query_string_token_not_accepted_for_http(monkeypatch):
    monkeypatch.setenv("SYNAPSE_PASSWORD", "pw-query")
    token = auth.generate_auth_token()
    client = TestClient(app)
    assert client.get(f"/api/status?token={token}").status_code == 401
    assert client.get("/api/status", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    status = client.get(f"/api/auth/status?token={token}").json()
    assert status["authenticated"] is False


def test_ws_ticket_requires_auth_and_is_single_use(monkeypatch):
    monkeypatch.setenv("SYNAPSE_PASSWORD", "pw-ticket")
    client = TestClient(app)
    assert client.post("/api/auth/ws-ticket").status_code == 401

    token = auth.generate_auth_token()
    res = client.post("/api/auth/ws-ticket", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    ticket = res.json()["ticket"]
    assert auth.consume_ws_ticket(ticket) is True
    assert auth.consume_ws_ticket(ticket) is False
    assert auth.consume_ws_ticket(None) is False
    assert auth.consume_ws_ticket("forged") is False


def test_ws_ticket_expires(monkeypatch):
    ticket = auth.issue_ws_ticket()
    real_time = auth.time.time
    monkeypatch.setattr(auth.time, "time", lambda: real_time() + auth.WS_TICKET_TTL_SECONDS + 1)
    assert auth.consume_ws_ticket(ticket) is False


def test_terminal_ws_rejects_bearer_token_in_url(monkeypatch):
    monkeypatch.setenv("SYNAPSE_PASSWORD", "pw-ws")
    token = auth.generate_auth_token()
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(f"/ws/terminal?token={token}") as ws:
            ws.receive_text()
    assert exc.value.code == 1008


def test_terminal_ws_without_ticket_closes_with_policy_code(monkeypatch):
    """Missing ticket must reach the browser as close code 1008, not a bare
    handshake 403 (seen as 1006), so the terminal stops reconnecting."""
    monkeypatch.setenv("SYNAPSE_PASSWORD", "pw-ws")
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws/terminal?env=host") as ws:
            ws.receive_text()
    assert exc.value.code == 1008
    assert exc.value.reason == "Authentication required"


# --- #10: rate limiter ---------------------------------------------------------

def test_rate_limit_check_does_not_grow_state():
    auth._FAILED_ATTEMPTS.clear()
    for i in range(50):
        assert auth.is_rate_limited(f"10.0.0.{i}") is False
    assert auth._FAILED_ATTEMPTS == {}


def test_rate_limit_prunes_expired_entries(monkeypatch):
    auth._FAILED_ATTEMPTS.clear()
    now = auth.time.time()
    for i in range(5):
        auth._FAILED_ATTEMPTS[f"old-{i}"] = (1, now - auth.LOCKOUT_WINDOW_SECONDS - 5)
    monkeypatch.setattr(auth, "_MAX_TRACKED_IPS", 5)
    auth.record_failed_attempt("fresh")
    assert set(auth._FAILED_ATTEMPTS) == {"fresh"}
    auth._FAILED_ATTEMPTS.clear()


class _FakeRequest:
    def __init__(self, peer, xff=None):
        self.client = type("C", (), {"host": peer})()
        self.headers = {"x-forwarded-for": xff} if xff else {}


def test_client_ip_ignores_forwarded_header_by_default(monkeypatch):
    monkeypatch.delenv("SYNAPSE_TRUST_PROXY", raising=False)
    assert auth.get_client_ip(_FakeRequest("10.1.1.1", "6.6.6.6")) == "10.1.1.1"


def test_client_ip_uses_proxy_appended_entry_when_trusted(monkeypatch):
    monkeypatch.setenv("SYNAPSE_TRUST_PROXY", "1")
    # Client spoofs the first entry; the proxy appends the real address last.
    assert auth.get_client_ip(_FakeRequest("10.1.1.1", "1.2.3.4, 203.0.113.9")) == "203.0.113.9"
    assert auth.get_client_ip(_FakeRequest("10.1.1.1")) == "10.1.1.1"


# --- #11: settings never expose secrets ---------------------------------------

def test_settings_api_redacts_secrets_and_hides_signing_key():
    from learning_engine.config_manager import save_settings, get_settings, REDACTED_PLACEHOLDER
    auth.get_server_secret()  # ensure auth:server_secret exists in the DB
    save_settings({"anthropicApiKey": "sk-real-anthropic", "auth_password": "pw-real", "theme": "dracula"})

    # Saving auth_password enables protection, so authenticate the request.
    headers = {"Authorization": f"Bearer {auth.generate_auth_token()}"}
    client = TestClient(app)
    res = client.get("/api/settings", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert not any(k.startswith("auth:") for k in body)
    assert body["anthropicApiKey"] == REDACTED_PLACEHOLDER
    assert body["auth_password"] == REDACTED_PLACEHOLDER
    assert body["theme"] == "dracula"
    assert "sk-real-anthropic" not in str(body)


def test_settings_roundtrip_with_placeholder_keeps_stored_secret():
    from learning_engine.config_manager import save_settings, get_settings
    save_settings({"geminiApiKey": "gm-real", "theme": "nord"})

    client = TestClient(app)
    body = client.get("/api/settings").json()
    body["theme"] = "monokai"
    assert client.post("/api/settings", json=body).status_code == 200

    stored = get_settings()
    assert stored["geminiApiKey"] == "gm-real"
    assert stored["theme"] == "monokai"

    assert client.post("/api/settings", json={"geminiApiKey": "gm-new"}).status_code == 200
    assert get_settings()["geminiApiKey"] == "gm-new"


def test_settings_api_cannot_overwrite_signing_key():
    from learning_engine.config_manager import get_settings
    before = auth.get_server_secret()
    client = TestClient(app)
    res = client.post("/api/settings", json={"auth:server_secret": "attacker-known"})
    assert res.status_code == 400
    assert auth.get_server_secret() == before
    assert get_settings().get("auth:server_secret") != "attacker-known"


# --- Pre-commit staged content & privacy guard tests ------------------------

def test_check_staged_content_detects_private_domains():
    from scripts.check_staged_content import is_private_path

    # Core public domain files must pass
    ok, _ = is_private_path("topics/computing/data/postgresql/lesson_01.md")
    assert ok is False

    ok, _ = is_private_path("topics/engineering/hardware/fpga/lesson_01.md")
    assert ok is False

    # Private domains must be detected and rejected
    private, reason = is_private_path("topics/chemistry/organic/lesson_01.md")
    assert private is True
    assert "chemistry" in reason

    private, reason = is_private_path("topics/composing/harmony/lesson_01.md")
    assert private is True
    assert "composing" in reason

    # Private language tracks must be detected and rejected
    private, reason = is_private_path("topics/languages/czech/lesson_01.md")
    assert private is True

    private, reason = is_private_path("topics/languages/german/lesson_01.md")
    assert private is True

    # Sessions and blueprints must be detected and rejected
    private, reason = is_private_path("topics/computing/sessions/active_session.md")
    assert private is True

    private, reason = is_private_path("topics/computing/chat_history.json")
    assert private is True

    private, reason = is_private_path("topics/computing/CURRICULUM_BLUEPRINT.md")
    assert private is True


def test_check_staged_content_detects_secrets():
    from scripts.check_staged_content import find_secrets_in_text

    # Safe placeholder keys must be ignored
    clean_text = 'ANTHROPIC_KEY = "test_dummy_key_12345"\nGEMINI_KEY = "dummy_placeholder_gemini_key"'
    hits = find_secrets_in_text(clean_text, "test.py")
    assert len(hits) == 0

    # Live key patterns must be flagged (constructed dynamically so source file is not flagged by gitleaks)
    ant_prefix = "sk-ant-" + "api03-"
    leaked_text = f'KEY = "{ant_prefix}livecredentialtoken1234567890"'
    hits = find_secrets_in_text(leaked_text, "config.py")
    assert len(hits) == 1
    assert hits[0][1] == "Anthropic API Key"

