"""
Regression & Verification Tests for Test Process Isolation Protections.
Verifies that:
1. Global isolation does not depend on test names or parametrization.
2. Database, workspace, and topics paths resolve strictly inside temporary directories.
3. Unexpected outbound network connections, urllib downloads, and LLM calls are blocked.
4. Real subprocess execution and PTY/shell launches are blocked.
5. In-process ASGI API testing remains fully functional without touching the network stack.
"""

import os
import socket
import urllib.request
import subprocess
import pytest
from pathlib import Path

from learning_engine.security import get_workspace_root, get_topics_dir
from learning_engine.database import get_db_path
from learning_engine.models import (
    get_cluster_config_path,
    get_node_pins_config_path,
    AnthropicProvider,
    GeminiProvider,
    OllamaProvider
)
from learning_engine.packages import get_packs_dir
from fastapi.testclient import TestClient
from app.backend.main import app

_REPO_ROOT = Path(__file__).resolve().parent.parent


def test_isolation_unnamed_and_arbitrary_test_has_isolated_paths():
    """
    Demonstrates that isolation does NOT depend on test names, module names, or parametrization.
    An arbitrary test name runs fully isolated in unique temporary directories.
    """
    # 1. Environment variables must point to temporary paths
    env_db = Path(os.environ["SYNAPSE_DB_PATH"]).resolve()
    env_ws = Path(os.environ["SYNAPSE_WORKSPACE"]).resolve()
    env_topics = Path(os.environ["SYNAPSE_TOPICS_DIR"]).resolve()

    assert env_db != (_REPO_ROOT / "data" / "synapse.db").resolve()
    assert env_ws != _REPO_ROOT.resolve()
    assert env_topics != (_REPO_ROOT / "topics").resolve()

    # 2. Database path resolution
    resolved_db = get_db_path().resolve()
    assert resolved_db == env_db
    assert not resolved_db.is_relative_to(_REPO_ROOT / "data")

    import learning_engine.database as le_db
    assert Path(le_db.DB_PATH).resolve() == env_db

    # 3. Workspace root and topics directory resolution
    resolved_ws = get_workspace_root().resolve()
    resolved_topics = get_topics_dir().resolve()
    assert resolved_ws == env_ws
    assert resolved_topics == env_topics
    assert resolved_ws != _REPO_ROOT.resolve()
    assert resolved_topics != (_REPO_ROOT / "topics").resolve()

    import learning_engine.security as le_sec
    assert Path(le_sec.WORKSPACE_ROOT).resolve() == env_ws
    assert Path(le_sec.TOPICS_DIR).resolve() == env_topics

    # 4. Config paths resolution
    resolved_cluster = get_cluster_config_path().resolve()
    resolved_pins = get_node_pins_config_path().resolve()
    resolved_packs = get_packs_dir().resolve()

    assert resolved_cluster.is_relative_to(env_ws)
    assert resolved_pins.is_relative_to(env_ws)
    assert resolved_packs.is_relative_to(env_ws)

    assert resolved_cluster != (_REPO_ROOT / ".synapse_cluster.json").resolve()
    assert resolved_pins != (_REPO_ROOT / ".synapse_node_pins.json").resolve()

    # 5. App module attributes resolution
    import app.backend.main as be_main
    assert Path(be_main.WORKSPACE_ROOT).resolve() == env_ws
    assert Path(be_main.TOPICS_DIR).resolve() == env_topics


def test_unexpected_outbound_network_rejected():
    """
    Verifies that unexpected outbound network connections and downloads
    are rejected without actually contacting an external service.
    """
    # 1. urllib.request.urlopen must raise test-protection error
    with pytest.raises(RuntimeError, match="blocked in test environment"):
        urllib.request.urlopen("https://example.com")

    # 2. urllib.request.urlretrieve must raise test-protection error
    with pytest.raises(RuntimeError, match="blocked in test environment"):
        urllib.request.urlretrieve("https://example.com/test.zip")

    # 3. socket.create_connection must raise test-protection error
    with pytest.raises(RuntimeError, match="blocked in test environment"):
        socket.create_connection(("example.com", 80))


def test_unexpected_ai_generation_rejected():
    """
    Verifies that unmocked live AI provider generation paths are blocked
    without attempting external API calls.
    """
    with pytest.raises(RuntimeError, match="blocked in test environment"):
        AnthropicProvider().generate("What is eBPF?")

    with pytest.raises(RuntimeError, match="blocked in test environment"):
        GeminiProvider().generate("What is eBPF?")

    with pytest.raises(RuntimeError, match="blocked in test environment"):
        OllamaProvider().generate("What is eBPF?")


def test_unexpected_subprocess_rejected():
    """
    Verifies that real subprocess executions are blocked without starting a process.
    """
    with pytest.raises(RuntimeError, match="blocked in tests"):
        subprocess.run(["echo", "hello"])

    with pytest.raises(RuntimeError, match="blocked in tests"):
        subprocess.Popen(["echo", "hello"])

    with pytest.raises(RuntimeError, match="blocked in tests"):
        subprocess.call(["echo", "hello"])


def test_unexpected_pty_launch_rejected():
    """
    Verifies that real PTY/shell launches are blocked without opening a PTY device.
    """
    try:
        import pty
    except ImportError:
        pytest.skip("pty module not available on this platform")

    with pytest.raises(RuntimeError, match="blocked in tests"):
        pty.openpty()

    with pytest.raises(RuntimeError, match="blocked in tests"):
        pty.fork()


def test_in_process_api_testing_preserved():
    """
    Verifies that in-process ASGI testing with TestClient succeeds cleanly
    and is not broken by the outbound network socket blocks.
    """
    client = TestClient(app)
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert "domains" in data
    assert data["domains"] >= 11
