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

def test_rate_limiting():
    ip = "192.168.1.100"
    reset_failed_attempts(ip)
    assert not is_rate_limited(ip)

    for _ in range(5):
        record_failed_attempt(ip)

    assert is_rate_limited(ip)
    reset_failed_attempts(ip)
    assert not is_rate_limited(ip)
