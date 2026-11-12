"""
Learning Workbench Backend API
Provides REST APIs for topics/curricula, AI persona chat, and a WebSocket PTY terminal.
"""

import sys
import os
import pty
import select
import struct
import fcntl
import termios
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

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

import threading
from collections import deque
from typing import Dict, List, Optional, Any

ANSI_ESCAPE_RE = re.compile(r'\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

class TerminalRingBuffer:
    MAX_LINE_LENGTH: int = 10_000

    def __init__(self, max_lines: int = 150):
        self.buffer: deque[str] = deque(maxlen=max_lines)
        self._lock = threading.Lock()

    def append_text(self, raw_bytes: bytes):
        with self._lock:
            try:
                text = raw_bytes.decode("utf-8", errors="replace")
                clean = ANSI_ESCAPE_RE.sub("", text)
                for line in clean.splitlines():
                    stripped = line.strip()
                    if stripped:
                        if len(stripped) > self.MAX_LINE_LENGTH:
                            stripped = stripped[:self.MAX_LINE_LENGTH] + "... [TRUNCATED]"
                        self.buffer.append(stripped)
            except Exception as e:
                # Log error silently to avoid breaking PTY flow
                pass

    def get_recent_lines(self, count: int = 50) -> List[str]:
        with self._lock:
            return list(self.buffer)[-count:]

    def get_recent_text(self, count: int = 50) -> str:
        with self._lock:
            return "\n".join(list(self.buffer)[-count:])

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, TerminalRingBuffer] = {}
        self._lock = threading.Lock()

    def get_buffer(self, session_id: str) -> TerminalRingBuffer:
        with self._lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = TerminalRingBuffer()
            return self.sessions[session_id]

# Global Session Manager
SESSION_MANAGER = SessionManager()

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from learning_engine.topic_manager import (
    get_topic_tree,
    get_domain_persona,
    resolve_subtopic,
    add_subtopic,
    delete_subtopic,
    rename_subtopic,
    get_unit_lessons,
    TOPICS_DIR
)
from learning_engine.generator import generate_subtopic_content
from learning_engine.models import (
    get_provider,
    get_chat_provider,
    OllamaProvider,
    OllamaCluster,
    get_configured_hosts,
    save_configured_hosts
)
from learning_engine.search import search_curriculum
from learning_engine.graph import get_prerequisite_graph, get_topic_dependencies
from learning_engine.mastery import (
    set_subtopic_mastery,
    load_mastery_data,
    get_mastery_summary,
    get_subtopic_mastery,
    get_completed_lessons,
    toggle_lesson_completion
)
from learning_engine.security import validate_workspace_path, sanitize_query
from learning_engine.config_manager import get_settings, save_settings
from learning_engine.exporter import export_handbook
from learning_engine.flashcards import generate_flashcards
from learning_engine.summary import regenerate_summary, generate_initial_summary

app = FastAPI(title="AI Learning Workbench Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Data Models
# -----------------------------------------------------------------------------

class AddTopicRequest(BaseModel):
    domain: str
    category: str
    subtopic: str
    title: Optional[str] = None
    generate: bool = True

class GenerateRequest(BaseModel):
    query: str
    provider: Optional[str] = None
    model: Optional[str] = None
    force: bool = False

class ChatMessage(BaseModel):
    role: str
    content: str

from pydantic import BaseModel, Field, validator
import re

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=0, max_length=500)
    message: str = Field(..., min_length=1, max_length=10000)
    history: List[Any] = []
    lesson_id: Optional[str] = Field(None, pattern=r'^[a-z0-9_-]*$')
    terminal_context: Optional[str] = Field(None, max_length=50000)
    lesson_content: Optional[str] = Field(None, max_length=50000)
    stream: Optional[bool] = False
    provider: Optional[str] = None
    model: Optional[str] = None

    @validator('query')
    def validate_query(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9_/.-]*$', v):
            raise ValueError('Invalid characters in query')
        if ".." in v:
            raise ValueError('Path traversal detected')
        return v

class GenerateRequest(BaseModel):
    domain: str = Field(..., pattern=r'^[a-z0-9_-]+$')
    category: str = Field(..., pattern=r'^[a-z0-9_/-]+$')
    subtopic: str = Field(..., pattern=r'^[a-z0-9_-]+$')
    level: str = Field(default='beginner', pattern=r'^(beginner|intermediate|advanced)$')
    force: bool = False

class TranslateRequest(BaseModel):
    text: str = Field(..., max_length=50000)
    target_lang: str = Field(..., pattern=r'^[a-z]{2}$')

# ... update chat_with_tutor to use GenerateRequest and ChatRequest ...

# -----------------------------------------------------------------------------
# REST Endpoints
# -----------------------------------------------------------------------------

@app.get("/api/status")
def get_status():
    tree = get_topic_tree()
    total_domains = len(tree)
    total_categories = 0
    total_subtopics = 0
    with_foundation = 0
    with_lesson = 0
    with_labs = 0
    complete = 0

    for domain, ddata in tree.items():
        total_categories += len(ddata["categories"])
        for cat, cdata in ddata["categories"].items():
            total_subtopics += len(cdata)
            for sub, sdata in cdata.items():
                st = sdata["status"]
                if st["has_foundation"]: with_foundation += 1
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
        "foundation_count": with_foundation,
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

@app.get("/api/settings/cluster-status")
def api_cluster_status():
    import time
    hosts = get_configured_hosts()
    results = {}
    for h in hosts:
        start = time.time()
        up = OllamaProvider.is_available(h)
        elapsed_ms = int((time.time() - start) * 1000)
        models = OllamaProvider.list_models(h) if up else []
        results[h] = {
            "online": up,
            "latency_ms": elapsed_ms if up else None,
            "models": models
        }
    return results

class ClusterHostsRequest(BaseModel):
    hosts: List[str]

@app.get("/api/settings/cluster")
def api_get_cluster_hosts():
    return {"hosts": get_configured_hosts()}

@app.post("/api/settings/cluster")
def api_set_cluster_hosts(req: ClusterHostsRequest):
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
    return {
        "summary": get_mastery_summary(),
        "topics": load_mastery_data()
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
def api_translate_content(req: TranslateRequest):
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
        provider = get_provider(model=req.model)
        translated_text = provider.generate(prompt).strip()
        cache_file.write_text(translated_text + "\n", encoding="utf-8")
        return {"translated": translated_text, "cached": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/topic")
def get_topic_details(
    query: str = Query(..., description="Subtopic query e.g. 'ebpf'"),
    level: Optional[str] = Query("beginner", description="Difficulty level: beginner, intermediate, advanced"),
    lesson_id: Optional[str] = Query(None, description="Optional specific lesson ID e.g. 'lesson_01_introduction'")
):
    try:
        query = sanitize_query(query)
        if level:
            level = sanitize_query(level)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    target = resolve_subtopic(query)
    if not target:
        raise HTTPException(status_code=404, detail=f"Topic '{query}' not found")

    domain, cat, sub, sub_path = target
    persona = get_domain_persona(domain)

    # Check available levels
    available_levels = []
    for lvl in ["beginner", "intermediate", "advanced"]:
        if (sub_path / lvl).exists() and any((sub_path / lvl).glob("*.md")):
            available_levels.append(lvl)

    # Handle direct function invocations in tests where default is QueryInfo
    raw_level = level.default if hasattr(level, "default") else level
    selected_level = (raw_level or "beginner").lower()
    target_dir = sub_path / selected_level if (sub_path / selected_level).exists() else sub_path

    foundation = ""
    labs = ""

    for fname in ["FOUNDATION.md", "foundation.md"]:
        if (target_dir / fname).exists():
            foundation = (target_dir / fname).read_text(encoding="utf-8")
            break
        elif (sub_path / fname).exists():
            foundation = (sub_path / fname).read_text(encoding="utf-8")
            break

    for fname in ["LABS.md", "labs.md"]:
        if (target_dir / fname).exists():
            labs = (target_dir / fname).read_text(encoding="utf-8")
            break
        elif (sub_path / fname).exists():
            labs = (sub_path / fname).read_text(encoding="utf-8")
            break

    # Multi-lesson discovery (e.g. lesson_01_*.md, lessons/*.md, or LESSON.md)
    discovered_lessons = get_unit_lessons(target_dir)
    if not discovered_lessons and target_dir != sub_path:
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
        "level": selected_level,
        "available_levels": available_levels,
        "mastery": get_subtopic_mastery(f"{domain}/{cat}/{sub}"),
        "completed_lessons": get_completed_lessons(f"{domain}/{cat}/{sub}"),
        "summary": summary,
        "chat_history": saved_chat_history,
        "foundation": foundation,
        "lesson": lesson,
        "lessons": lessons_list,
        "active_lesson_id": target_lesson_id,
        "labs": labs,
        "full_content": full_content,
        "has_content": bool(foundation or lesson or labs or lessons_list)
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

def build_chat_system_instruction(
    domain: str,
    category: str,
    subtopic: str,
    active_lesson: Optional[str] = None,
    terminal_context: Optional[str] = None
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
    if active_lesson:
        clean_lesson = active_lesson.replace("_", " ").title()
        prompt_lines.append(f"Current Lesson Focus: '{clean_lesson}'.")

    prompt_lines.extend([
        "\n### Core Directives for Socratic Dialogue:",
        "1. ULTRA-CONCISE: Limit answers strictly to 2-4 sentences max. Never lecture or dump long text.",
        "2. SOCRATIC GUIDANCE: Provide the single most direct intuition immediately, then follow with ONE targeted question to test or deepen their understanding.",
        "3. CASUAL GREETINGS: If greeted (e.g. 'hi', 'hello'), respond warmly in 1-2 friendly sentences and ask what specific concept or intuition from the lesson they want to discuss.",
        "4. FIRST-PRINCIPLES: Use accurate technical terminology without conversational fluff.",
    ])

    if terminal_context and terminal_context.strip():
        prompt_lines.extend([
            "\n### Live Student Terminal Output (Recent Commands / Error Logs):",
            "```text",
            terminal_context.strip()[-2500:],
            "```",
            "INSTRUCTION: The student ran commands in their workspace terminal. If they ask about an error or command failure, directly diagnose the root cause from the terminal output above and state the fix concisely in 1-3 sentences."
        ])

    return "\n".join(prompt_lines)

def build_neutral_workspace_instruction(terminal_context: Optional[str] = None) -> str:
    lines = [
        "You are a versatile, high-signal Socratic Mentor for the Synapse Polymath Workspace.",
        "No specific curriculum topic is currently selected. The student is exploring across all 12 domains (Computing, Engineering, Formal Sciences, Natural Sciences, etc.).",
        "\n### Core Directives:",
        "1. ULTRA-CONCISE: Limit answers strictly to 2-4 sentences max. Never lecture or dump long text.",
        "2. NEUTRAL & MULTIDISCIPLINARY: Answer questions across any engineering, mathematical, or scientific subject with first-principles rigor.",
        "3. TOPIC SELECTION: If the student asks what to study, guide them to pick a domain or topic from the sidebar tree.",
        "4. CASUAL GREETINGS: If greeted ('hi', 'hello'), respond warmly in 1-2 friendly sentences and ask what engineering, computing, or science subject they would like to explore or troubleshoot."
    ]
    if terminal_context and terminal_context.strip():
        lines.extend([
            "\n### Live Student Terminal Output (Recent Commands / Error Logs):",
            "```text",
            terminal_context.strip()[-2500:],
            "```",
            "INSTRUCTION: The student ran commands in their workspace terminal. If they ask about an error or command output, directly diagnose the root cause from the terminal output above and state the fix concisely in 1-3 sentences."
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
        updated_history = [m.dict() if hasattr(m, 'dict') else m for m in history] + [
            {"role": "student", "content": user_msg},
            {"role": "tutor", "content": tutor_reply}
        ]
        history_file.write_text(json.dumps(updated_history, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[!] Auto-save error: {e}")

@app.get("/api/terminal/buffer")
def get_terminal_buffer(session_id: str = "default", lines: int = 50):
    buffer = SESSION_MANAGER.get_buffer(session_id)
    return {
        "lines": buffer.get_recent_lines(lines),
        "text": buffer.get_recent_text(lines)
    }

@app.post("/api/chat")
async def chat_with_tutor(req: ChatRequest):
    target = resolve_subtopic(req.query) if req.query and req.query.strip() else None

    terminal_ctx = req.terminal_context
    if not terminal_ctx or not terminal_ctx.strip():
        terminal_ctx = SESSION_MANAGER.get_buffer("default").get_recent_text(50)

    if target:
        domain, cat, sub, sub_path = target
        system_instruction = build_chat_system_instruction(
            domain=domain,
            category=cat,
            subtopic=sub,
            active_lesson=req.lesson_id,
            terminal_context=terminal_ctx
        )
    else:
        sub_path = None
        system_instruction = build_neutral_workspace_instruction(terminal_context=terminal_ctx)

    provider, used_model = get_chat_provider(model=req.model)

    conversation_text = []
    for m in req.history[-6:]:
        conversation_text.append(f"{m.role.capitalize()}: {m.content}")

    # Inject terminal buffer directly into prompt so LLM sees it immediately
    if terminal_ctx and terminal_ctx.strip():
        conversation_text.append(
            f"[Live Terminal Buffer Context]:\n```text\n{terminal_ctx.strip()[-2000:]}\n```"
        )
    
    # Inject active lesson context if provided
    if req.lesson_content and req.lesson_content.strip():
        with open("/Users/radovan.varga/.gemini/tmp/synapse/debug.log", "a") as f:
            f.write(f"[DEBUG] Received lesson content length: {len(req.lesson_content)}\n")
        conversation_text.append(
            f"[Active Curriculum Context]:\n```markdown\n{req.lesson_content.strip()[-5000:]}\n```"
        )
    else:
        with open("/Users/radovan.varga/.gemini/tmp/synapse/debug.log", "a") as f:
            f.write("[DEBUG] No lesson content received in ChatRequest\n")

    conversation_text.append(f"Student: {req.message}")
    conversation_text.append("Tutor:")

    prompt = "\n\n".join(conversation_text)

    if req.stream:
        async def stream_generator():
            full_reply = []
            for chunk in provider.generate_stream(prompt, system_instruction=system_instruction, max_tokens=250):
                full_reply.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"

            reply_text = "".join(full_reply).strip()
            save_chat_session(sub_path, req.message, reply_text, req.history)
            yield f"data: {json.dumps({'done': True, 'full_reply': reply_text, 'model': used_model})}\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")

    response_text = provider.generate(prompt, system_instruction=system_instruction)
    reply = response_text.strip()
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
    if (sub_path / "FOUNDATION.md").exists():
        context_parts.append((sub_path / "FOUNDATION.md").read_text(encoding="utf-8")[:3000])

    for l in get_unit_lessons(sub_path)[:4]:
        p = Path(l["path"])
        if p.exists():
            context_parts.append(p.read_text(encoding="utf-8")[:2000])

    if (sub_path / "LABS.md").exists():
        context_parts.append((sub_path / "LABS.md").read_text(encoding="utf-8")[:2000])

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
    await websocket.accept()

    env_type = websocket.query_params.get("env", "host")

    master, slave = pty.openpty()
    # Default terminal size (80 cols, 24 rows)
    winsize = struct.pack("HHHH", 24, 80, 0, 0)
    fcntl.ioctl(slave, termios.TIOCSWINSZ, winsize)

    cache_dir = WORKSPACE_ROOT / ".cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    zdot_dir = cache_dir / "zsh"
    zdot_dir.mkdir(exist_ok=True)
    zshrc_path = zdot_dir / ".zshrc"
    zshrc_path.write_text(
        'if [ -f "$HOME/.zshrc" ]; then source "$HOME/.zshrc"; fi\n'
        'alias ps="ps -ww"\n',
        encoding="utf-8"
    )

    bashrc_path = cache_dir / "bashrc"
    bashrc_path.write_text(
        'if [ -f "$HOME/.bashrc" ]; then source "$HOME/.bashrc"; fi\n'
        'alias ps="ps -ww"\n'
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
        session_id = str(id(websocket))
        buffer = SESSION_MANAGER.get_buffer(session_id)
        try:
            while True:
                await asyncio.sleep(0.01)
                r, _, _ = select.select([master], [], [], 0)
                if master in r:
                    try:
                        data = os.read(master, 4096)
                        if data:
                            buffer.append_text(data)
                            await websocket.send_bytes(data)
                        else:
                            break
                    except (BlockingIOError, OSError):
                        pass
        except Exception:
            pass

    read_task = asyncio.create_task(pty_read_loop())

    try:
        while True:
            msg = await websocket.receive()
            if "bytes" in msg and msg["bytes"]:
                os.write(master, msg["bytes"])
            elif "text" in msg and msg["text"]:
                text = msg["text"]
                # Check for resize event
                if text.startswith("{") and "cols" in text:
                    try:
                        evt = json.loads(text)
                        if evt.get("type") == "resize":
                            cols = evt.get("cols", 80)
                            rows = evt.get("rows", 24)
                            new_size = struct.pack("HHHH", rows, cols, 0, 0)
                            fcntl.ioctl(master, termios.TIOCSWINSZ, new_size)
                            try:
                                os.killpg(os.getpgid(pid), signal.SIGWINCH)
                            except Exception:
                                pass
                            continue
                    except Exception:
                        pass
                os.write(master, text.encode("utf-8"))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        read_task.cancel()
        try:
            os.close(master)
            os.kill(pid, 9)
            os.waitpid(pid, 0)
        except Exception:
            pass

# -----------------------------------------------------------------------------
# Static SPA Mounting (if frontend is built)
# -----------------------------------------------------------------------------
from fastapi.staticfiles import StaticFiles

DIST_DIR = WORKSPACE_ROOT / "app/frontend/dist"
if DIST_DIR.exists():
    app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True), name="static")
