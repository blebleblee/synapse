import os
import pytest
from fastapi.testclient import TestClient
from learning_engine.auth import (
    is_auth_enabled,
    verify_password,
    generate_auth_token,
    verify_auth_token,
    is_rate_limited,
    record_failed_attempt,
    reset_failed_attempts
)
from app.backend.main import app

def test_auth_disabled_by_default(monkeypatch):
    monkeypatch.delenv("SYNAPSE_PASSWORD", raising=False)
    monkeypatch.delenv("SYNAPSE_AUTH_PASSWORD", raising=False)
    assert not is_auth_enabled()
    assert verify_auth_token("arbitrary-or-none")

    client = TestClient(app)
    res = client.get("/api/auth/status")
    assert res.status_code == 200
    assert res.json()["auth_required"] is False
    assert res.json()["authenticated"] is True

def test_auth_enabled_protection(monkeypatch):
    monkeypatch.setenv("SYNAPSE_PASSWORD", "SuperSecretPass123!")
    assert is_auth_enabled()
    assert verify_password("SuperSecretPass123!")
    assert not verify_password("wrongpassword")

    token = generate_auth_token()
    assert verify_auth_token(token)
    assert not verify_auth_token("invalid.token")
    assert not verify_auth_token(None)

    client = TestClient(app)

    # 1. Unauthenticated request to /api/status should fail with 401
    res = client.get("/api/status")
    assert res.status_code == 401

    # 2. Status endpoint reports auth_required
    res_status = client.get("/api/auth/status")
    assert res_status.status_code == 200
    assert res_status.json()["auth_required"] is True
    assert res_status.json()["authenticated"] is False

    # 3. Failed login
    res_fail = client.post("/api/auth/login", json={"password": "wrong"})
    assert res_fail.status_code == 401

    # 4. Successful login
    res_login = client.post("/api/auth/login", json={"password": "SuperSecretPass123!"})
    assert res_login.status_code == 200
    auth_token = res_login.json()["token"]
    assert auth_token

    # 5. Authenticated request with Bearer token succeeds
    res_auth = client.get("/api/status", headers={"Authorization": f"Bearer {auth_token}"})
    assert res_auth.status_code == 200

    # 6. Authenticated request with X-Synapse-Token header succeeds
    res_header = client.get("/api/status", headers={"X-Synapse-Token": auth_token})
    assert res_header.status_code == 200

from starlette.websockets import WebSocketDisconnect

def test_terminal_websocket_auth_rejection(monkeypatch):
    """
    Verifies that /ws/terminal rejects unauthenticated connections with code 1008
    before opening a PTY or accepting the connection.
    """
    monkeypatch.setenv("SYNAPSE_PASSWORD", "SuperSecretPass123!")
    client = TestClient(app)

    # 1. Connecting without token raises WebSocketDisconnect with code 1008
    with pytest.raises(WebSocketDisconnect) as exc1:
        with client.websocket_connect("/ws/terminal"):
            pass
    assert exc1.value.code == 1008

    # 2. Connecting with invalid token raises WebSocketDisconnect with code 1008
    with pytest.raises(WebSocketDisconnect) as exc2:
        with client.websocket_connect("/ws/terminal?token=invalid_bogus_token"):
            pass
    assert exc2.value.code == 1008

def test_protected_endpoints_surface(monkeypatch):
    """
    Verifies that all core curriculum, mastery, generation, settings, and package
    endpoints return 401 when authentication is enabled, while public endpoints remain accessible.
    """
    monkeypatch.setenv("SYNAPSE_PASSWORD", "SuperSecretPass123!")
    client = TestClient(app)

    # Public endpoints must succeed without token
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/auth/status").status_code == 200

    # Protected endpoints must reject unauthenticated requests with 401
    protected_gets = [
        "/api/tree",
        "/api/topic?query=computing/data/postgresql",
        "/api/packages",
        "/api/settings",
        "/api/mastery"
    ]
    for endpoint in protected_gets:
        res = client.get(endpoint)
        assert res.status_code == 401, f"Expected 401 for unauthenticated GET {endpoint}, got {res.status_code}"

    protected_posts = [
        ("/api/mastery", {"path": "computing/data/postgresql", "state": "studying"}),
        ("/api/quiz", {"query": "computing/data/postgresql"}),
        ("/api/settings/cluster", {"hosts": ["http://127.0.0.1:11434"]}),
    ]
    for endpoint, payload in protected_posts:
        res = client.post(endpoint, json=payload)
        assert res.status_code == 401, f"Expected 401 for unauthenticated POST {endpoint}, got {res.status_code}"

    # Authenticated requests with Bearer token must succeed
    token = generate_auth_token()
    auth_headers = {"Authorization": f"Bearer {token}"}
    for endpoint in protected_gets:
        res = client.get(endpoint, headers=auth_headers)
        assert res.status_code == 200, f"Expected 200 for authenticated GET {endpoint}, got {res.status_code}"

def test_rate_limiting():
    ip = "192.168.1.100"
    reset_failed_attempts(ip)
    assert not is_rate_limited(ip)

    for _ in range(5):
        record_failed_attempt(ip)

    assert is_rate_limited(ip)
    reset_failed_attempts(ip)
    assert not is_rate_limited(ip)
