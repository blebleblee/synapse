"""
Unit and Functional Tests for Node Model Pinning
"""

import pytest
from learning_engine.models import (
    normalize_host_key,
    get_configured_node_pins,
    get_node_pin,
    save_configured_node_pins
)
from fastapi.testclient import TestClient
from app.backend.main import app

client = TestClient(app)

def test_normalize_host_key():
    assert normalize_host_key("http://192.168.200.60:8080/") == "192.168.200.60:8080"
    assert normalize_host_key("https://studio.2464.cz:11434") == "studio.2464.cz:11434"
    assert normalize_host_key("localhost:11434") == "localhost:11434"

def test_get_node_pin_default_mapping():
    """Verifies that 192.168.200.60 has a pinned model."""
    pin = get_node_pin("http://192.168.200.60:8080")
    assert pin == "qwopus3.6-27b-coder-mtp:latest"

    # Also works without protocol or with port stripped
    assert get_node_pin("192.168.200.60:8080") == "qwopus3.6-27b-coder-mtp:latest"
    assert get_node_pin("192.168.200.60") == "qwopus3.6-27b-coder-mtp:latest"

def test_api_cluster_pins_endpoint():
    """Functional tests for GET and POST /api/settings/cluster-pins."""
    res = client.get("/api/settings/cluster-pins")
    assert res.status_code == 200
    data = res.json()
    assert "pins" in data
    assert isinstance(data["pins"], dict)
    assert "192.168.200.60:8080" in data["pins"] or "192.168.200.60" in data["pins"]

    # Test saving custom pin
    save_res = client.post("/api/settings/cluster-pins", json={
        "pins": {
            "test-node:11434": "qwen2.5-coder:7b"
        }
    })
    assert save_res.status_code == 200
    saved_data = save_res.json()
    assert saved_data.get("ok") is True
    assert "test-node:11434" in saved_data["pins"]
