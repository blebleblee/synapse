"""
Acceptance Tests for Persisted Settings and Dynamic Consumer Propagation.
Verifies that settings saved via /api/settings or config_manager correctly propagate
to their actual backend consumers:
1. auth_password -> enables auth and verifies login password.
2. cluster_hosts -> propagates to get_configured_hosts().
3. node_pins -> propagates to get_node_pin().
4. primary_model -> propagates to get_chat_provider().
"""

import os
import pytest
from fastapi.testclient import TestClient
from app.backend.main import app
from learning_engine.config_manager import save_settings, get_settings
from learning_engine.auth import is_auth_enabled, verify_password
from learning_engine.models import (
    get_configured_hosts,
    get_configured_node_pins,
    get_node_pin,
    get_chat_provider
)

client = TestClient(app)

def test_settings_auth_password_enables_authentication(monkeypatch):
    """
    When SYNAPSE_PASSWORD env var is absent, saving auth_password in database settings
    must dynamically enable authentication, protect endpoints, and accept the password.
    """
    monkeypatch.delenv("SYNAPSE_PASSWORD", raising=False)
    monkeypatch.delenv("SYNAPSE_AUTH_PASSWORD", raising=False)

    assert not is_auth_enabled()

    # Save auth password via settings API
    res = client.post("/api/settings", json={"auth_password": "DatabaseSecretPass987!"})
    assert res.status_code == 200

    # Auth must now be active
    assert is_auth_enabled()
    assert verify_password("DatabaseSecretPass987!")
    assert not verify_password("wrong_password")

    # Protected endpoint rejects unauthenticated request
    unauth_res = client.get("/api/status")
    assert unauth_res.status_code == 401

    # Login with the database-configured password succeeds
    login_res = client.post("/api/auth/login", json={"password": "DatabaseSecretPass987!"})
    assert login_res.status_code == 200
    token = login_res.json().get("token")
    assert token

    # Authenticated call succeeds
    auth_res = client.get("/api/status", headers={"Authorization": f"Bearer {token}"})
    assert auth_res.status_code == 200

def test_settings_cluster_hosts_dynamic_propagation():
    """
    Saving cluster_hosts in settings dynamically updates get_configured_hosts().
    """
    custom_hosts = ["http://10.50.0.1:11434", "http://10.50.0.2:11434"]
    res = client.post("/api/settings", json={"cluster_hosts": custom_hosts})
    assert res.status_code == 200

    loaded = get_configured_hosts()
    assert "http://10.50.0.1:11434" in loaded
    assert "http://10.50.0.2:11434" in loaded

def test_settings_node_pins_dynamic_propagation():
    """
    Saving node_pins in settings dynamically updates get_node_pin().
    """
    pins = {"10.50.0.1:11434": "qwen2.5-coder:32b"}
    res = client.post("/api/settings", json={"node_pins": pins})
    assert res.status_code == 200

    pin = get_node_pin("http://10.50.0.1:11434")
    assert pin == "qwen2.5-coder:32b"

def test_settings_chat_provider_picks_up_primary_model(monkeypatch):
    """
    When model is not explicitly passed to get_chat_provider(), it resolves
    the primary_model from database settings.
    """
    save_settings({"primary_model": "custom-chat-model:14b"})

    class MockCluster:
        def select_node_for_model(self, model):
            return "http://mock-node:11434", model

        def get_cluster_status(self):
            return {"http://mock-node:11434": {"online": True, "models": ["custom-chat-model:14b"]}}

    monkeypatch.setattr("learning_engine.models.OllamaCluster", MockCluster)

    provider, used_model = get_chat_provider()
    assert used_model == "custom-chat-model:14b"
    assert provider.host == "http://mock-node:11434"


def test_cluster_status_probes_requested_hosts_under_their_own_names(monkeypatch):
    """Settings lists hosts as typed ('localhost'); the status must come back under those names."""
    from fastapi.testclient import TestClient
    import app.backend.main as be_main
    import learning_engine.models as le_models

    seen = []
    def fake_available(host, timeout=1.5):
        seen.append(host)
        return host == "http://localhost:11434"
    monkeypatch.setattr(le_models.OllamaProvider, "is_available", staticmethod(fake_available))
    monkeypatch.setattr(le_models.OllamaProvider, "list_models", staticmethod(lambda host: ["m1:latest"]))

    client = TestClient(be_main.app)
    res = client.get("/api/settings/cluster-status", params={"hosts": "http://localhost:11434/,http://10.0.0.9:11434"})
    assert res.status_code == 200
    data = res.json()
    assert set(data) == {"http://localhost:11434", "http://10.0.0.9:11434"}
    assert data["http://localhost:11434"]["online"] is True
    assert data["http://localhost:11434"]["models"] == ["m1:latest"]
    assert data["http://10.0.0.9:11434"]["online"] is False


def test_cluster_status_rejects_non_http_hosts():
    from fastapi.testclient import TestClient
    import app.backend.main as be_main
    res = TestClient(be_main.app).get("/api/settings/cluster-status", params={"hosts": "file:///etc/passwd"})
    assert res.status_code == 400
