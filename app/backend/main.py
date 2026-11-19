"""
Learning Workbench Backend API
Provides REST APIs for topics/curricula, AI persona chat, and a WebSocket PTY terminal.
"""

import sys
import os
import select
import struct
import signal
import asyncio
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

import threading
from collections import deque
from typing import Dict, List, Optional, Any

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
    get_unit_lessons
)
from learning_engine.utils import perform_cleanup
from learning_engine.generator import generate_subtopic_content
from learning_engine.models import (
    get_provider,
    get_chat_provider,
    OllamaProvider,
    OllamaCluster,
    get_configured_hosts,
    save_configured_hosts,
    CLUSTER_HOST_SPECS
)
from learning_engine.search import search_curriculum
from learning_engine.graph import get_prerequisite_graph, get_topic_dependencies
from learning_engine.database import get_connection
from learning_engine.mastery import (
    set_subtopic_mastery,
    get_mastery_summary,
    get_subtopic_mastery,
    get_completed_lessons,
    toggle_lesson_completion
)
from learning_engine.security import validate_workspace_path, sanitize_query, is_dangerous_host_command
from learning_engine.config_manager import get_settings, save_settings
from learning_engine.exporter import export_handbook
from learning_engine.flashcards import generate_flashcards
from learning_engine.summary import regenerate_summary, generate_initial_summary
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
    is_auth_enabled,
    verify_password,
    generate_auth_token,
    verify_auth_token,
    is_rate_limited,
    record_failed_attempt,
    reset_failed_attempts
)

app = FastAPI(title="AI Learning Workbench Backend", version="1.1.1")

@app.on_event("startup")
def startup_event():
    try:
        seed_starter_curriculum()
    except Exception as e:
        print(f"[!] Startup curriculum seed note: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if is_auth_enabled() and path.startswith("/api/"):
        # Public endpoints that don't require authorization
        if path in ["/api/auth/status", "/api/auth/login", "/api/health"]:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        if not token:
            token = request.headers.get("X-Synapse-Token")
        if not token:
            token = request.query_params.get("token")

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
    terminal_context: Optional[str] = Field(None, max_length=50000)
    last_terminal_command: Optional[str] = Field(None, max_length=1000)
    lesson_content: Optional[str] = Field(None, max_length=50000)
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
    domain: str = Field(..., pattern=r'^[a-z0-9_-]+$')
    category: str = Field(..., pattern=r'^[a-z0-9_/-]+$')
    subtopic: str = Field(..., pattern=r'^[a-z0-9_-]+$')
    force: bool = False

class TranslateRequest(BaseModel):
    text: str = Field(..., max_length=50000)
    target_lang: str = Field(..., pattern=r'^[a-z]{2}$')

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
    if not token:
        token = request.query_params.get("token")

    auth_required = is_auth_enabled()
    authenticated = verify_auth_token(token) if auth_required else True
    return {
        "auth_required": auth_required,
        "authenticated": authenticated
    }

@app.post("/api/auth/login")
def api_login(req: LoginRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
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

@app.get("/api/health")
def get_health():
    return {"status": "ok", "app": "synapse-backend"}

@app.get("/api/status")
def get_status():
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

@app.get("/api/tree")
def get_tree():
    return get_topic_tree()

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
        return {"connected": True}
        
    # 2. Check if cluster has any node online if no specific model/host match
    cluster = OllamaCluster()
    status = cluster.get_cluster_status()
    if any(d.get("online") for d in status.values()):
        return {"connected": True, "warning": "Specified host/model unreachable, but cluster has other active nodes."}
        
    return {"connected": False, "error": "Unable to connect to Ollama/LocalAI cluster."}

@app.get("/api/settings/cluster-status")
def api_cluster_status():
    import time
    from learning_engine.models import get_node_pin
    hosts = get_configured_hosts()
    results = {}
    for h in hosts:
        start = time.time()
        up = OllamaProvider.is_available(h)
        elapsed_ms = int((time.time() - start) * 1000)
        models = OllamaProvider.list_models(h) if up else []
        pin = get_node_pin(h)
        results[h] = {
            "online": up,
            "latency_ms": elapsed_ms if up else None,
            "models": models,
            "pinned_model": pin
        }
    return results

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
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "gemini-2.5-flash",
        "gemini-2.5-pro"
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
    return {"results": search_curriculum(q)}

@app.get("/api/graph")
def api_graph():
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
    topics = {row["path"]: {"state": row["state"], "completed_lessons": json.loads(row["completed_lessons"])} for row in rows}
    
    return {
        "summary": get_mastery_summary(),
        "topics": topics
    }

@app.post("/api/mastery")
def update_mastery(req: MasteryUpdateRequest):
    return set_subtopic_mastery(req.path, req.state)

@app.post("/api/mastery/lesson")
def update_lesson_mastery(req: LessonMasteryRequest):
    return toggle_lesson_completion(req.path, req.lesson_id, req.completed)

@app.get("/api/settings")
def get_app_settings():
    return get_settings()

@app.post("/api/settings")
def update_app_settings(settings: Dict[str, Any]):
    save_settings(settings)
    return {"status": "success"}

@app.get("/api/packages")
def api_list_packages():
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
            content = await file.read()
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
    try:
        csv_file = generate_flashcards(query)
        return FileResponse(
            str(csv_file),
            media_type="text/csv",
            filename=f"{query.replace('/', '_')}_flashcards.csv"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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
        except Exception:
            pass

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

import hashlib

class TranslateRequest(BaseModel):
    text: str
    target_lang: str
    model: Optional[str] = None

LANGUAGE_NAMES = {
    "cs": "Czech (Čeština)",
    "de": "German (Deutsch)",
    "es": "Spanish (Español)",
    "ru": "Russian (Русский)",
    "en": "English"
}

@app.post("/api/translate")
async def api_translate_content(req: TranslateRequest):
    if req.target_lang == "en" or not req.text.strip():
        return {"translated": req.text, "cached": True}

    lang_name = LANGUAGE_NAMES.get(req.target_lang, req.target_lang)

    cache_dir = WORKSPACE_ROOT / ".cache" / "translations"
    cache_dir.mkdir(parents=True, exist_ok=True)
    text_hash = hashlib.sha256((req.text + req.target_lang).encode("utf-8")).hexdigest()
    cache_file = cache_dir / f"{text_hash}_{req.target_lang}.md"

    if cache_file.exists():
        return {"translated": cache_file.read_text(encoding="utf-8"), "cached": True}

    prompt = f"""You are an expert technical translator and polyglot philologist.
Translate the following technical curriculum text into {lang_name}.

CRITICAL INVARIANTS:
1. DO NOT translate or modify code blocks (```...```). Keep all code, manifests, and CLI commands 100% identical.
2. DO NOT translate or modify KaTeX math equations ($...$ and $$...$$). Keep all mathematical notation 100% identical.
3. DO NOT translate Mermaid diagrams (```mermaid...```).
4. Translate all technical explanations and narrative prose with high fidelity and natural grammatical precision.
5. Output clean Markdown only with no preamble or wrapping.

Text to translate:
\"\"\"
{req.text}
\"\"\""""

    try:
        import asyncio
        provider, used_model = get_chat_provider(model=req.model)
        translated_text = await asyncio.to_thread(provider.generate, prompt)
        translated_text = translated_text.strip()
        cache_file.write_text(translated_text + "\n", encoding="utf-8")
        return {"translated": translated_text, "cached": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
def get_topic_details(
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
            if (target_dir / fname).exists():
                lesson = (target_dir / fname).read_text(encoding="utf-8")
                break
            elif (sub_path / fname).exists():
                lesson = (sub_path / fname).read_text(encoding="utf-8")
                break
        if not lesson and (sub_path / "artifacts").exists():
            artifacts = list((sub_path / "artifacts").glob("lesson_*.md"))
            if artifacts:
                lesson = artifacts[0].read_text(encoding="utf-8")

    # Load summary non-blocking
    summary = ""
    for fname in ["SUMMARY.md", "summary.md"]:
        summary_file = sub_path / fname
        if summary_file.exists():
            summary = summary_file.read_text(encoding="utf-8")
            break
    if not summary:
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
        "path": str(sub_path.relative_to(WORKSPACE_ROOT)),
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

@app.post("/api/generate")
def generate_topic(req: GenerateRequest):
    target = resolve_subtopic(req.query)
    if not target:
        raise HTTPException(status_code=404, detail=f"Topic '{req.query}' not found")

    domain, cat, sub, sub_path = target
    provider = get_provider(provider_type=req.provider, model=req.model)

    results = generate_subtopic_content(
        domain=domain,
        category=cat,
        subtopic_id=sub,
        subtopic_dir=sub_path,
        provider=provider,
        force=req.force
    )

    return {
        "domain": domain,
        "category": cat,
        "subtopic": sub,
        "results": results
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
    count = perform_cleanup(clean_sessions=sessions, clean_exports=exports, clean_mastery=mastery)
    return {"success": True, "cleaned": count}

LANGUAGE_MANDATES = {
    "cs": "MANDATORY LANGUAGE DIRECTIVE: The student has selected Czech (Čeština). You MUST converse, explain concepts, and formulate all responses strictly in natural, fluent Czech. Preserve exact technical keywords, CLI flags, and code syntax, but formulate all explanations, questions, and guidance in Czech.",
    "de": "MANDATORY LANGUAGE DIRECTIVE: The student has selected German (Deutsch). You MUST converse, explain concepts, and formulate all responses strictly in natural, fluent German. Preserve exact technical keywords, CLI flags, and code syntax, but formulate all explanations, questions, and guidance in German.",
    "es": "MANDATORY LANGUAGE DIRECTIVE: The student has selected Spanish (Español). You MUST converse, explain concepts, and formulate all responses strictly in natural, fluent Spanish. Preserve exact technical keywords, CLI flags, and code syntax, but formulate all explanations, questions, and guidance in Spanish.",
    "ru": "MANDATORY LANGUAGE DIRECTIVE: The student has selected Russian (Русский). You MUST converse, explain concepts, and formulate all responses strictly in natural, fluent Russian. Preserve exact technical keywords, CLI flags, and code syntax, but formulate all explanations, questions, and guidance in Russian.",
}

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
    domain_titles = {
        "computing": "Systems Software, Kernel Architecture & Distributed Systems",
        "formal_sciences": "Pure Mathematics, Formal Logic & Discrete Structures",
        "natural_sciences": "Physics, Chemistry & Foundations of Science",
        "engineering": "Robotics, Electronics & Embedded Hardware",
        "crafts": "Engineering Mechanisms, CAD & Digital Prototyping",
        "arts": "Music Theory, Composition & Audio DSP",
        "business": "Economics, System Dynamics & Strategic Decision Making",
        "humanities": "Cognitive Science, Epistemology & Socratic Philosophy",
    }
    specialty = domain_titles.get(domain, domain.replace("_", " ").title())
    sub_title = subtopic.replace("_", " ").title()

    prompt_lines = [
        f"You are a concise, high-signal Socratic Mentor specializing in {specialty}.",
        f"The student is actively working on: '{sub_title}' (Discipline: {category}).",
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
        "1. ULTRA-CONCISE: Limit answers strictly to 2-4 sentences max. Never lecture or dump long text.",
        "2. SOCRATIC GUIDANCE: Provide the single most direct intuition immediately, then follow with ONE targeted question to test or deepen their understanding.",
        "3. CASUAL GREETINGS: If greeted (e.g. 'hi', 'hello'), respond warmly in 1-2 friendly sentences and ask what specific concept or intuition from the lesson they want to discuss.",
        "4. FIRST-PRINCIPLES: Use accurate technical terminology without conversational fluff.",
        "5. ACTIVE LESSON GROUNDING: Always refer to the specific definitions, formulas, or architecture presented in the active lesson on screen."
    ])

    if last_command and last_command.strip():
        prompt_lines.append(f"\n### Student's Last Executed Terminal Command: `{last_command.strip()}`")

    if terminal_context and terminal_context.strip():
        prompt_lines.extend([
            "\n### Live Student Terminal Output & Workspace Session (Commands & Results):",
            "```text",
            terminal_context.strip()[-3500:],
            "```",
            "CRITICAL TERMINAL DIRECTIVE: The student has an integrated terminal open in their workspace. If the student asks about what they typed, a command they ran (such as their last command noted above), an error, exit code, or terminal output, you MUST directly inspect the terminal text and last command above, identify the command/output, explain it clearly, and guide them on what to do next with first-principles clarity."
        ])

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
        "1. ULTRA-CONCISE: Limit answers strictly to 2-4 sentences max. Never lecture or dump long text.",
        "2. NEUTRAL & MULTIDISCIPLINARY: Answer questions across any engineering, mathematical, or scientific subject with first-principles rigor.",
        "3. TOPIC SELECTION: If the student asks what to study, guide them to pick a domain or topic from the sidebar tree.",
        "4. CASUAL GREETINGS: If greeted ('hi', 'hello'), respond warmly in 1-2 friendly sentences and ask what engineering, computing, or science subject they would like to explore or troubleshoot."
    ])
    if last_command and last_command.strip():
        lines.append(f"\n### Student's Last Executed Terminal Command: `{last_command.strip()}`")

    if terminal_context and terminal_context.strip():
        lines.extend([
            "\n### Live Student Terminal Output & Workspace Session (Commands & Results):",
            "```text",
            terminal_context.strip()[-3500:],
            "```",
            "CRITICAL TERMINAL DIRECTIVE: The student has an integrated terminal open in their workspace. If the student asks about what they typed, a command they ran (such as their last command noted above), an error, exit code, or terminal output, you MUST directly inspect the terminal text and last command above, identify the command/output, explain it clearly, and guide them on what to do next with first-principles clarity."
        ])
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
        clean_excerpt = lesson_text.strip()[:8000]
        conversation_text.append(
            f"[Active Lesson in Reader Window - '{req.lesson_title or req.lesson_id or 'Current Lesson'}']:\n```markdown\n{clean_excerpt}\n```\n(INSTRUCTION: The student is looking at this lesson right now. If they ask 'explain this' or inquire about concepts, code, or formulas, ground your explanation in this lesson text.)"
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

    # Inject last command and terminal buffer directly into prompt so LLM sees it immediately
    if last_cmd and last_cmd.strip():
        conversation_text.append(
            f"[Student's Most Recent Terminal Command]: `{last_cmd.strip()}`"
        )
    if terminal_ctx and terminal_ctx.strip():
        conversation_text.append(
            f"[Live Student Terminal Session]:\n```text\n{terminal_ctx.strip()[-3000:]}\n```\n(The student's terminal session shows their recent commands and output above. If the student refers to what they typed or command results, reference this block directly.)"
        )

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
                    for chunk in provider.generate_stream(prompt, system_instruction=system_instruction, max_tokens=250):
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

        return StreamingResponse(stream_generator(), media_type="text/event-stream")

    try:
        response_text = provider.generate(prompt, system_instruction=system_instruction)
        reply = response_text.strip()
    except Exception as gen_err:
        reply = f"⚠️ Socratic Mentor error ({used_model}): {gen_err}. Please verify your cluster node in Settings ⚙."

    save_chat_session(sub_path, req.message, reply, req.history)

    return {
        "reply": reply,
        "model": used_model
    }

class SummaryRequest(BaseModel):
    query: str
    provider: Optional[str] = None
    model: Optional[str] = None

@app.post("/api/summary/regenerate")
def api_regenerate_summary(req: SummaryRequest):
    new_summary = regenerate_summary(req.query, provider_type=req.provider, model=req.model)
    return {"summary": new_summary}

class QuizRequest(BaseModel):
    query: str
    provider: Optional[str] = None
    model: Optional[str] = None

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

    provider = get_provider(provider_type=req.provider, model=req.model)
    raw = provider.generate(prompt, system_instruction=system_instruction).strip()

    # Clean markdown code block if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        quiz_data = json.loads(raw)
        return {"questions": quiz_data}
    except Exception:
        # Fallback structured question
        return {
            "questions": [
                {
                    "id": 1,
                    "question": f"In {sub.replace('_', ' ').title()}, what is the primary architectural trade-off?",
                    "options": [
                        "Latency vs. throughput optimization",
                        "Consistency vs. availability",
                        "Memory footprint vs. cache coherence",
                        "Control plane overhead vs. fault isolation"
                    ],
                    "correctIndex": 0,
                    "explanation": "Systems optimization requires balancing critical resource constraints."
                }
            ]
        }

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

    # Git commit and push
    try:
        import subprocess
        subprocess.run(["git", "add", str(file_path)], check=True, cwd=str(WORKSPACE_ROOT), capture_output=True)
        subprocess.run(["git", "commit", "-m", f"session({sub}): save tutor study log for {timestamp}"], check=True, cwd=str(WORKSPACE_ROOT), capture_output=True)
        subprocess.run(["git", "push", "origin", "main"], check=False, cwd=str(WORKSPACE_ROOT), capture_output=True)
    except Exception:
        pass

    return {
        "success": True,
        "filename": filename,
        "path": str(file_path.relative_to(WORKSPACE_ROOT))
    }

@app.post("/api/artifacts/compile")
def compile_artifacts(req: QuizRequest):
    target = resolve_subtopic(req.query)
    if not target:
        raise HTTPException(status_code=404, detail=f"Topic '{req.query}' not found")

    domain, cat, sub, sub_path = target
    artifacts_dir = sub_path / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    persona = get_domain_persona(domain)
    sessions_dir = sub_path / "sessions"
    session_texts = []
    if sessions_dir.exists():
        for sfile in sessions_dir.glob("*.md"):
            session_texts.append(sfile.read_text(encoding="utf-8")[:2000])

    prompt = f"""Synthesize all learning sessions, core theorems, and operational best practices for '{sub.replace('_', ' ').title()}' into an exhaustive Mastered Field Reference Guide.

Structure:
# Mastered Field Guide: {sub.replace('_', ' ').title()}
## 1. Executive Summary & Core Invariants
## 2. Essential Architecture & Cheatsheet
## 3. High-Value Production Snippets / Formulas
## 4. Troubleshooting Playbook & Critical Pitfalls

Sessions History:
{"".join(session_texts) if session_texts else "No prior session logs."}

Output clean, production-ready Markdown."""

    provider = get_provider(provider_type=req.provider, model=req.model)
    compiled_guide = provider.generate(prompt, system_instruction=persona)

    output_file = artifacts_dir / "MASTERED_GUIDE.md"
    output_file.write_text(compiled_guide.strip() + "\n", encoding="utf-8")

    # Git commit and push
    try:
        import subprocess
        subprocess.run(["git", "add", str(output_file)], check=True, cwd=str(WORKSPACE_ROOT), capture_output=True)
        subprocess.run(["git", "commit", "-m", f"artifacts({sub}): compile mastered field guide"], check=True, cwd=str(WORKSPACE_ROOT), capture_output=True)
        subprocess.run(["git", "push", "origin", "main"], check=False, cwd=str(WORKSPACE_ROOT), capture_output=True)
    except Exception:
        pass

    return {
        "success": True,
        "path": str(output_file.relative_to(WORKSPACE_ROOT))
    }

# -----------------------------------------------------------------------------
# WebSocket Interactive Terminal (PTY Bridge)
# -----------------------------------------------------------------------------

@app.websocket("/ws/terminal")
async def terminal_websocket(websocket: WebSocket):
    global LAST_TERMINAL_COMMAND
    token = websocket.query_params.get("token")
    if is_auth_enabled() and not verify_auth_token(token):
        await websocket.close(code=1008, reason="Authentication required")
        return

    await websocket.accept()

    env_type = websocket.query_params.get("env", "host")

    pty_available = HAS_POSIX_PTY
    master = -1
    slave = -1
    if HAS_POSIX_PTY:
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

    # Resilient Pipe Bridge Fallback if host kern.tty.ptmx_max limit is reached or on Windows
    if not pty_available:
        if sys.platform == "win32":
            shell = os.environ.get("COMSPEC", "powershell.exe")
            args = []
        else:
            shell = "/bin/bash" if os.path.exists("/bin/bash") else "/bin/sh"
            args = ["-i"]

        proc = await asyncio.create_subprocess_exec(
            shell, *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(WORKSPACE_ROOT),
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
        try:
            while True:
                msg = await websocket.receive()
                if "bytes" in msg and msg["bytes"]:
                    proc.stdin.write(msg["bytes"])
                    await proc.stdin.drain()
                elif "text" in msg and msg["text"]:
                    text = msg["text"]
                    if text.startswith("{") and "cols" in text:
                        continue
                    proc.stdin.write(text.encode("utf-8"))
                    await proc.stdin.drain()
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
        'if [ -f "$HOME/.zshrc" ]; then source "$HOME/.zshrc"; fi\n'
        'export PROMPT_EOL_MARK=""\n'
        'unsetopt PROMPT_SP 2>/dev/null\n'
        'alias ps="ps -ww"\n'
        'alias rm="rm -i"\n'
        'alias cp="cp -i"\n'
        'alias mv="mv -i"\n',
        encoding="utf-8"
    )

    bashrc_path = cache_dir / "bashrc"
    bashrc_path.write_text(
        'if [ -f "$HOME/.bashrc" ]; then source "$HOME/.bashrc"; fi\n'
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

    if env_type == "docker":
        docker_bin = shutil.which("docker")
        docker_ok = False
        if docker_bin:
            try:
                import subprocess
                p = subprocess.run([docker_bin, "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.5)
                if p.returncode == 0:
                    docker_ok = True
            except Exception:
                docker_ok = False

        if docker_ok:
            exec_cmd = [
                docker_bin, "run", "-it", "--rm",
                "--privileged",
                "-v", f"{WORKSPACE_ROOT}:/workspace",
                "-w", "/workspace",
                "ubuntu:24.04", "/bin/bash"
            ]
        else:
            notice = (
                'echo -e "\\033[1;33m[!] Rancher Desktop / Docker daemon is not running or socket is unreachable.\\033[0m\\n" && '
                'echo -e "\\033[1;36mRancher Desktop Setup Instructions for macOS:\\033[0m" && '
                'echo -e "  1. Start Rancher Desktop (or install via: brew install --cask rancher)" && '
                'echo -e "  2. In Rancher Preferences -> Container Engine, select dockerd (moby)" && '
                'echo -e "  3. Verify connection in your terminal: docker info\\n" && '
                'echo -e "\\033[1;32m[i] Active in Local Host Shell (/bin/bash)...\\033[0m\\n" && '
                'exec /bin/bash'
            )
            exec_cmd = ["/bin/bash", "-c", notice]

    elif env_type == "k8s":
        kubectl_bin = shutil.which("kubectl")
        k8s_ok = False
        if kubectl_bin:
            try:
                import subprocess
                p = subprocess.run([kubectl_bin, "cluster-info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.5)
                if p.returncode == 0:
                    k8s_ok = True
            except Exception:
                k8s_ok = False

        if k8s_ok:
            exec_cmd = [
                kubectl_bin, "run", f"synapse-lab-{os.getpid()}",
                "-it", "--rm", "--restart=Never",
                "--image=nicolaka/netshoot",
                "--namespace=default", "--", "bash"
            ]
        else:
            notice = (
                'echo -e "\\033[1;33m[!] Kubernetes cluster (k3s / Rancher Desktop) is not reachable.\\033[0m\\n" && '
                'echo -e "\\033[1;36mk3s Cluster Setup Instructions for macOS:\\033[0m" && '
                'echo -e "  1. In Rancher Desktop -> Preferences -> Kubernetes, check [Enable Kubernetes]" && '
                'echo -e "  2. Wait for k3s cluster to reach Running status" && '
                'echo -e "  3. Verify cluster nodes: kubectl get nodes\\n" && '
                'echo -e "\\033[1;32m[i] Active in Local Host Shell (/bin/bash)...\\033[0m\\n" && '
                'exec /bin/bash'
            )
            exec_cmd = ["/bin/bash", "-c", notice]

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

        os.chdir(str(WORKSPACE_ROOT))
        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        env["ZDOTDIR"] = str(zdot_dir)
        env["PROMPT_COMMAND"] = ""
        env["PAGER"] = "cat"
        os.execvpe(exec_cmd[0], exec_cmd, env)

    # Parent process
    os.close(slave)

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
    # 1. PyInstaller frozen onefile mode
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        p = Path(sys._MEIPASS) / "app" / "frontend" / "dist"
        if p.exists():
            return p

    # 2. Bundled in site-packages/app/frontend/dist (e.g. Windows embedded Python sidecar)
    app_pkg_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if app_pkg_dist.exists():
        return app_pkg_dist

    # 3. Electron resources path or development workspace root
    env_res = os.environ.get("SYNAPSE_RESOURCES_PATH")
    candidates = [
        Path(env_res) / "frontend" / "dist" if env_res else None,
        Path(sys.executable).resolve().parent.parent / "frontend" / "dist",
        WORKSPACE_ROOT / "app" / "frontend" / "dist",
        Path.cwd() / "app" / "frontend" / "dist",
    ]
    for c in candidates:
        if c and c.exists():
            return c
    return None

DIST_DIR = resolve_dist_dir()

@app.get("/")
def get_spa_root():
    dist = resolve_dist_dir()
    if dist and (dist / "index.html").exists():
        from fastapi.responses import FileResponse
        return FileResponse(str(dist / "index.html"), media_type="text/html")
    return {"detail": "Synapse Workbench Backend Online. Initializing frontend assets..."}

if DIST_DIR and DIST_DIR.exists():
    if (DIST_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")
    app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True), name="static")
