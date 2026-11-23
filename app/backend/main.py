"""
Learning Workbench Backend API
Provides REST APIs for topics/curricula, AI persona chat, and a WebSocket PTY terminal.
"""

import sys
import os
import select
import sqlite3
import struct
import signal
import asyncio
import time
import json
import datetime
import re
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from collections import deque

try:
    import pty
    import fcntl
    import termios
    HAS_POSIX_PTY = True
except ImportError:
    pty = None
    fcntl = None
    termios = None
    HAS_POSIX_PTY = False

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

import concurrent.futures
import threading
from collections import deque
from typing import Dict, List, Optional, Any

# Dedicated isolated threadpool for LLM execution to prevent blocking HTTP endpoints
AI_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="synapse_ai_worker")

ANSI_ESCAPE_RE = re.compile(r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
MAX_TERMINAL_LINE_LENGTH = 10000
TERMINAL_HISTORY: deque[str] = deque(maxlen=150)
LAST_TERMINAL_COMMAND: str = ""

def resolve_backspaces(s: str) -> str:
    chars = []
    for c in s:
        if c == '\b':
            if chars:
                chars.pop()
        elif c != '\r':
            chars.append(c)
    return "".join(chars)

def append_terminal_bytes(raw_bytes: bytes):
    try:
        text = raw_bytes.decode("utf-8", errors="replace")
        clean = ANSI_ESCAPE_RE.sub("", text)
        for line in clean.splitlines():
            stripped = resolve_backspaces(line).strip()
            if stripped:
                if len(stripped) > MAX_TERMINAL_LINE_LENGTH:
                    stripped = stripped[:MAX_TERMINAL_LINE_LENGTH] + "... [TRUNCATED]"
                TERMINAL_HISTORY.append(stripped)
    except Exception:
        pass

def get_terminal_lines(count: int = 50) -> List[str]:
    return list(TERMINAL_HISTORY)[-count:]

def get_terminal_text(count: int = 50) -> str:
    return "\n".join(list(TERMINAL_HISTORY)[-count:])

# Ensure workspace root is in sys.path
_DEV_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_DEV_ROOT) not in sys.path:
    sys.path.insert(0, str(_DEV_ROOT))

from learning_engine.security import (
    WORKSPACE_ROOT,
    TOPICS_DIR,
    validate_workspace_path,
    sanitize_query
)
from learning_engine.topic_manager import (
    get_topic_tree,
    get_domain_persona,
    resolve_subtopic,
    add_subtopic,
    delete_subtopic,
    rename_subtopic,
    scan_subtopic_status,
    get_unit_lessons,
    invalidate_topic_tree_cache
)
from learning_engine.utils import perform_cleanup, vacuum_database
from learning_engine.generator import generate_subtopic_content
from learning_engine.models import (
    get_provider,
    get_chat_provider,
    get_translation_provider,
    OllamaProvider,
    OllamaCluster,
    get_configured_hosts,
    save_configured_hosts,
    CLUSTER_HOST_SPECS,
    GenerationStopped,
)
from learning_engine.search import search_curriculum
from learning_engine.json_salvage import json_object_list
from learning_engine.graph import get_prerequisite_graph, get_topic_dependencies
from learning_engine.database import get_connection
from learning_engine.mastery import (
    set_subtopic_mastery,
    get_mastery_summary,
    get_subtopic_mastery,
    get_completed_lessons,
    toggle_lesson_completion,
    normalize_topic_path,
    resolve_topic_state
)
from learning_engine.security import validate_workspace_path, sanitize_query, is_dangerous_host_command, is_allowed_host, is_allowed_origin
from learning_engine.config_manager import get_settings, save_settings, redact_settings, filter_client_settings, ConfigError
from learning_engine.exporter import export_handbook
from learning_engine.flashcards import generate_flashcards, anki_csv_text
from learning_engine.packages import (
    export_topic_pack,
    install_topic_pack,
    list_installed_packs,
    uninstall_topic_pack,
    get_domain_pack_info,
    resolve_or_download_pack,
    seed_starter_curriculum
)
from learning_engine.auth import (
    get_client_ip,
    issue_ws_ticket,
    consume_ws_ticket,
    is_auth_enabled,
    verify_password,
    generate_auth_token,
    verify_auth_token,
    is_rate_limited,
    record_failed_attempt,
    reset_failed_attempts
)

from contextlib import asynccontextmanager

LAST_ACTIVITY_TIME = time.time()
ACTIVE_WEBSOCKET_COUNT = 0

@asynccontextmanager
async def lifespan(app: FastAPI):
    global LAST_ACTIVITY_TIME, ACTIVE_WEBSOCKET_COUNT
    LAST_ACTIVITY_TIME = time.time()
    try:
        seed_starter_curriculum()
    except Exception as e:
        print(f"[!] Startup curriculum seed note: {e}")

    warmers = []
    try:
        # Pre-warm topic tree cache at startup so initial browser GET /api/tree returns in 1ms
        tree_warmer = threading.Thread(target=get_topic_tree, name="tree-warm", daemon=True)
        tree_warmer.start()
        warmers.append(tree_warmer)
    except Exception:
        pass
    try:
        # Build or refresh the full-text search index in the background.
        from learning_engine.search import warm_index_in_background
        warmers.append(warm_index_in_background())
    except Exception:
        pass

    idle_task = None
    idle_timeout_str = os.environ.get("SYNAPSE_IDLE_TIMEOUT")
    if idle_timeout_str:
        try:
            timeout_sec = float(idle_timeout_str)
            if timeout_sec > 0:
                async def _idle_watcher():
                    while True:
                        await asyncio.sleep(10)
                        if ACTIVE_WEBSOCKET_COUNT == 0 and (time.time() - LAST_ACTIVITY_TIME) >= timeout_sec:
                            print(f"[*] Idle timeout reached ({timeout_sec / 60:.1f}m without requests). Initiating shutdown...", flush=True)
                            os.kill(os.getpid(), signal.SIGTERM)
                            break
                idle_task = asyncio.create_task(_idle_watcher())
        except Exception:
            pass

    yield
    # Shutdown actions
    if idle_task and not idle_task.done():
        idle_task.cancel()
    try:
        await TRANSLATIONS.shutdown()
    except Exception:
        pass
    # Let start-up warmers finish before the database is checkpointed; left
    # running, they would write into whatever database comes next.
    for t in warmers:
        if t is not None:
            await asyncio.to_thread(t.join, 15)
    try:
        from learning_engine.database import checkpoint_db
        print("[*] Synapse Backend shutting down... checkpointing database WAL...", flush=True)
        checkpoint_db(truncate=True)
    except Exception:
        pass

from learning_engine.version import __version__
from app.backend.lesson_context import lesson_excerpt
from app.backend.translation_jobs import (
    LANGUAGE_NAMES, TranslationQueue, cache_file_for, interactive_ai, read_cached, split_sections,
    translate_section,
)

app = FastAPI(title="AI Learning Workbench Backend", version=__version__, lifespan=lifespan)

_CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"] + [
    o.strip() for o in os.environ.get("SYNAPSE_ALLOWED_ORIGINS", "").split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    global LAST_ACTIVITY_TIME
    LAST_ACTIVITY_TIME = time.time()
    path = request.url.path
    auth_enabled = is_auth_enabled()

    # Without a password, the instance is only served to localhost. This blocks
    # LAN/Internet access to an open instance and DNS-rebinding from websites.
    if not auth_enabled and not is_allowed_host(request.headers.get("host")):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=403,
            content={"detail": "This Synapse instance has no password and only accepts localhost connections. "
                               "Set SYNAPSE_PASSWORD to allow remote access, or add the host to SYNAPSE_ALLOWED_HOSTS."},
        )

    # Browsers send state-changing "simple" requests cross-site without a CORS
    # preflight (e.g. a no-cors POST from any website). Reject foreign origins.
    if request.method not in ("GET", "HEAD", "OPTIONS") and not is_allowed_origin(
        request.headers.get("origin"), request.headers.get("host")
    ):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=403, content={"detail": "Cross-origin request rejected"})

    if auth_enabled and path.startswith("/api/"):
        # Public endpoints that don't require authorization
        if path in ["/api/auth/status", "/api/auth/login", "/api/health"]:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        if not token:
            token = request.headers.get("X-Synapse-Token")
        # Tokens in query strings are not accepted: they leak into access logs,
        # proxy logs and browser history.

        if not verify_auth_token(token):
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=401, content={"detail": "Authentication required"})

    return await call_next(request)

# -----------------------------------------------------------------------------
# Data Models
# -----------------------------------------------------------------------------

from pydantic import BaseModel, Field, field_validator
import re

class AddTopicRequest(BaseModel):
    domain: str
    category: str
    subtopic: str
    title: Optional[str] = None
    generate: bool = True

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    query: Optional[str] = Field(None, max_length=500)
    message: str = Field(..., min_length=1, max_length=10000)
    history: List[Any] = []
    lesson_id: Optional[str] = Field(None, pattern=r'^[a-z0-9_-]*$')
    lesson_title: Optional[str] = Field(None, max_length=200)
    section_title: Optional[str] = Field(None, max_length=200)
    terminal_context: Optional[str] = Field(None, max_length=50000)
    last_terminal_command: Optional[str] = Field(None, max_length=1000)
    # Whole lessons/labs run up to ~115k characters; lesson_excerpt() picks what the model sees.
    lesson_content: Optional[str] = Field(None, max_length=400_000)
    language: Optional[str] = Field("en", max_length=10)
    stream: Optional[bool] = False
    provider: Optional[str] = None
    model: Optional[str] = None
    host: Optional[str] = None

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        if not re.match(r'^[a-zA-Z0-9_/.-]*$', v):
            raise ValueError('Invalid characters in query')
        if ".." in v:
            raise ValueError('Path traversal detected')
        return v

class GenerateRequest(BaseModel):
    query: str
    force: bool = False
    provider: Optional[str] = None
    model: Optional[str] = None

class LoginRequest(BaseModel):
    password: str = Field(..., min_length=1, max_length=512)

# ... update chat_with_tutor to use GenerateRequest and ChatRequest ...

# -----------------------------------------------------------------------------
# REST Endpoints
# -----------------------------------------------------------------------------

@app.get("/api/auth/status")
def get_auth_status(request: Request):
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    if not token:
        token = request.headers.get("X-Synapse-Token")

    auth_required = is_auth_enabled()
    authenticated = verify_auth_token(token) if auth_required else True
    return {
        "auth_required": auth_required,
        "authenticated": authenticated
    }

@app.post("/api/auth/login")
def api_login(req: LoginRequest, request: Request):
    client_ip = get_client_ip(request)
    if is_rate_limited(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Too many failed login attempts. Please wait 60 seconds before retrying."
        )

    if not is_auth_enabled():
        return {"token": generate_auth_token(), "status": "authenticated", "auth_required": False}

    if not verify_password(req.password):
        record_failed_attempt(client_ip)
        raise HTTPException(status_code=401, detail="Invalid instance password.")

    reset_failed_attempts(client_ip)
    token = generate_auth_token()
    return {"token": token, "status": "authenticated", "auth_required": True}

@app.post("/api/auth/ws-ticket")
def api_ws_ticket():
    """One-time, 30-second ticket for /ws/terminal (requires a valid bearer token via middleware)."""
    return {"ticket": issue_ws_ticket()}

@app.get("/api/health")
async def get_health():
    return {"status": "ok", "app": "synapse-backend", "version": __version__}

@app.get("/api/status")
async def get_status():
    tree = get_topic_tree()
    total_domains = len(tree)
    total_categories = 0
    total_subtopics = 0
    with_lesson = 0
    with_labs = 0
    complete = 0

    # Get mastery counts directly from DB
    conn = get_connection()
    mastery_rows = conn.execute("SELECT path, state, completed_lessons FROM mastery").fetchall()
    conn.close()

    # Calculate curriculum stats
    for domain, ddata in tree.items():
        total_categories += len(ddata["categories"])
        for cat, cdata in ddata["categories"].items():
            total_subtopics += len(cdata)
            for sub, sdata in cdata.items():
                st = sdata["status"]
                if st["has_lesson"]: with_lesson += 1
                if st["has_labs"]: with_labs += 1
                if st["complete"]: complete += 1

    cluster = OllamaCluster()
    cluster_status = cluster.get_cluster_status()
    ollama_up = any(d["online"] for d in cluster_status.values())
    ollama_models = []
    for d in cluster_status.values():
        for m in d.get("models", []):
            if m not in ollama_models:
                ollama_models.append(m)

    return {
        "domains": total_domains,
        "categories": total_categories,
        "subtopics": total_subtopics,
        "lesson_count": with_lesson,
        "labs_count": with_labs,
        "complete_count": complete,
        "ollama_available": ollama_up,
        "ollama_models": ollama_models
    }

def _without_server_paths(node):
    """Copy of the topic tree without absolute paths (`full_path`, and each
    lesson's `path`). They are for server-side use (exports, search); the
    browser never reads them, and they reveal the server's folder layout to
    remote clients. Relative paths, which the UI uses, stay."""
    if isinstance(node, dict):
        return {k: _without_server_paths(v) for k, v in node.items()
                if k != "full_path" and not (k == "path" and isinstance(v, str) and Path(v).is_absolute())}
    if isinstance(node, list):
        return [_without_server_paths(v) for v in node]
    return node


@app.get("/api/tree")
async def get_tree():
    return _without_server_paths(get_topic_tree())

class TestOllamaRequest(BaseModel):
    host: str

@app.post("/api/settings/test-ollama")
def api_test_ollama(req: TestOllamaRequest):
    import time
    host = req.host.strip().rstrip("/")
    start = time.time()
    try:
        up = OllamaProvider.is_available(host)
        elapsed_ms = int((time.time() - start) * 1000)
        if up:
            models = OllamaProvider.list_models(host)
            return {"ok": True, "latency_ms": elapsed_ms, "models": models}
        return {"ok": False, "error": f"Host {host} is unreachable or timed out"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

class CheckConnectivityRequest(BaseModel):
    host: Optional[str] = None
    model: Optional[str] = None

@app.post("/api/check-mentor-connectivity")
def api_check_mentor_connectivity(req: CheckConnectivityRequest):
    """
    Pre-flight check for the Mentor AI connection.
    Verifies the configured host and model are accessible.
    """
    host = req.host or "http://localhost:11434"
    model = req.model
    
    # 1. Direct check
    if OllamaProvider.check_connectivity(host, model):
        return {"connected": True, "model": model} if model else {"connected": True}

    # 2. Check if cluster has any node online if no specific model/host match.
    # The chat then answers with another model; report which one.
    cluster = OllamaCluster()
    status = cluster.get_cluster_status()
    if any(d.get("online") for d in status.values()):
        result = {
            "connected": True,
            "warning": f"Model '{model or 'auto'}' is not available on {host}; the mentor uses another model.",
        }
        try:
            _, result["model"] = get_chat_provider(model=model, host=host)
        except Exception:
            pass
        return result

    return {"connected": False, "error": "Unable to connect to Ollama/LocalAI cluster."}

@app.get("/api/settings/cluster-status")
def api_cluster_status(hosts: Optional[str] = Query(None, max_length=4000)):
    """Probes Ollama nodes from the backend (browsers are blocked by Ollama's CORS rules).

    With `hosts` (comma-separated), probes exactly those and answers under the
    same names the caller used; otherwise the configured cluster.
    """
    import time
    from concurrent.futures import ThreadPoolExecutor
    from learning_engine.models import get_node_pin
    if hosts:
        targets = list(dict.fromkeys(h.strip().rstrip("/") for h in hosts.split(",") if h.strip()))[:16]
        bad = [h for h in targets if not re.match(r"^https?://[^\s/]+$", h)]
        if bad:
            raise HTTPException(status_code=400, detail=f"Not an http(s) host: {bad[0]}")
    else:
        targets = get_configured_hosts()

    def probe(h: str):
        start = time.time()
        up = OllamaProvider.is_available(h, timeout=4.0)
        elapsed_ms = int((time.time() - start) * 1000)
        return h, {
            "online": up,
            "latency_ms": elapsed_ms if up else None,
            "models": OllamaProvider.list_models(h) if up else [],
            "pinned_model": get_node_pin(h),
        }

    with ThreadPoolExecutor(max_workers=max(1, min(8, len(targets)))) as pool:
        return dict(pool.map(probe, targets))

@app.get("/api/settings/cluster-pins")
def api_get_cluster_pins():
    from learning_engine.models import get_configured_node_pins
    return {"pins": get_configured_node_pins()}

class ClusterPinsRequest(BaseModel):
    pins: Dict[str, str]

@app.post("/api/settings/cluster-pins")
def api_save_cluster_pins(req: ClusterPinsRequest):
    from learning_engine.models import save_configured_node_pins
    saved = save_configured_node_pins(req.pins)
    return {"ok": True, "pins": saved}

@app.get("/api/settings/discovered-models")
def api_discovered_models():
    """
    Scans all valid configured endpoints and returns a deduplicated, sorted list
    of unique model names ready for direct selection.
    """
    cluster = OllamaCluster()
    status = cluster.get_cluster_status()
    unique_models = []
    seen = set()

    for host, h_data in status.items():
        if not h_data.get("online"):
            continue
        for m in h_data.get("models", []):
            clean_m = m.strip()
            if clean_m and clean_m not in seen:
                seen.add(clean_m)
                unique_models.append(clean_m)

    # Cloud models
    for cm in [
        "claude-sonnet-5",
        "claude-opus-5-5",
        "claude-haiku-5-5",
        "gemini-3.8-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite"
    ]:
        if cm not in seen:
            seen.add(cm)
            unique_models.append(cm)

    unique_models.sort(key=lambda s: s.lower())

    return {
        "models": unique_models,
        "nodes_scanned": len(status),
        "nodes_online": sum(1 for d in status.values() if d.get("online"))
    }

class ClusterHostsRequest(BaseModel):
    hosts: List[str]

@app.get("/api/settings/cluster")
def api_get_cluster_hosts():
    return {"hosts": get_configured_hosts()}

@app.post("/api/settings/cluster")
def api_set_cluster_hosts(req: ClusterHostsRequest):
    if not req.hosts:
        return {"hosts": get_configured_hosts(), "saved": False}
    updated = save_configured_hosts(req.hosts)
    return {"hosts": updated, "saved": True}

@app.get("/api/search")
def api_search(q: str = Query(..., min_length=2)):
    # Plain `def`: FastAPI runs it in a worker thread. The full-text scan takes
    # seconds on a large workspace and must not block the event loop (which
    # would freeze every other request and all terminal WebSockets).
    return {"results": search_curriculum(q)}

@app.get("/api/graph")
async def api_graph():
    return get_prerequisite_graph()

@app.get("/api/topic/dependencies")
def api_topic_dependencies(query: str = Query(..., description="Relative path of topic to find dependencies for")):
    return get_topic_dependencies(query)

class MasteryUpdateRequest(BaseModel):
    path: str
    state: str

class LessonMasteryRequest(BaseModel):
    path: str
    lesson_id: str
    completed: Optional[bool] = None

@app.get("/api/mastery")
def get_mastery():
    conn = get_connection()
    rows = conn.execute("SELECT path, state, completed_lessons FROM mastery").fetchall()
    conn.close()

    grouped: Dict[str, List[Any]] = {}
    for row in rows:
        canon_path = normalize_topic_path(row["path"])
        grouped.setdefault(canon_path, []).append(row)

    topics = {}
    for canon_path, r_list in grouped.items():
        c_row = next((r for r in r_list if normalize_topic_path(r["path"]) == r["path"]), None)
        l_row = next((r for r in r_list if str(r["path"]).startswith("topics/")), None)
        state, completed = resolve_topic_state(c_row, l_row)
        topics[canon_path] = {"state": state, "completed_lessons": completed}

    return {
        "summary": get_mastery_summary(),
        "topics": topics
    }

@app.post("/api/mastery")
def update_mastery(req: MasteryUpdateRequest):
    res = set_subtopic_mastery(req.path, req.state)
    invalidate_topic_tree_cache()
    return res

@app.post("/api/mastery/lesson")
def update_lesson_mastery(req: LessonMasteryRequest):
    res = toggle_lesson_completion(req.path, req.lesson_id, req.completed)
    invalidate_topic_tree_cache()
    return res

@app.get("/api/settings")
def get_app_settings():
    # Never return the token signing key or secret values to the client.
    return redact_settings(get_settings())

@app.post("/api/settings")
def update_app_settings(settings: Dict[str, Any]):
    try:
        save_settings(filter_client_settings(settings))
    except ConfigError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "success"}

@app.get("/api/packages")
async def api_list_packages():
    domains = [
        {"domain": "arts", "title": "Arts & Music Production", "description": "Composition, acoustic DSP, synthesizers, visual arts, and performance."},
        {"domain": "business", "title": "Business & Strategy", "description": "Financial modeling, negotiation, organizational design, operations."},
        {"domain": "computing", "title": "Computing & Systems", "description": "AI, data engineering, eBPF infrastructure, Linux systems, kernel mechanics."},
        {"domain": "crafts", "title": "Crafts & LEGO Engineering", "description": "Precision mechanisms, pneumatics, structural integrity, gear trains."},
        {"domain": "economics", "title": "Economics & Quantitative Finance", "description": "Econometrics, game theory, macroeconomics, market design."},
        {"domain": "engineering", "title": "Physical Engineering", "description": "Robotics, aerospace, control systems, structural analysis."},
        {"domain": "formal_sciences", "title": "Formal Sciences & Mathematics", "description": "Abstract algebra, category theory, logic, computational proofs."},
        {"domain": "health_sciences", "title": "Health Sciences & Medicine", "description": "Pharmacology, neuroanatomy, genomics, emergency protocols."},
        {"domain": "humanities", "title": "Humanities & Philosophy", "description": "Epistemology, cognitive biases, rhetoric, formal debate."},
        {"domain": "languages", "title": "Linguistics & Polyglot Foundations", "description": "Phonology, syntactic parsing, natural language evolution."},
        {"domain": "motorsports", "title": "Motorsports & Vehicle Dynamics", "description": "Aerodynamics, telemetry, tire physics, suspension kinematics."},
        {"domain": "natural_sciences", "title": "Natural Sciences", "description": "Quantum mechanics, thermodynamics, molecular biology, astrophysics."}
    ]
    installed_list = list_installed_packs()
    installed_domains = {p.get("domain") for p in installed_list if isinstance(p, dict)}

    for d in domains:
        stats = get_domain_pack_info(d["domain"])
        d["lesson_count"] = stats["lesson_count"]
        d["lab_count"] = stats["lab_count"]
        d["is_installed"] = (d["domain"] in installed_domains) or (stats["lesson_count"] > 0)

    return {
        "installed": installed_list,
        "available_domains": domains
    }

@app.post("/api/packages/export")
def api_export_package(domain: str = Query(...)):
    domain = sanitize_query(domain)
    try:
        pack_path = export_topic_pack(domain)
        return FileResponse(
            path=str(pack_path),
            filename=f"{domain}.synpack",
            media_type="application/gzip"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

MAX_PACKAGE_UPLOAD_BYTES = 500 * 1024 * 1024

@app.post("/api/packages/install")
async def api_install_package(
    domain: Optional[str] = Query(None),
    file: Optional[UploadFile] = File(None)
):
    if file:
        if not file.filename.endswith(".synpack") and not file.filename.endswith(".tar.gz"):
            raise HTTPException(status_code=400, detail="Only .synpack or .tar.gz archives can be installed.")
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".synpack", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            content = await file.read(MAX_PACKAGE_UPLOAD_BYTES + 1)
            if len(content) > MAX_PACKAGE_UPLOAD_BYTES:
                tmp_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Package exceeds the 500 MB upload limit.")
            tmp_path.write_bytes(content)
        try:
            result = install_topic_pack(tmp_path)
            return result
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Installation failed: {e}")
        finally:
            tmp_path.unlink(missing_ok=True)
    elif domain:
        domain = sanitize_query(domain)
        try:
            pack_path = resolve_or_download_pack(domain)
            result = install_topic_pack(pack_path)
            return result
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Domain pack installation failed: {e}")
    else:
        raise HTTPException(status_code=400, detail="Either 'file' upload or 'domain' parameter is required.")

@app.delete("/api/packages/{domain}")
def api_uninstall_package(domain: str):
    domain = sanitize_query(domain)
    try:
        return uninstall_topic_pack(domain)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/export")
def download_export(domain: str, level: Optional[str] = None):
    try:
        domain = sanitize_query(domain)
        if level:
            level = sanitize_query(level)
        out_file = export_handbook(domain, level)
        target_path = validate_workspace_path(WORKSPACE_ROOT, out_file)
        return FileResponse(
            str(target_path),
            media_type="text/markdown",
            filename=target_path.name
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/flashcards")
def download_flashcards(query: str):
    """Anki export. Serves the topic's deck; generates one only if it has none."""
    target = resolve_subtopic(query)
    if not target:
        raise HTTPException(status_code=404, detail=f"Topic '{query}' not found")
    csv_file = target[3] / "flashcards.csv"
    if not csv_file.exists():
        try:
            csv_file = generate_flashcards(query)
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Could not generate flashcards with the AI model: {e}")
    from fastapi.responses import Response
    return Response(
        content=anki_csv_text(csv_file.read_text(encoding="utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{query.replace("/", "_")}_flashcards.csv"'},
    )

@app.get("/api/flashcards/deck")
def get_flashcards_deck(query: str):
    target = resolve_subtopic(query)
    if not target:
        raise HTTPException(status_code=404, detail=f"Topic '{query}' not found")

    domain, cat, sub, sub_path = target
    csv_file = sub_path / "flashcards.csv"
    if not csv_file.exists():
        try:
            csv_file = generate_flashcards(query)
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Could not generate flashcards with the AI model: {e}")

    import csv
    cards = []
    if csv_file.exists():
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            idx = 0
            for row in reader:
                if not row or row[0].startswith("#"):
                    continue
                front = row[0]
                back = row[1] if len(row) > 1 else ""
                tag = row[2] if len(row) > 2 else ""
                cards.append({"id": idx, "front": front, "back": back, "tag": tag})
                idx += 1

    return {"topic": sub.replace("_", " ").title(), "cards": cards}

class FlashcardReviewRequest(BaseModel):
    path: str = Field(..., max_length=500)
    interval_days: int = Field(default=1, ge=1, le=365)

@app.get("/api/flashcards/queue")
def api_flashcards_queue():
    from learning_engine.mastery import get_due_flashcard_reviews
    return {"queue": get_due_flashcard_reviews()}

@app.post("/api/flashcards/review")
def api_record_flashcard_review(req: FlashcardReviewRequest):
    from learning_engine.mastery import record_flashcard_review
    res = record_flashcard_review(req.path, interval_days=req.interval_days)
    return res

import hashlib

class TranslateRequest(BaseModel):
    # A complete multi-lesson guide can be a few hundred KB of Markdown.
    text: str = Field(..., max_length=600_000)
    target_lang: str = Field(..., pattern=r'^[a-z]{2}$')
    model: Optional[str] = None
    provider: Optional[str] = None
    host: Optional[str] = None
    stream: bool = False


class TranslateJobRequest(TranslateRequest):
    title: Optional[str] = Field(None, max_length=300)
    path: Optional[str] = Field(None, max_length=500)
    lesson_id: Optional[str] = Field(None, max_length=200)


def translation_cache_dir() -> Path:
    return WORKSPACE_ROOT / ".cache" / "translations"


TRANSLATIONS = TranslationQueue(
    get_provider=lambda **kw: get_translation_provider(**kw),
    executor=AI_EXECUTOR,
    cache_dir=translation_cache_dir,
)


@app.post("/api/translate/jobs")
async def api_translate_job_submit(req: TranslateJobRequest):
    """Queues a lesson translation, or returns it at once when cached."""
    if req.target_lang == "en" or not req.text.strip():
        return {"status": "done", "cached": True, "translated": req.text}
    cached = read_cached(translation_cache_dir(), req.text, req.target_lang)
    if cached is not None:
        return {"status": "done", "cached": True, "translated": cached}
    job = TRANSLATIONS.submit(
        req.text, req.target_lang, title=req.title or "", path=req.path, lesson_id=req.lesson_id,
        model=req.model, provider_type=req.provider, host=req.host,
    )
    return TRANSLATIONS.describe(job)


@app.get("/api/translate/jobs")
async def api_translate_jobs_list():
    return {"jobs": TRANSLATIONS.list()}


@app.get("/api/translate/jobs/{job_id}")
async def api_translate_job_get(job_id: str):
    job = TRANSLATIONS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found.")
    return TRANSLATIONS.describe(job, include_result=True)


@app.delete("/api/translate/jobs/{job_id}")
async def api_translate_job_stop(job_id: str):
    job = TRANSLATIONS.stop(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found.")
    return TRANSLATIONS.describe(job)


@app.post("/api/translate")
async def api_translate_content(req: TranslateRequest, request: Request):
    """Translates in the request (used by scripts and tests). The app uses the queue."""
    if req.target_lang == "en" or not req.text.strip():
        return {"translated": req.text, "cached": True}
    cache_dir = translation_cache_dir()
    cached = read_cached(cache_dir, req.text, req.target_lang)
    if cached is not None:
        return {"translated": cached, "cached": True}

    try:
        provider, used_model = get_translation_provider(model=req.model, provider_type=req.provider, host=req.host)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    lang_name = LANGUAGE_NAMES.get(req.target_lang, req.target_lang)
    sections = split_sections(req.text)
    total = sum(1 for s in sections if s.strip())
    sem = asyncio.Semaphore(2)
    failed = False

    async def one(section: str) -> str:
        nonlocal failed
        async with sem:
            if section.strip() and await request.is_disconnected():
                raise asyncio.CancelledError()
            text, ok, _ = await translate_section(provider, AI_EXECUTOR, section, lang_name)
            failed = failed or not ok
            return text

    def finish(parts: list) -> dict:
        final = "".join(parts).strip()
        identical = final == req.text.strip()
        if not failed and not identical and final:
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file_for(cache_dir, req.text, req.target_lang).write_text(final + "\n", encoding="utf-8")
        return {"translated": final, "cached": False, "model": used_model, "fallback": failed or identical}

    tasks = [asyncio.ensure_future(one(s)) for s in sections]
    if not req.stream:
        try:
            return finish(await asyncio.gather(*tasks))
        finally:
            for task in tasks:
                task.cancel()

    async def progress_stream():
        try:
            yield json.dumps({"progress": 0, "total": total, "model": used_model}) + "\n"
            done = 0
            for fut in asyncio.as_completed([t for t, s in zip(tasks, sections) if s.strip()]):
                await fut
                done += 1
                yield json.dumps({"progress": done, "total": total}) + "\n"
            yield json.dumps(finish([t.result() for t in tasks])) + "\n"
        finally:
            for task in tasks:
                task.cancel()

    return StreamingResponse(progress_stream(), media_type="application/x-ndjson")

# -----------------------------------------------------------------------------
# Neural Audio Narration (Edge-TTS with Guy Baritone Voice & MP3 Disk Cache)
# -----------------------------------------------------------------------------
import hashlib

AUDIO_CACHE_DIR = WORKSPACE_ROOT / "data" / "audio_cache"
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

class AudioNarrateRequest(BaseModel):
    text: str
    voice: Optional[str] = "en-US-GuyNeural"
    pitch: Optional[str] = "-10Hz"
    rate: Optional[str] = "-4%"

@app.post("/api/audio/narrate")
async def api_audio_narrate(req: AudioNarrateRequest):
    """
    Synthesizes markdown lesson text into studio-grade neural audio (MP3).
    Caches audio to disk so repeated listens are instant with 0ms latency.
    """
    raw_text = req.text.strip()
    if not raw_text:
        raise HTTPException(status_code=400, detail="Text is empty.")

    # Clean markdown for natural, human speech:
    clean = re.sub(r"```[\s\S]*?```", " Code snippet omitted. ", raw_text)
    clean = re.sub(r"`([^`]+)`", r"\1", clean)
    clean = re.sub(r"\$\$[\s\S]*?\$\$", " Mathematical formulation omitted. ", clean)
    clean = re.sub(r"\$([^$]+)\$", r"\1", clean)
    clean = re.sub(r"^#+\s*", "", clean, flags=re.MULTILINE)
    clean = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", clean)
    clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean)
    clean = re.sub(r"<!--[\s\S]*?-->", "", clean)
    clean = re.sub(r"\s+", " ", clean).strip()

    if not clean:
        raise HTTPException(status_code=400, detail="No readable text after markdown stripping.")

    # Unique cache key based on content, voice, pitch, rate
    cache_str = f"{clean}:{req.voice}:{req.pitch}:{req.rate}"
    cache_hash = hashlib.sha256(cache_str.encode("utf-8")).hexdigest()
    cache_file = AUDIO_CACHE_DIR / f"{cache_hash}.mp3"

    if cache_file.exists() and cache_file.stat().st_size > 1000:
        return FileResponse(
            str(cache_file),
            media_type="audio/mpeg",
            headers={"X-Audio-Cache": "HIT"}
        )

    try:
        import edge_tts
        communicate = edge_tts.Communicate(
            text=clean,
            voice=req.voice or "en-US-GuyNeural",
            pitch=req.pitch or "-10Hz",
            rate=req.rate or "-4%"
        )
        await communicate.save(str(cache_file))
        return FileResponse(
            str(cache_file),
            media_type="audio/mpeg",
            headers={"X-Audio-Cache": "MISS"}
        )
    except Exception as e:
        print(f"[!] Neural TTS generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Neural speech synthesis error: {e}")

@app.get("/api/topic")
async def get_topic_details(
    query: str = Query(..., description="Subtopic query e.g. 'ebpf'"),
    lesson_id: Optional[str] = Query(None, description="Optional specific lesson ID e.g. 'lesson_01_introduction'")
):
    try:
        query = sanitize_query(query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    target = resolve_subtopic(query)
    if not target:
        raise HTTPException(status_code=404, detail=f"Topic '{query}' not found")

    domain, cat, sub, sub_path = target
    persona = get_domain_persona(domain)

    labs = ""
    for fname in ["LABS.md", "labs.md"]:
        if (sub_path / fname).exists():
            labs = (sub_path / fname).read_text(encoding="utf-8")
            break

    # Multi-lesson discovery (e.g. lesson_01_*.md, lessons/*.md, or LESSON.md)
    discovered_lessons = get_unit_lessons(sub_path)

    lessons_list = []
    lesson = ""
    raw_lesson_id = lesson_id.default if hasattr(lesson_id, "default") else lesson_id
    target_lesson_id = raw_lesson_id

    # If no explicit lesson_id provided, check if query contains a 4th segment matching a lesson
    if not target_lesson_id:
        q_parts = query.split("/")
        if len(q_parts) >= 4:
            lesson_candidate = q_parts[3].lower()
            for item in discovered_lessons:
                item_id = item["id"].lower()
                if item_id == lesson_candidate or item_id == f"lesson_{lesson_candidate}" or lesson_candidate in item_id:
                    target_lesson_id = item["id"]
                    break
            if not target_lesson_id:
                cand_num = lesson_candidate.split("_")[0] if "_" in lesson_candidate else lesson_candidate
                if cand_num.isdigit():
                    prefix = f"lesson_{int(cand_num):02d}_"
                    for item in discovered_lessons:
                        if item["id"].lower().startswith(prefix):
                            target_lesson_id = item["id"]
                            break

    if discovered_lessons:
        # Default to first lesson if not specified or not found
        valid_ids = [item["id"] for item in discovered_lessons]
        if not target_lesson_id or target_lesson_id not in valid_ids:
            target_lesson_id = discovered_lessons[0]["id"]

        for item in discovered_lessons:
            content = ""
            p = Path(item["path"])
            if p.exists():
                content = p.read_text(encoding="utf-8")
            if item["id"] == target_lesson_id:
                lesson = content
            lessons_list.append({
                "id": item["id"],
                "title": item["title"],
                "filename": item["filename"],
                "content": content
            })

    # Fallback to single LESSON.md if not populated via discovered_lessons
    if not lesson:
        for fname in ["LESSON.md", "lesson.md"]:
            if (sub_path / fname).exists():
                lesson = (sub_path / fname).read_text(encoding="utf-8")
                break
        if not lesson and (sub_path / "artifacts").exists():
            artifacts = list((sub_path / "artifacts").glob("lesson_*.md"))
            if artifacts:
                lesson = artifacts[0].read_text(encoding="utf-8")

    # A lesson file named like "*summary*" doubles as the course summary.
    summary = ""
    for l_item in lessons_list:
        if "summary" in l_item["id"]:
            summary = l_item["content"]
            break

    # Load persistent chat history for this topic
    saved_chat_history = []
    history_file = sub_path / "sessions" / "chat_history.json"
    if history_file.exists():
        try:
            saved_chat_history = json.loads(history_file.read_text(encoding="utf-8"))
        except Exception:
            saved_chat_history = []

    # Preserve sequential numbered prefixes for course progression (e.g. 01 HCI Architecture)
    display_title = sub.replace('_', ' ').title()

    # Look up human-friendly titles from topic tree
    tree = get_topic_tree()
    unit_display_title = None
    course_display_title = None
    discipline_display_title = None
    domain_display_title = domain.replace("_", " ").title()

    domain_data = tree.get(domain, {})
    for disc_slug, disc_data in domain_data.get("disciplines", {}).items():
        for c_slug, c_info in disc_data.get("courses", {}).items():
            for u_slug, u_info in c_info.get("units", {}).items():
                if Path(u_info["full_path"]).resolve() == sub_path.resolve():
                    unit_display_title = u_info.get("display_name")
                    discipline_display_title = disc_slug.replace("_", " ").title()
                    if u_slug != "core":
                        course_display_title = c_info.get("display_name")
                    break

    course_final_title = None
    if course_display_title and course_display_title != unit_display_title:
        course_final_title = course_display_title
    elif "/" in cat and sub != "core":
        course_final_title = cat.split("/")[1].replace("_", " ").title()

    # Build complete continuous curriculum document
    full_sections = []

    # Quick navigation table of contents at the top of Complete Guide
    if lessons_list and len(lessons_list) > 1:
        toc_lines = ["## Course Table of Contents\n"]
        for idx, item in enumerate(lessons_list):
            toc_lines.append(f"{idx + 1}. [{item['title']}](#section-{item['id']})")
        if labs:
            toc_lines.append(f"{len(lessons_list) + 1}. [Operational Labs & Hands-on Verification](#section-labs)")
        full_sections.append("\n".join(toc_lines))

    if lessons_list:
        for idx, item in enumerate(lessons_list):
            l_content = item.get("content", "").strip()
            # If the lesson content already begins with an H1 (# ), do NOT duplicate header
            if l_content.startswith("# "):
                full_sections.append(f'<div id="section-{item["id"]}">\n\n---\n\n{l_content}\n\n</div>')
            else:
                l_title = item.get("title", f"Lesson {idx + 1}")
                full_sections.append(f'<div id="section-{item["id"]}">\n\n---\n\n# {l_title}\n\n{l_content}\n\n</div>')
    elif lesson:
        if lesson.strip().startswith("# "):
            full_sections.append(f'<div id="section-lesson">\n\n---\n\n{lesson.strip()}\n\n</div>')
        else:
            full_sections.append(f'<div id="section-lesson">\n\n---\n\n# Technical Lesson\n\n{lesson.strip()}\n\n</div>')

    if labs:
        if labs.strip().startswith("# "):
            full_sections.append(f'<div id="section-labs">\n\n---\n\n{labs.strip()}\n\n</div>')
        else:
            full_sections.append(f'<div id="section-labs">\n\n---\n\n# Operational Labs\n\n{labs.strip()}\n\n</div>')

    full_content = "\n\n".join(full_sections)

    return {
        "domain": domain,
        "domain_title": domain_display_title,
        "category": cat,
        "discipline_title": discipline_display_title or cat.split("/")[0].replace("_", " ").title(),
        "course_title": course_final_title,
        "subtopic": sub,
        "display_title": unit_display_title or display_title,
        "path": f"{domain}/{cat}/{sub}",
        "persona": persona,
        "mastery": get_subtopic_mastery(f"{domain}/{cat}/{sub}"),
        "completed_lessons": get_completed_lessons(f"{domain}/{cat}/{sub}"),
        "summary": summary,
        "chat_history": saved_chat_history,
        "lesson": lesson,
        "lessons": lessons_list,
        "active_lesson_id": target_lesson_id,
        "labs": labs,
        "full_content": full_content,
        "has_content": bool(lesson or labs or lessons_list)
    }

# Stop in the UI only aborted the browser request; the server kept drafting
# and published minutes later. Running generations can now be cancelled.
_generation_cancel: Dict[str, threading.Event] = {}
_generation_cancel_lock = threading.Lock()


class CancelGenerateRequest(BaseModel):
    query: str


@app.post("/api/generate/cancel")
def cancel_generation(req: CancelGenerateRequest):
    target = resolve_subtopic(req.query)
    key = str(target[3]) if target else req.query
    with _generation_cancel_lock:
        event = _generation_cancel.get(key)
    if event:
        event.set()
    return {"cancelled": bool(event)}


@app.post("/api/generate")
def generate_topic(req: GenerateRequest):
    target = resolve_subtopic(req.query)
    if not target:
        raise HTTPException(status_code=404, detail=f"Topic '{req.query}' not found")

    domain, cat, sub, sub_path = target
    key = str(sub_path)
    with _generation_cancel_lock:
        if key in _generation_cancel:
            raise HTTPException(status_code=409, detail="This course is already being generated.")
        stop_event = threading.Event()
        _generation_cancel[key] = stop_event
    try:
        provider = get_provider(provider_type=req.provider, model=req.model)
        results = generate_subtopic_content(
            domain=domain,
            category=cat,
            subtopic_id=sub,
            subtopic_dir=sub_path,
            provider=provider,
            force=req.force,
            should_stop=stop_event.is_set,
        )
    except GenerationStopped:
        raise HTTPException(status_code=409, detail="Generation stopped; the course was not changed.")
    finally:
        with _generation_cancel_lock:
            _generation_cancel.pop(key, None)

    return {
        "domain": domain,
        "category": cat,
        "subtopic": sub,
        "results": results,
        # Already on disk, so not generated; the UI must not call them failures.
        "skipped": sorted(getattr(results, "skipped", ())),
    }

@app.post("/api/add")
def add_topic(req: AddTopicRequest):
    try:
        path = add_subtopic(req.domain, req.category, req.subtopic, req.title)
        gen_results = {}
        if req.generate:
            provider = get_provider()
            gen_results = generate_subtopic_content(req.domain, req.category, req.subtopic, path, provider=provider)

        return {
            "success": True,
            "path": str(path.relative_to(WORKSPACE_ROOT)),
            "generated": gen_results
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class RenameTopicRequest(BaseModel):
    path: str
    new_title: str

@app.delete("/api/topic")
def api_delete_topic(path: str = Query(..., description="Relative path of topic/unit to delete")):
    success = delete_subtopic(path)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to delete topic '{path}'")
    return {"success": True, "message": f"Deleted {path}"}

@app.put("/api/topic/rename")
def api_rename_topic(req: RenameTopicRequest):
    success = rename_subtopic(req.path, req.new_title)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to rename topic '{req.path}'")
    return {"success": True, "message": f"Renamed to {req.new_title}"}

@app.post("/api/clean")
def api_clean(req: Dict[str, bool] = {}):
    """
    Cleans transient runtime artifacts.
    """
    sessions = req.get("sessions", True)
    exports = req.get("exports", True)
    mastery = req.get("mastery", False)
    caches = req.get("caches", False)
    count = perform_cleanup(clean_sessions=sessions, clean_exports=exports, clean_mastery=mastery,
                            clean_caches=caches)
    vacuumed = False
    if req.get("db", False):
        try:
            vacuum_database()
            vacuumed = True
        except sqlite3.Error as e:
            raise HTTPException(status_code=500, detail=f"Database vacuum failed: {e}")
    return {"success": True, "cleaned": count, "vacuumed": vacuumed}

@app.delete("/api/chat/session")
def api_clear_chat_session(query: Optional[str] = Query(None, description="Topic path; empty for the workspace chat")):
    """Clears one topic's saved mentor chat (the mentor window's "Clear
    conversation"). Settings → Clear chat sessions still clears every topic."""
    if query and query.strip():
        try:
            query = sanitize_query(query)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        target = resolve_subtopic(query)
        if not target:
            raise HTTPException(status_code=404, detail=f"Unknown topic '{query}'")
        sessions_dir = target[3] / "sessions"
    else:
        sessions_dir = TOPICS_DIR / ".workspace_sessions"
    removed = sessions_dir.is_dir()
    if removed:
        shutil.rmtree(sessions_dir)
    return {"success": True, "removed": removed}


def _schedule_shutdown():
    """Sends SIGTERM to this process shortly after the response is sent."""
    def _do_shutdown():
        time.sleep(0.5)
        os.kill(os.getpid(), signal.SIGTERM)

    threading.Thread(target=_do_shutdown, daemon=True).start()

@app.post("/api/system/shutdown")
def api_system_shutdown(request: Request):
    """
    Gracefully stops the Synapse server process.
    Restricted strictly to localhost clients.
    """
    client_ip = getattr(request.client, "host", "") if request.client else ""
    if client_ip not in ("127.0.0.1", "::1", "::ffff:127.0.0.1"):
        raise HTTPException(status_code=403, detail="Shutdown endpoint restricted to localhost")

    _schedule_shutdown()
    return {"message": "Server shutdown initiated", "status": "shutting_down"}

LANGUAGE_MANDATES = {
    "cs": "MANDATORY LANGUAGE DIRECTIVE: The student has selected Czech (Čeština). You MUST converse, explain concepts, and formulate all responses strictly in natural, fluent Czech. Preserve exact technical keywords, CLI flags, and code syntax, but formulate all explanations, questions, and guidance in Czech.",
    "de": "MANDATORY LANGUAGE DIRECTIVE: The student has selected German (Deutsch). You MUST converse, explain concepts, and formulate all responses strictly in natural, fluent German. Preserve exact technical keywords, CLI flags, and code syntax, but formulate all explanations, questions, and guidance in German.",
    "es": "MANDATORY LANGUAGE DIRECTIVE: The student has selected Spanish (Español). You MUST converse, explain concepts, and formulate all responses strictly in natural, fluent Spanish. Preserve exact technical keywords, CLI flags, and code syntax, but formulate all explanations, questions, and guidance in Spanish.",
    "ru": "MANDATORY LANGUAGE DIRECTIVE: The student has selected Russian (Русский). You MUST converse, explain concepts, and formulate all responses strictly in natural, fluent Russian. Preserve exact technical keywords, CLI flags, and code syntax, but formulate all explanations, questions, and guidance in Russian.",
}

def terminal_section(terminal_context: Optional[str], last_command: Optional[str]) -> List[str]:
    """The student's terminal, once, for the system instruction. It is only
    relevant when the question is about it, so the model is told to leave it
    alone otherwise (it used to be sent twice under a "you MUST inspect" rule)."""
    lines: List[str] = []
    if last_command and last_command.strip():
        lines.append(f"\n### Student's Last Executed Terminal Command: `{last_command.strip()}`")
    if terminal_context and terminal_context.strip():
        lines.extend([
            "\n### Live Student Terminal Output & Workspace Session (Commands & Results):",
            "```text",
            terminal_context.strip()[-3500:],
            "```",
        ])
    if lines:
        lines.append(
            "TERMINAL: The student has a terminal open next to the lesson. When they ask about a command they "
            "ran, an error, an exit code or other terminal output, read the terminal text and last command above, "
            "explain what happened and what to do next. When the question is not about the terminal, ignore it."
        )
    return lines


def build_chat_system_instruction(
    domain: str,
    category: str,
    subtopic: str,
    active_lesson: Optional[str] = None,
    active_lesson_title: Optional[str] = None,
    terminal_context: Optional[str] = None,
    last_command: Optional[str] = None,
    language: Optional[str] = "en"
) -> str:
    sub_title = subtopic.replace("_", " ").title()

    prompt_lines = [
        f"You are a Socratic Mentor for the course '{sub_title}' "
        f"({domain.replace('_', ' ').title()} / {category.replace('_', ' ').title()}).",
        f"The student is actively working on: '{sub_title}'.",
    ]

    lang_code = (language or "en").lower()
    if lang_code in LANGUAGE_MANDATES:
        prompt_lines.append(f"\n{LANGUAGE_MANDATES[lang_code]}")
    lesson_display = active_lesson_title or (active_lesson.replace("_", " ").title() if active_lesson else None)
    if lesson_display:
        prompt_lines.append(f"Current Lesson Displayed on Student's Screen: '{lesson_display}'.")
        prompt_lines.append("The student can see this lesson directly in the reader window. If they ask 'explain this', 'what does this mean', 'summarize this', or ask for examples or code walkthroughs, directly ground your explanation in the active lesson text provided.")

    prompt_lines.extend([
        "\n### Core Directives for Socratic Dialogue:",
        "1. RIGHT-SIZED ANSWERS: Match the length to the request. A quick conceptual question gets 2-5 sentences. When the student asks you to explain, compare, walk through code, or give a scenario or exercise, give a complete, focused answer (short paragraphs, a list or a code block; usually under 250 words). Never pad.",
        "2. SOCRATIC GUIDANCE: Lead with the most direct intuition, then, when it helps learning, ask ONE targeted question that tests or deepens understanding.",
        "3. CASUAL GREETINGS: If greeted (e.g. 'hi', 'hello'), respond warmly in 1-2 friendly sentences and ask what specific concept or intuition from the lesson they want to discuss.",
        "4. FIRST-PRINCIPLES: Use accurate technical terminology without conversational fluff.",
        "5. ACTIVE LESSON GROUNDING: First look for the answer in the active lesson excerpt. When it covers the question, base your answer on it: use its explanation, its examples and the fixes it recommends.",
        "6. ACCURACY: Do not invent commands, flags, APIs, numbers or citations. Only when the excerpt does not cover the question, say so briefly and answer from well-established knowledge; if you are unsure, say that plainly."
    ])

    prompt_lines.extend(terminal_section(terminal_context, last_command))

    return "\n".join(prompt_lines)

def build_neutral_workspace_instruction(
    terminal_context: Optional[str] = None,
    last_command: Optional[str] = None,
    language: Optional[str] = "en"
) -> str:
    lines = [
        "You are a versatile, high-signal Socratic Mentor for the Synapse Polymath Workspace.",
        "No specific curriculum topic is currently selected. The student is exploring across all 12 domains (Computing, Engineering, Formal Sciences, Natural Sciences, etc.).",
    ]

    lang_code = (language or "en").lower()
    if lang_code in LANGUAGE_MANDATES:
        lines.append(f"\n{LANGUAGE_MANDATES[lang_code]}")

    lines.extend([
        "\n### Core Directives:",
        "1. RIGHT-SIZED ANSWERS: Match the length to the request. A quick conceptual question gets 2-5 sentences. When the student asks you to explain, compare, walk through code, or give a scenario or exercise, give a complete, focused answer (short paragraphs, a list or a code block; usually under 250 words). Never pad.",
        "2. NEUTRAL & MULTIDISCIPLINARY: Answer questions across any engineering, mathematical, or scientific subject with first-principles rigor.",
        "3. TOPIC SELECTION: If the student asks what to study, guide them to pick a domain or topic from the sidebar tree.",
        "4. CASUAL GREETINGS: If greeted ('hi', 'hello'), respond warmly in 1-2 friendly sentences and ask what engineering, computing, or science subject they would like to explore or troubleshoot.",
        "5. ACCURACY: Do not invent commands, flags, APIs, numbers or citations. If you are unsure, say that plainly."
    ])
    lines.extend(terminal_section(terminal_context, last_command))
    return "\n".join(lines)

def save_chat_session(sub_path: Optional[Path], user_msg: str, tutor_reply: str, history: List[Any]):
    try:
        if sub_path:
            sessions_dir = sub_path / "sessions"
        else:
            sessions_dir = TOPICS_DIR / ".workspace_sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)

        active_session_file = sessions_dir / "active_session.md"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"\n\n**[{timestamp}] Student:**\n{user_msg}\n\n**[{timestamp}] AI Tutor:**\n{tutor_reply}\n\n---\n"
        with open(active_session_file, "a", encoding="utf-8") as f:
            f.write(entry)

        history_file = sessions_dir / "chat_history.json"
        updated_history = [
            m if isinstance(m, dict) else (m.dict() if hasattr(m, 'dict') else vars(m))
            for m in history
        ] + [
            {"role": "student", "content": user_msg},
            {"role": "tutor", "content": tutor_reply}
        ]
        history_file.write_text(json.dumps(updated_history, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[!] Auto-save error: {e}")

@app.get("/api/terminal/buffer")
def get_terminal_buffer(session_id: str = "default", lines: int = 50):
    return {
        "lines": get_terminal_lines(lines),
        "text": get_terminal_text(lines),
        "last_command": LAST_TERMINAL_COMMAND
    }

@app.post("/api/chat")
async def chat_with_tutor(req: ChatRequest):
    target = resolve_subtopic(req.query) if req.query and req.query.strip() else None

    terminal_ctx = req.terminal_context
    if not terminal_ctx or not terminal_ctx.strip():
        terminal_ctx = get_terminal_text(50)

    last_cmd = req.last_terminal_command or LAST_TERMINAL_COMMAND

    # Resolve active lesson text directly from payload or disk fallback
    lesson_text = req.lesson_content or ""
    if target:
        domain, cat, sub, sub_path = target
        if not lesson_text and sub_path:
            if req.lesson_id and req.lesson_id != "all":
                if req.lesson_id == "labs":
                    cand = sub_path / "labs.md"
                else:
                    cand = sub_path / f"{req.lesson_id}.md"
                if cand.exists():
                    lesson_text = cand.read_text(encoding="utf-8")
            if not lesson_text:
                for f in sorted(sub_path.glob("lesson_*.md")):
                    lesson_text = f.read_text(encoding="utf-8")
                    break

        system_instruction = build_chat_system_instruction(
            domain=domain,
            category=cat,
            subtopic=sub,
            active_lesson=req.lesson_id,
            active_lesson_title=req.lesson_title,
            terminal_context=terminal_ctx,
            last_command=last_cmd,
            language=req.language
        )
    else:
        sub_path = None
        system_instruction = build_neutral_workspace_instruction(
            terminal_context=terminal_ctx,
            last_command=last_cmd,
            language=req.language
        )

    try:
        provider, used_model = get_chat_provider(model=req.model, host=req.host)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to initialize AI provider for model '{req.model or 'auto'}': {e}"
        )

    conversation_text = []

    # Inject active lesson context prominently at top of prompt
    if lesson_text and lesson_text.strip():
        clean_excerpt = lesson_excerpt(lesson_text, req.message, req.section_title)

        section_label = f" - Section: '{req.section_title.replace('#', '').strip()}'" if req.section_title else ""
        conversation_text.append(
            f"[Active Lesson in Reader Window - '{req.lesson_title or req.lesson_id or 'Current Lesson'}'{section_label}]:\n```markdown\n{clean_excerpt}\n```\n(INSTRUCTION: The student is looking at this lesson right now. If they ask 'explain this' or inquire about concepts, code, or formulas, ground your explanation in this lesson text.)"
        )

    for m in req.history[-6:]:
        if isinstance(m, dict):
            r = m.get("role", "student")
            c = m.get("content", "")
        else:
            r = getattr(m, "role", "student")
            c = getattr(m, "content", "")
        if c and c.strip():
            conversation_text.append(f"{str(r).capitalize()}: {c}")

    # Avoid duplicating current message if client passed it in history
    if conversation_text and conversation_text[-1].strip() == f"Student: {req.message}".strip():
        conversation_text.pop()

    # The terminal and last command are in the system instruction (terminal_section).

    conversation_text.append(f"Student: {req.message}")
    conversation_text.append("Tutor:")

    prompt = "\n\n".join(conversation_text)

    if req.stream:
        import asyncio
        import threading

        async def stream_generator():
            q = asyncio.Queue()
            loop = asyncio.get_running_loop()

            def worker():
                try:
                    # Background translations pause while the mentor answers.
                    with interactive_ai():
                        for chunk in provider.generate_stream(prompt, system_instruction=system_instruction, max_tokens=2048):
                            loop.call_soon_threadsafe(q.put_nowait, ("chunk", chunk))
                    loop.call_soon_threadsafe(q.put_nowait, ("done", None))
                except Exception as e:
                    loop.call_soon_threadsafe(q.put_nowait, ("error", e))

            threading.Thread(target=worker, daemon=True).start()

            full_reply = []
            while True:
                msg_type, data = await q.get()
                if msg_type == "chunk":
                    full_reply.append(data)
                    yield f"data: {json.dumps({'chunk': data})}\n\n"
                elif msg_type == "done":
                    break
                elif msg_type == "error":
                    err_text = f"⚠️ Socratic Mentor stream error ({used_model}): {data}. Please verify your active model or cluster node in Settings ⚙."
                    yield f"data: {json.dumps({'chunk': err_text, 'done': True, 'full_reply': err_text, 'model': used_model})}\n\n"
                    return

            reply_text = "".join(full_reply).strip()
            save_chat_session(sub_path, req.message, reply_text, req.history)
            yield f"data: {json.dumps({'done': True, 'full_reply': reply_text, 'model': used_model})}\n\n"

        # The mentor may answer with a fallback model; tell the UI which one.
        return StreamingResponse(stream_generator(), media_type="text/event-stream",
                                 headers={"X-Synapse-Model": used_model})

    try:
        with interactive_ai():
            response_text = provider.generate(prompt, system_instruction=system_instruction)
        reply = response_text.strip()
    except Exception as gen_err:
        reply = f"⚠️ Socratic Mentor error ({used_model}): {gen_err}. Please verify your cluster node in Settings ⚙."

    save_chat_session(sub_path, req.message, reply, req.history)

    return {
        "reply": reply,
        "model": used_model
    }

class QuizRequest(BaseModel):
    query: str
    provider: Optional[str] = None
    model: Optional[str] = None
    host: Optional[str] = None

class SaveSessionRequest(BaseModel):
    query: str
    history: List[ChatMessage]

@app.post("/api/quiz")
def generate_quiz(req: QuizRequest):
    target = resolve_subtopic(req.query)
    if not target:
        raise HTTPException(status_code=404, detail=f"Topic '{req.query}' not found")

    domain, cat, sub, sub_path = target
    persona = get_domain_persona(domain)

    context_parts = []
    for l in get_unit_lessons(sub_path)[:4]:
        p = Path(l["path"])
        if p.exists():
            context_parts.append(p.read_text(encoding="utf-8")[:2000])

    labs_path = sub_path / "labs.md"
    if labs_path.exists():
        context_parts.append(labs_path.read_text(encoding="utf-8")[:2000])

    system_instruction = persona + "\nYou are an expert examiner. Generate challenging scenario-based multiple-choice quiz questions to test deep intuition and operational mechanics."
    prompt = f"""Based on the curriculum for '{sub.replace('_', ' ').title()}', generate 3 scenario-based multiple choice questions.
Return strictly a valid JSON array of 3 objects with this exact structure:
[
  {{
    "id": 1,
    "question": "Scenario: ...",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correctIndex": 0,
    "explanation": "Why this option is correct based on first principles."
  }}
]

Curriculum Context:
{"".join(context_parts)}

Output valid JSON only with no markdown backticks or commentary."""

    provider = get_provider(provider_type=req.provider, model=req.model, host=req.host, domain=domain)
    try:
        raw = provider.generate(prompt, system_instruction=system_instruction) or ""
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"The AI model could not write the quiz ({e}). Check Settings → AI models.")
    questions = parse_quiz_questions(raw)
    if not questions:
        # This used to return a canned question ("what is the primary
        # architectural trade-off?") with made-up options, shown as if it
        # were the course quiz.
        raise HTTPException(status_code=502, detail="The AI model did not return usable quiz questions. Try again or pick another model in Settings → AI models.")
    return {"questions": questions}


def parse_quiz_questions(raw: str) -> List[Dict[str, Any]]:
    """The model's reply as quiz questions; malformed questions are dropped."""
    data = json_object_list(raw)
    questions = []
    for item in data:
        question, options, correct = item.get("question"), item.get("options"), item.get("correctIndex")
        if not (isinstance(question, str) and question.strip()):
            continue
        if not (isinstance(options, list) and len(options) >= 2 and all(isinstance(o, str) and o.strip() for o in options)):
            continue
        if isinstance(correct, bool) or not isinstance(correct, int) or not 0 <= correct < len(options):
            continue
        questions.append({
            "id": len(questions) + 1,
            "question": question.strip(),
            "options": options,
            "correctIndex": correct,
            "explanation": str(item.get("explanation") or ""),
        })
    return questions

@app.post("/api/session/save")
def save_session(req: SaveSessionRequest):
    target = resolve_subtopic(req.query)
    if not target:
        raise HTTPException(status_code=404, detail=f"Topic '{req.query}' not found")

    domain, cat, sub, sub_path = target
    sessions_dir = sub_path / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    filename = f"{timestamp}_socratic_session.md"
    file_path = sessions_dir / filename

    content_lines = [
        f"# Socratic Study Session: {sub.replace('_', ' ').title()}",
        f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Domain:** `{domain}` | **Category:** `{cat}`\n",
        "## Dialogue Log\n"
    ]

    for msg in req.history:
        role = "Student (You)" if msg.role == "student" else "AI Tutor"
        content_lines.append(f"### {role}\n{msg.content}\n")

    file_path.write_text("\n".join(content_lines), encoding="utf-8")

    return {
        "success": True,
        "filename": filename,
        "path": str(file_path.relative_to(WORKSPACE_ROOT))
    }

# -----------------------------------------------------------------------------
# WebSocket Interactive Terminal (PTY Bridge)
# -----------------------------------------------------------------------------

def sandbox_tool_search_path() -> str:
    """PATH for finding docker/kubectl. Apps started from the Dock get a minimal
    PATH, and Rancher Desktop installs its tools in ~/.rd/bin."""
    extra = [str(Path.home() / ".rd" / "bin"), "/opt/homebrew/bin", "/usr/local/bin",
             "/Applications/Docker.app/Contents/Resources/bin"]
    current = os.environ.get("PATH", "")
    parts = current.split(os.pathsep) if current else []
    return os.pathsep.join(parts + [p for p in extra if p not in parts])


def find_sandbox_tool(name: str) -> Optional[str]:
    return shutil.which(name, path=sandbox_tool_search_path())


def sandbox_tool_responds(cmd: list) -> bool:
    """True if the daemon/cluster behind the tool answers (5 s budget: a
    starting Rancher VM is slow)."""
    import subprocess
    env = {**os.environ, "PATH": sandbox_tool_search_path()}
    try:
        return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              timeout=5, env=env).returncode == 0
    except Exception:
        return False


def _sandbox_unavailable(title: str, steps: list[str]) -> list[str]:
    """A terminal that explains why the sandbox is unavailable and opens no
    shell. Falling back to a host shell here meant the panel said "Sandbox"
    while commands (and lesson Run buttons) ran on the real machine."""
    yellow, red, green, reset = "\033[1;33m", "\033[1;31m", "\033[1;32m", "\033[0m"
    lines = [
        f"{yellow}[!] {title}{reset}",
        "",
        *steps,
        "",
        f"{red}No shell was opened: commands here would have run on this computer, not in a sandbox.{reset}",
        f'{green}[i] Start the sandbox and reconnect, or choose "Host Shell (Local)" to work on this computer on purpose.{reset}',
    ]
    # Lines go in as arguments (no shell quoting); the panel stays open without
    # a shell, so typed input goes nowhere.
    script = 'printf "%s\\n" "$@"; stty -echo 2>/dev/null; exec tail -f /dev/null'
    return ["/bin/sh", "-c", script, "synapse-sandbox-unavailable", *lines]


async def terminal_command(env_type: str, host_cmd: list[str]) -> list[str]:
    """The process to run in the terminal PTY for the selected profile."""
    if env_type == "docker":
        docker_bin = find_sandbox_tool("docker")
        if docker_bin and await asyncio.to_thread(sandbox_tool_responds, [docker_bin, "info"]):
            return [
                docker_bin, "run", "-it", "--rm",
                "-v", f"{WORKSPACE_ROOT}:/workspace",
                "-w", "/workspace",
                "ubuntu:24.04", "/bin/bash",
            ]
        return _sandbox_unavailable(
            "Linux Sandbox: the Docker daemon (Rancher Desktop / Docker) is not running or not reachable.",
            [
                "\033[1;36mSetup on macOS:\033[0m",
                "  1. Start Rancher Desktop (or install it: brew install --cask rancher)",
                "  2. Rancher Desktop -> Preferences -> Container Engine: dockerd (moby)",
                "  3. Check it in a terminal: docker info",
            ],
        )
    if env_type == "k8s":
        kubectl_bin = find_sandbox_tool("kubectl")
        if kubectl_bin and await asyncio.to_thread(sandbox_tool_responds, [kubectl_bin, "cluster-info"]):
            return [
                kubectl_bin, "run", f"synapse-lab-{os.getpid()}",
                "-it", "--rm", "--restart=Never",
                "--image=nicolaka/netshoot",
                "--namespace=default", "--", "bash",
            ]
        return _sandbox_unavailable(
            "Kubernetes Pod: the cluster (k3s / Rancher Desktop) is not reachable.",
            [
                "\033[1;36mSetup on macOS:\033[0m",
                "  1. Rancher Desktop -> Preferences -> Kubernetes: Enable Kubernetes",
                "  2. Wait until the cluster is Running",
                "  3. Check it in a terminal: kubectl get nodes",
            ],
        )
    return host_cmd


@app.websocket("/ws/terminal")
async def terminal_websocket(websocket: WebSocket):
    global LAST_TERMINAL_COMMAND
    # Browsers do not apply CORS to WebSockets: reject cross-site origins
    # (cross-site WebSocket hijacking) and non-local hosts on open instances.
    ws_host = websocket.headers.get("host")
    if not is_allowed_origin(websocket.headers.get("origin"), ws_host):
        await websocket.close(code=1008, reason="Origin not allowed")
        return
    if not is_auth_enabled() and not is_allowed_host(ws_host):
        await websocket.close(code=1008, reason="Host not allowed")
        return

    # Browsers cannot set headers on WebSockets, so authenticate with a
    # one-time ticket from POST /api/auth/ws-ticket instead of the bearer token.
    if is_auth_enabled() and not consume_ws_ticket(websocket.query_params.get("ticket")):
        # Accept, then close with 1008: a close before accept reaches the browser
        # as a bare HTTP 403 (close code 1006), which the terminal treats as a
        # network error and retries forever. Nothing is sent before the close.
        # (Bad origins/hosts above are still refused without accepting.)
        await websocket.accept()
        await websocket.close(code=1008, reason="Authentication required")
        return

    await websocket.accept()

    env_type = websocket.query_params.get("env", "host")

    # Determine default terminal working directory (user's home directory by default)
    term_cwd = Path.home()
    if not term_cwd.exists():
        term_cwd = WORKSPACE_ROOT

    pty_available = HAS_POSIX_PTY
    master = -1
    slave = -1

    if HAS_POSIX_PTY and sys.platform != "win32":
        try:
            master, slave = pty.openpty()
            # Default terminal size (80 cols, 24 rows)
            winsize = struct.pack("HHHH", 24, 80, 0, 0)
            fcntl.ioctl(slave, termios.TIOCSWINSZ, winsize)

            try:
                attrs = termios.tcgetattr(slave)
                attrs[0] |= termios.ICRNL
                termios.tcsetattr(slave, termios.TCSANOW, attrs)
            except Exception:
                pass
        except OSError:
            pty_available = False

    if sys.platform == "win32":
        try:
            from winpty import PtyProcess
            shell = os.environ.get("COMSPEC", "cmd.exe")
            proc = PtyProcess.spawn([shell], cwd=str(term_cwd), dimensions=(24, 80))
            notice = "\r\n\x1b[1;32m[i] Connected to Synapse Windows ConPTY Shell\x1b[0m\r\n"
            await websocket.send_text(notice)

            async def winpty_read_loop():
                try:
                    while proc.isalive():
                        data = await asyncio.to_thread(proc.read, 1024)
                        if data:
                            b_data = data.encode("utf-8", errors="replace")
                            append_terminal_bytes(b_data)
                            await websocket.send_bytes(b_data)
                        else:
                            await asyncio.sleep(0.01)
                except Exception:
                    pass

            pipe_task = asyncio.create_task(winpty_read_loop())
            try:
                while True:
                    msg = await websocket.receive()
                    if "text" in msg and msg["text"]:
                        text = msg["text"]
                        if text.startswith("{") and "cols" in text:
                            try:
                                dim = json.loads(text)
                                proc.set_winsize(dim.get("rows", 24), dim.get("cols", 80))
                            except Exception:
                                pass
                            continue
                        proc.write(text)
                    elif "bytes" in msg and msg["bytes"]:
                        proc.write(msg["bytes"].decode("utf-8", errors="replace"))
            except WebSocketDisconnect:
                pass
            finally:
                pipe_task.cancel()
                try:
                    proc.close()
                except Exception:
                    pass
            return
        except Exception as winpty_err:
            print(f"[!] WinPTY unavailable or failed: {winpty_err}. Using fallback pipe bridge.")

    # Resilient Pipe Bridge Fallback if host kern.tty.ptmx_max limit is reached or on Windows
    if not pty_available or sys.platform == "win32":
        if sys.platform == "win32":
            shell = os.environ.get("COMSPEC", "cmd.exe")
            args = ["/K", "chcp 65001"]
        else:
            shell = "/bin/bash" if os.path.exists("/bin/bash") else "/bin/sh"
            args = ["-i"]

        proc = await asyncio.create_subprocess_exec(
            shell, *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(term_cwd),
            env=os.environ.copy()
        )
        notice = "\r\n\x1b[1;32m[i] Connected to Synapse Interactive Shell (Cross-Platform Pipe Mode)\x1b[0m\r\n"
        await websocket.send_text(notice)

        async def pipe_read_loop():
            try:
                while True:
                    data = await proc.stdout.read(1024)
                    if not data:
                        break
                    append_terminal_bytes(data)
                    await websocket.send_bytes(data)
            except Exception:
                pass

        pipe_task = asyncio.create_task(pipe_read_loop())
        input_buffer: List[str] = []
        try:
            while True:
                msg = await websocket.receive()
                raw_text = ""
                if "text" in msg and msg["text"]:
                    raw_text = msg["text"]
                elif "bytes" in msg and msg["bytes"]:
                    raw_text = msg["bytes"].decode("utf-8", errors="replace")

                if not raw_text:
                    continue

                if raw_text.startswith("{") and "cols" in raw_text:
                    continue

                # Filter out raw terminal escape sequences in pipe mode to avoid cursor displacement
                if raw_text.startswith("\x1b"):
                    continue

                # Normalize CRLF and CR to LF so Enter triggers cleanly once
                normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n")

                for ch in normalized:
                    if ch == "\n":
                        cmd_line = "".join(input_buffer)
                        input_buffer.clear()
                        if cmd_line.strip():
                            LAST_TERMINAL_COMMAND = cmd_line.strip()

                        await websocket.send_text("\r\n")
                        eol = b"\r\n" if sys.platform == "win32" else b"\n"
                        proc.stdin.write(cmd_line.encode("utf-8") + eol)
                        await proc.stdin.drain()
                    elif ch in ("\x7f", "\x08", "\b"):  # Backspace key (ASCII 127 DEL, ASCII 8 BS)
                        if input_buffer:
                            input_buffer.pop()
                            # In VT100/ANSI/xterm: \b moves left, space clears character, \b moves left again
                            await websocket.send_text("\b \b")
                    elif ch == "\x03":  # Ctrl+C
                        input_buffer.clear()
                        await websocket.send_text("^C\r\n")
                        try:
                            if sys.platform != "win32":
                                proc.send_signal(signal.SIGINT)
                            else:
                                proc.stdin.write(b"\x03\r\n")
                                await proc.stdin.drain()
                        except Exception:
                            pass
                    elif ch == "\x15":  # Ctrl+U (clear line)
                        if input_buffer:
                            await websocket.send_text("\b \b" * len(input_buffer))
                            input_buffer.clear()
                    elif ord(ch) >= 32 or ch == "\t":
                        input_buffer.append(ch)
                        await websocket.send_text(ch)
        except WebSocketDisconnect:
            pass
        finally:
            pipe_task.cancel()
            try:
                proc.terminate()
            except Exception:
                pass
        return

    cache_dir = WORKSPACE_ROOT / ".cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    zdot_dir = cache_dir / "zsh"
    zdot_dir.mkdir(exist_ok=True)
    zshrc_path = zdot_dir / ".zshrc"
    zshrc_path.write_text(
        'if [ -f "/etc/zprofile" ]; then source "/etc/zprofile"; fi\n'
        'if [ -f "$HOME/.zprofile" ]; then source "$HOME/.zprofile"; fi\n'
        'if [ -f "$HOME/.zshenv" ]; then source "$HOME/.zshenv"; fi\n'
        'if [ -f "$HOME/.zshrc" ]; then source "$HOME/.zshrc"; fi\n'
        'export PROMPT_EOL_MARK=""\n'
        'unsetopt PROMPT_SP 2>/dev/null\n'
        'setopt interactivecomments\n'
        'export LANG="${LANG:-en_US.UTF-8}"\n'
        'export LC_ALL="${LC_ALL:-en_US.UTF-8}"\n'
        'alias ps="ps -ww"\n'
        'alias rm="rm -i"\n'
        'alias cp="cp -i"\n'
        'alias mv="mv -i"\n',
        encoding="utf-8"
    )

    bashrc_path = cache_dir / "bashrc"
    bashrc_path.write_text(
        'if [ -f "/etc/profile" ]; then source "/etc/profile"; fi\n'
        'if [ -f "$HOME/.bash_profile" ]; then source "$HOME/.bash_profile"; elif [ -f "$HOME/.profile" ]; then source "$HOME/.profile"; fi\n'
        'if [ -f "$HOME/.bashrc" ]; then source "$HOME/.bashrc"; fi\n'
        'export LANG="${LANG:-en_US.UTF-8}"\n'
        'export LC_ALL="${LC_ALL:-en_US.UTF-8}"\n'
        'alias ps="ps -ww"\n'
        'alias rm="rm -i"\n'
        'alias cp="cp -i"\n'
        'alias mv="mv -i"\n'
        'shopt -s checkwinsize 2>/dev/null\n',
        encoding="utf-8"
    )

    shell = os.environ.get("SHELL", "/bin/zsh" if os.path.exists("/bin/zsh") else "/bin/bash")
    if "bash" in shell:
        exec_cmd = [shell, "--rcfile", str(bashrc_path), "-i"]
    else:
        exec_cmd = [shell, "-i"]

    exec_cmd = await terminal_command(env_type, exec_cmd)

    pid = os.fork()

    if pid == 0:
        # Child process
        os.close(master)
        os.setsid()
        fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
        os.dup2(slave, 0)
        os.dup2(slave, 1)
        os.dup2(slave, 2)
        os.close(slave)

        os.chdir(str(term_cwd))
        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        env["LANG"] = env.get("LANG") or "en_US.UTF-8"
        env["LC_ALL"] = env.get("LC_ALL") or "en_US.UTF-8"
        if sys.platform == "darwin":
            default_paths = ["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin", "/usr/sbin", "/sbin"]
            current_path = env.get("PATH", "")
            missing = [p for p in default_paths if p not in current_path]
            if missing:
                env["PATH"] = ":".join(missing) + (":" + current_path if current_path else "")
        if env_type in ("docker", "k8s"):
            env["PATH"] = sandbox_tool_search_path() if not env.get("PATH") else os.pathsep.join(
                [env["PATH"]] + [p for p in sandbox_tool_search_path().split(os.pathsep) if p not in env["PATH"].split(os.pathsep)])
        env["ZDOTDIR"] = str(zdot_dir)
        env["PROMPT_COMMAND"] = ""
        env["PAGER"] = "cat"
        os.execvpe(exec_cmd[0], exec_cmd, env)

    # Parent process. Forget the fd after closing it: the number is soon reused
    # by another socket, and closing it again on disconnect would kill that one.
    os.close(slave)
    slave = -1

    # Set non-blocking on master
    flags = fcntl.fcntl(master, fcntl.F_GETFL)
    fcntl.fcntl(master, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    loop = asyncio.get_event_loop()

    async def pty_read_loop():
        try:
            while True:
                await asyncio.sleep(0.01)
                r, _, _ = select.select([master], [], [], 0)
                if master in r:
                    try:
                        data = os.read(master, 4096)
                        if data:
                            append_terminal_bytes(data)
                            await websocket.send_bytes(data)
                        else:
                            break
                    except (BlockingIOError, OSError):
                        pass
        except Exception:
            pass

    read_task = asyncio.create_task(pty_read_loop())

    input_line_buffer = ""
    pending_dangerous_cmd = None
    confirm_buffer = ""
    current_cols = 80
    current_rows = 24

    try:
        while True:
            msg = await websocket.receive()
            raw_bytes = None
            if "bytes" in msg and msg["bytes"]:
                raw_bytes = msg["bytes"]
            elif "text" in msg and msg["text"]:
                text = msg["text"]
                # Check for resize event
                if text.startswith("{") and "cols" in text:
                    try:
                        evt = json.loads(text)
                        if evt.get("type") == "resize":
                            cols = evt.get("cols", 80)
                            rows = evt.get("rows", 24)
                            if cols != current_cols or rows != current_rows:
                                current_cols = cols
                                current_rows = rows
                                new_size = struct.pack("HHHH", rows, cols, 0, 0)
                                fcntl.ioctl(master, termios.TIOCSWINSZ, new_size)
                                try:
                                    os.killpg(os.getpgid(pid), signal.SIGWINCH)
                                except Exception:
                                    pass
                            continue
                    except Exception:
                        pass
                raw_bytes = text.encode("utf-8")

            if not raw_bytes:
                continue

            # Host safety verification guard
            if env_type == "host":
                # If awaiting confirmation for a blocked dangerous command
                if pending_dangerous_cmd:
                    handled = False
                    for b in raw_bytes:
                        if b in (13, 10):  # Enter
                            handled = True
                            if confirm_buffer.strip().upper() == "CONFIRM":
                                await websocket.send_text("\r\n\x1b[1;32m[CONFIRMED - Executing on host]\x1b[0m\r\n")
                                os.write(master, pending_dangerous_cmd.encode("utf-8") + b"\r")
                            else:
                                await websocket.send_text("\r\n\x1b[1;32m[CANCELLED - Destructive command blocked]\x1b[0m\r\n")
                                os.write(master, b"\x03")
                            pending_dangerous_cmd = None
                            confirm_buffer = ""
                            input_line_buffer = ""
                        elif b == 3:  # Ctrl+C
                            handled = True
                            await websocket.send_text("\r\n\x1b[1;32m[CANCELLED]\x1b[0m\r\n")
                            os.write(master, b"\x03")
                            pending_dangerous_cmd = None
                            confirm_buffer = ""
                            input_line_buffer = ""
                        elif b in (8, 127):  # Backspace
                            if confirm_buffer:
                                confirm_buffer = confirm_buffer[:-1]
                                await websocket.send_text("\b \b")
                        elif 32 <= b <= 126:
                            ch = chr(b)
                            confirm_buffer += ch
                            await websocket.send_text(ch)
                    if handled or pending_dangerous_cmd:
                        continue

                # Normal typing: track line buffer and inspect on Enter
                intercept_enter = False
                for b in raw_bytes:
                    if b in (13, 10):  # Enter key
                        cmd_executed = input_line_buffer.strip()
                        if cmd_executed:
                            LAST_TERMINAL_COMMAND = cmd_executed
                        if is_dangerous_host_command(input_line_buffer):
                            intercept_enter = True
                            pending_dangerous_cmd = input_line_buffer
                            confirm_buffer = ""
                            warning = (
                                "\r\n\r\n"
                                "\x1b[1;41;37m DANGER \x1b[0m \x1b[1;31m[SYNAPSE HOST SAFETY GUARD]\x1b[0m\r\n"
                                f"\x1b[1;33mBlocked destructive command on host OS:\x1b[0m \x1b[1;37m{pending_dangerous_cmd}\x1b[0m\r\n"
                                "\x1b[1;36mThis operation can permanently destroy host system files or your workspace.\x1b[0m\r\n"
                                "\x1b[1;33mTo run anyway, type \x1b[1;32mCONFIRM\x1b[1;33m and press Enter. To cancel, press Enter or Ctrl+C: \x1b[0m"
                            )
                            await websocket.send_text(warning)
                        input_line_buffer = ""
                    elif b in (8, 127):  # Backspace
                        input_line_buffer = input_line_buffer[:-1]
                    elif b in (3, 21):  # Ctrl+C, Ctrl+U
                        input_line_buffer = ""
                    elif 32 <= b <= 126:
                        input_line_buffer += chr(b)

                if intercept_enter:
                    continue

            if b"\r" in raw_bytes and b"\n" not in raw_bytes:
                raw_bytes = raw_bytes.replace(b"\r", b"\n")

            try:
                os.write(master, raw_bytes)
            except OSError:
                break
    except (WebSocketDisconnect, Exception) as e:
        if "WebSocketDisconnect" in type(e).__name__:
            pass
        else:
            print(f"TERMINAL WS EXCEPTION: {type(e)}: {e}", flush=True)
    finally:
        read_task.cancel()
        try:
            if master != -1:
                os.close(master)
        except Exception:
            pass
        try:
            if slave != -1:
                os.close(slave)
        except Exception:
            pass
        try:
            if pid > 0:
                os.kill(pid, 9)
                os.waitpid(pid, 0)
        except Exception:
            pass

# -----------------------------------------------------------------------------
# Static SPA Mounting (if frontend is built)
# -----------------------------------------------------------------------------
from fastapi.staticfiles import StaticFiles

def resolve_dist_dir() -> Optional[Path]:
    # 1. Electron packaged resources (authoritative in production desktop shell)
    env_res = os.environ.get("SYNAPSE_RESOURCES_PATH")
    if env_res:
        electron_dist = Path(env_res) / "frontend" / "dist"
        if electron_dist.exists() and (electron_dist / "index.html").exists():
            return electron_dist

    # 2. PyInstaller frozen onefile mode
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        p = Path(sys._MEIPASS) / "app" / "frontend" / "dist"
        if p.exists() and (p / "index.html").exists():
            return p

    # 3. Bundled in site-packages/app/frontend/dist (e.g. Windows embedded Python sidecar)
    app_pkg_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if app_pkg_dist.exists() and (app_pkg_dist / "index.html").exists():
        return app_pkg_dist

    # 4. Fallback relative to executable, workspace root, or cwd
    candidates = [
        Path(sys.executable).resolve().parent.parent / "frontend" / "dist",
        WORKSPACE_ROOT / "app" / "frontend" / "dist",
        Path.cwd() / "app" / "frontend" / "dist",
    ]
    for c in candidates:
        if c and c.exists() and (c / "index.html").exists():
            return c
    return None

DIST_DIR = resolve_dist_dir()

@app.get("/")
def get_spa_root():
    dist = resolve_dist_dir()
    if dist and (dist / "index.html").exists():
        from fastapi.responses import FileResponse
        return FileResponse(
            str(dist / "index.html"),
            media_type="text/html",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            }
        )
    return {"detail": "Synapse Workbench Backend Online. Initializing frontend assets..."}

if DIST_DIR and DIST_DIR.exists():
    if (DIST_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")
    app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True), name="static")
