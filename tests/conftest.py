"""
Pytest configuration and test-process isolation protections for Synapse.
Enforces:
1. Global temporary workspace, topics directory, and unique SQLite database for ALL tests.
2. Interception of unexpected outbound network connections, urllib downloads, and LLM calls.
3. Interception of real subprocess executions and PTY/shell launches.
4. Active regression monitoring to guarantee real repository files are never touched.
"""

import sys
import os
import shutil
import tempfile
import atexit
import socket
import urllib.request
import subprocess
import pytest
from pathlib import Path

# Identify real repo root
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Early Database & Run Isolation:
# Unconditionally override any inherited SYNAPSE_DB_PATH, SYNAPSE_WORKSPACE, or SYNAPSE_TOPICS_DIR.
# Create a unique temporary directory per test run.
_GLOBAL_RUN_TMPDIR = Path(tempfile.mkdtemp(prefix="synapse_test_run_")).resolve()

def _cleanup_run_dir():
    try:
        shutil.rmtree(_GLOBAL_RUN_TMPDIR, ignore_errors=True)
    except Exception:
        pass

atexit.register(_cleanup_run_dir)

# Template seed workspace and topics directory
_SEED_WORKSPACE = _GLOBAL_RUN_TMPDIR / "seed_workspace"
_SEED_TOPICS_DIR = _SEED_WORKSPACE / "topics"
_SEED_TOPICS_DIR.mkdir(parents=True, exist_ok=True)
(_SEED_WORKSPACE / "data").mkdir(parents=True, exist_ok=True)
(_SEED_WORKSPACE / "exports" / "packages").mkdir(parents=True, exist_ok=True)

# Set early environment overrides before any application modules are imported
_INITIAL_RUN_DB = _SEED_WORKSPACE / "data" / "early_synapse.db"
os.environ["SYNAPSE_DB_PATH"] = str(_INITIAL_RUN_DB)
os.environ["SYNAPSE_WORKSPACE"] = str(_SEED_WORKSPACE)
os.environ["SYNAPSE_TOPICS_DIR"] = str(_SEED_TOPICS_DIR)

_CORE_DOMAINS = [
    "arts", "business", "computing", "crafts", "economics", "engineering",
    "formal_sciences", "health_sciences", "humanities", "languages",
    "motorsports", "natural_sciences"
]

for d in _CORE_DOMAINS:
    target_d = _SEED_TOPICS_DIR / d
    target_d.mkdir(parents=True, exist_ok=True)
    real_syllabus = _REPO_ROOT / "topics" / d / "SYLLABUS.md"
    if real_syllabus.exists():
        shutil.copy2(real_syllabus, target_d / "SYLLABUS.md")
    else:
        (target_d / "SYLLABUS.md").write_text(f"# {d.title()} Syllabus\n", encoding="utf-8")

    real_gemini = _REPO_ROOT / "topics" / d / "GEMINI.md"
    if real_gemini.exists():
        shutil.copy2(real_gemini, target_d / "GEMINI.md")

# Copy the specific course fixtures required by existing functional assertions
_FIXTURE_COURSES = [
    Path("computing/infrastructure/kubernetes"),
    Path("computing/data/postgresql"),
    Path("computing/systems/bash"),
    Path("computing/ai/deep_learning"),
    Path("computing/ai/large_language_models"),
    Path("arts/music_performance/bass_guitar"),
]

for course_rel in _FIXTURE_COURSES:
    src_course = _REPO_ROOT / "topics" / course_rel
    dst_course = _SEED_TOPICS_DIR / course_rel
    if src_course.exists():
        dst_course.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_course, dst_course, dirs_exist_ok=True)


@pytest.fixture(autouse=True)
def isolate_test_auth(monkeypatch):
    """
    By default, tests run in open single-user mode (auth disabled)
    so standard endpoint functional tests pass without needing tokens.
    Authentication-specific tests in test_auth.py explicitly set SYNAPSE_PASSWORD.
    """
    monkeypatch.delenv("SYNAPSE_PASSWORD", raising=False)
    monkeypatch.delenv("SYNAPSE_AUTH_PASSWORD", raising=False)


@pytest.fixture(autouse=True)
def global_test_isolation(tmp_path, monkeypatch):
    """
    Enforces complete filesystem, database, network, and process isolation for EVERY backend test.
    Applies unconditionally regardless of test name, module, or parametrization.
    """
    # 1. Isolated temporary workspace directory
    test_ws = tmp_path / "workspace"
    test_ws.mkdir(parents=True, exist_ok=True)
    test_packs_dir = test_ws / "exports" / "packages"
    test_packs_dir.mkdir(parents=True, exist_ok=True)

    # 2. Isolated temporary topics directory (standard workspace layout: workspace / 'topics')
    test_topics = test_ws / "topics"
    shutil.copytree(_SEED_TOPICS_DIR, test_topics)

    # Seed temporary .synapse_node_pins.json from repo defaults if present
    real_pins_file = _REPO_ROOT / ".synapse_node_pins.json"
    test_pins_file = test_ws / ".synapse_node_pins.json"
    if real_pins_file.exists():
        shutil.copy2(real_pins_file, test_pins_file)

    test_cluster_file = test_ws / ".synapse_cluster.json"

    # 3. Isolated unique SQLite database per test
    test_db_dir = test_ws / "data"
    test_db_dir.mkdir(parents=True, exist_ok=True)
    test_db_path = test_db_dir / "synapse_test.db"

    # 4. Set environment overrides
    monkeypatch.setenv("SYNAPSE_DB_PATH", str(test_db_path))
    monkeypatch.setenv("SYNAPSE_WORKSPACE", str(test_ws))
    monkeypatch.setenv("SYNAPSE_TOPICS_DIR", str(test_topics))

    # 5. Patch application module constants and cached attributes
    import learning_engine.database as le_db
    monkeypatch.setattr(le_db, "DB_PATH", test_db_path)
    le_db.init_db()

    import learning_engine.models as le_models
    monkeypatch.setattr(le_models, "CLUSTER_CONFIG_PATH", test_cluster_file)
    monkeypatch.setattr(le_models, "NODE_PINS_CONFIG_PATH", test_pins_file)

    import learning_engine.packages as le_packs
    monkeypatch.setattr(le_packs, "PACKS_DIR", test_packs_dir)

    import learning_engine.topic_manager as le_tm
    le_tm.invalidate_topic_tree_cache()

    # Dynamically patch TOPICS_DIR and WORKSPACE_ROOT across all loaded modules
    for mod in list(sys.modules.values()):
        if mod is None:
            continue
        if hasattr(mod, "TOPICS_DIR"):
            monkeypatch.setattr(mod, "TOPICS_DIR", test_topics)
        if hasattr(mod, "WORKSPACE_ROOT"):
            monkeypatch.setattr(mod, "WORKSPACE_ROOT", test_ws)

    # 6. Test-process network protections: block unexpected outbound connections
    def _blocked_create_connection(address, *args, **kwargs):
        raise RuntimeError(f"Unexpected outbound network connection blocked in test environment: {address}")

    def _blocked_urlopen(url, *args, **kwargs):
        raise RuntimeError(f"Unexpected outbound urllib.request.urlopen blocked in test environment: {url}")

    def _blocked_urlretrieve(url, *args, **kwargs):
        raise RuntimeError(f"Unexpected outbound urllib.request.urlretrieve blocked in test environment: {url}")

    monkeypatch.setattr(socket, "create_connection", _blocked_create_connection)
    monkeypatch.setattr(urllib.request, "urlopen", _blocked_urlopen)
    monkeypatch.setattr(urllib.request, "urlretrieve", _blocked_urlretrieve)

    # Simulated Ollama connectivity: safe mock without opening external network sockets
    monkeypatch.setattr(le_models.OllamaProvider, "check_connectivity", lambda host, model=None: False)
    monkeypatch.setattr(le_models.OllamaProvider, "is_available", lambda host: False)
    monkeypatch.setattr(
        le_models.OllamaCluster,
        "get_cluster_status",
        lambda self: {"http://127.0.0.1:11434": {"online": False, "models": []}}
    )

    # Block live cloud and local generation calls
    def _blocked_ai_generate(*args, **kwargs):
        raise RuntimeError("Unexpected AI generation call blocked in test environment")

    monkeypatch.setattr(le_models.AnthropicProvider, "generate", _blocked_ai_generate)
    if hasattr(le_models.AnthropicProvider, "generate_stream"):
        monkeypatch.setattr(le_models.AnthropicProvider, "generate_stream", _blocked_ai_generate)
    monkeypatch.setattr(le_models.GeminiProvider, "generate", _blocked_ai_generate)
    if hasattr(le_models.GeminiProvider, "generate_stream"):
        monkeypatch.setattr(le_models.GeminiProvider, "generate_stream", _blocked_ai_generate)
    monkeypatch.setattr(le_models.OllamaProvider, "generate", _blocked_ai_generate)
    if hasattr(le_models.OllamaProvider, "generate_stream"):
        monkeypatch.setattr(le_models.OllamaProvider, "generate_stream", _blocked_ai_generate)

    # 7. Test-process subprocess protections: block real shell launches and subprocess executions
    def _blocked_subprocess(*args, **kwargs):
        cmd = args[0] if args else kwargs.get("args", "unknown")
        raise RuntimeError(f"Real subprocess execution blocked in tests: {cmd}")

    monkeypatch.setattr(subprocess, "run", _blocked_subprocess)
    monkeypatch.setattr(subprocess, "Popen", _blocked_subprocess)
    monkeypatch.setattr(subprocess, "call", _blocked_subprocess)
    monkeypatch.setattr(subprocess, "check_call", _blocked_subprocess)
    monkeypatch.setattr(subprocess, "check_output", _blocked_subprocess)

    import asyncio
    monkeypatch.setattr(asyncio, "create_subprocess_exec", _blocked_subprocess)
    monkeypatch.setattr(asyncio, "create_subprocess_shell", _blocked_subprocess)

    try:
        import pty
        def _blocked_pty(*args, **kwargs):
            raise RuntimeError("Real PTY launch blocked in tests")
        monkeypatch.setattr(pty, "openpty", _blocked_pty)
        monkeypatch.setattr(pty, "fork", _blocked_pty)
    except (ImportError, AttributeError):
        pass

    # 8. Isolate chat session logging to temp directory
    import app.backend.main as be_main
    session_dir = test_ws / "sessions"
    session_dir.mkdir(parents=True, exist_ok=True)

    def _safe_save_chat_session(sub_path, user_msg, tutor_reply, history):
        entry_file = session_dir / "active_session.md"
        with open(entry_file, "a", encoding="utf-8") as f:
            f.write(f"Student: {user_msg}\nTutor: {tutor_reply}\n")

    monkeypatch.setattr(be_main, "save_chat_session", _safe_save_chat_session)

    # 9. Pre-test snapshot of real repository data and topics
    real_data = _REPO_ROOT / "data"
    real_topics = _REPO_ROOT / "topics"
    data_files_before = {p: p.stat().st_mtime_ns for p in real_data.rglob("*") if p.is_file()} if real_data.exists() else {}
    topics_files_before = {p: p.stat().st_mtime_ns for p in real_topics.rglob("*") if p.is_file() and not p.name.endswith(".tmp")}

    yield

    # 10. Post-test assertion: ensure zero additions, modifications, or deletions in real repository
    data_files_after = {p: p.stat().st_mtime_ns for p in real_data.rglob("*") if p.is_file()} if real_data.exists() else {}
    topics_files_after = {p: p.stat().st_mtime_ns for p in real_topics.rglob("*") if p.is_file() and not p.name.endswith(".tmp")}

    assert data_files_before == data_files_after, "Safety Violation: Real data/ directory was modified during test!"
    assert topics_files_before == topics_files_after, "Safety Violation: Real topics/ directory was modified during test!"

    le_tm.invalidate_topic_tree_cache()
