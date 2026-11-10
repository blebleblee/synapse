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
import asyncio
import json
import datetime
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from learning_engine.topic_manager import (
    get_topic_tree,
    get_domain_persona,
    resolve_subtopic,
    add_subtopic,
    TOPICS_DIR
)
from learning_engine.generator import generate_subtopic_content
from learning_engine.models import get_provider, OllamaProvider
from learning_engine.search import search_curriculum
from learning_engine.graph import get_prerequisite_graph
from learning_engine.mastery import set_subtopic_mastery, load_mastery_data, get_mastery_summary, get_subtopic_mastery
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

class ChatRequest(BaseModel):
    query: str
    message: str
    history: List[ChatMessage] = []
    provider: Optional[str] = None
    model: Optional[str] = None

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

    ollama_up = OllamaProvider.is_available()
    ollama_models = OllamaProvider.list_models() if ollama_up else []

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

@app.get("/api/search")
def api_search(q: str = Query(..., min_length=2)):
    return {"results": search_curriculum(q)}

@app.get("/api/graph")
def api_graph():
    return get_prerequisite_graph()

class MasteryUpdateRequest(BaseModel):
    path: str
    state: str

@app.get("/api/mastery")
def get_mastery():
    return {
        "summary": get_mastery_summary(),
        "topics": load_mastery_data()
    }

@app.post("/api/mastery")
def update_mastery(req: MasteryUpdateRequest):
    return set_subtopic_mastery(req.path, req.state)

@app.get("/api/export")
def download_export(domain: str, level: Optional[str] = None):
    try:
        out_file = export_handbook(domain, level)
        return FileResponse(
            str(out_file),
            media_type="text/markdown",
            filename=out_file.name
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

@app.get("/api/topic")
def get_topic_details(
    query: str = Query(..., description="Subtopic query e.g. 'ebpf'"),
    level: Optional[str] = Query("beginner", description="Difficulty level: beginner, intermediate, advanced")
):
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

    selected_level = (level or "beginner").lower()
    target_dir = sub_path / selected_level if (sub_path / selected_level).exists() else sub_path

    foundation = ""
    lesson = ""
    labs = ""

    if (target_dir / "FOUNDATION.md").exists():
        foundation = (target_dir / "FOUNDATION.md").read_text(encoding="utf-8")
    elif (sub_path / "FOUNDATION.md").exists():
        foundation = (sub_path / "FOUNDATION.md").read_text(encoding="utf-8")

    if (target_dir / "LESSON.md").exists():
        lesson = (target_dir / "LESSON.md").read_text(encoding="utf-8")
    elif (sub_path / "LESSON.md").exists():
        lesson = (sub_path / "LESSON.md").read_text(encoding="utf-8")

    if (target_dir / "LABS.md").exists():
        labs = (target_dir / "LABS.md").read_text(encoding="utf-8")
    elif (sub_path / "LABS.md").exists():
        labs = (sub_path / "LABS.md").read_text(encoding="utf-8")

    # If lesson is not found, check artifacts folder
    if not lesson and (sub_path / "artifacts").exists():
        artifacts = list((sub_path / "artifacts").glob("lesson_*.md"))
        if artifacts:
            lesson = artifacts[0].read_text(encoding="utf-8")

    # Load or generate initial summary
    summary = ""
    summary_file = sub_path / "SUMMARY.md"
    if summary_file.exists():
        summary = summary_file.read_text(encoding="utf-8")
    elif bool(foundation or lesson or labs):
        try:
            summary = generate_initial_summary(domain, cat, sub, sub_path)
        except Exception:
            summary = ""

    # Load persistent chat history for this topic
    saved_chat_history = []
    history_file = sub_path / "sessions" / "chat_history.json"
    if history_file.exists():
        try:
            saved_chat_history = json.loads(history_file.read_text(encoding="utf-8"))
        except Exception:
            saved_chat_history = []

    return {
        "domain": domain,
        "category": cat,
        "subtopic": sub,
        "path": str(sub_path.relative_to(WORKSPACE_ROOT)),
        "persona": persona,
        "level": selected_level,
        "available_levels": available_levels or ["beginner", "intermediate", "advanced"],
        "mastery": get_subtopic_mastery(f"{domain}/{cat}/{sub}"),
        "summary": summary,
        "chat_history": saved_chat_history,
        "foundation": foundation,
        "lesson": lesson,
        "labs": labs,
        "has_content": bool(foundation or lesson or labs)
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

@app.post("/api/chat")
def chat_with_tutor(req: ChatRequest):
    target = resolve_subtopic(req.query)
    if not target:
        raise HTTPException(status_code=404, detail=f"Topic '{req.query}' not found")

    domain, cat, sub, sub_path = target
    persona = get_domain_persona(domain)

    context_parts = [
        f"# Subject: {sub.replace('_', ' ').title()} (Domain: {domain}, Category: {cat})"
    ]

    for fname in ["FOUNDATION.md", "LESSON.md", "LABS.md"]:
        fpath = sub_path / fname
        if fpath.exists():
            context_parts.append(f"\n--- {fname} (Excerpt) ---\n" + fpath.read_text(encoding="utf-8")[:2500])

    system_instruction = persona + "\n\n" + "\n".join(context_parts)
    provider = get_provider(provider_type=req.provider, model=req.model)

    conversation_text = []
    for m in req.history[-6:]:
        conversation_text.append(f"{m.role.capitalize()}: {m.content}")
    conversation_text.append(f"Student: {req.message}")
    conversation_text.append("Tutor:")

    prompt = "\n\n".join(conversation_text)
    response_text = provider.generate(prompt, system_instruction=system_instruction)
    reply = response_text.strip()

    # -------------------------------------------------------------
    # Auto-Save Conversation & History
    # -------------------------------------------------------------
    try:
        sessions_dir = sub_path / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)

        # 1. Append to active_session.md
        active_session_file = sessions_dir / "active_session.md"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"\n\n**[{timestamp}] Student:**\n{req.message}\n\n**[{timestamp}] AI Tutor:**\n{reply}\n\n---\n"
        with open(active_session_file, "a", encoding="utf-8") as f:
            f.write(entry)

        # 2. Persist chat_history.json
        history_file = sessions_dir / "chat_history.json"
        updated_history = [m.dict() for m in req.history] + [
            {"role": "student", "content": req.message},
            {"role": "tutor", "content": reply}
        ]
        history_file.write_text(json.dumps(updated_history, indent=2), encoding="utf-8")

        # 3. Auto-commit to Git in background
        subprocess.Popen(
            ["git", "add", str(sessions_dir)],
            cwd=str(WORKSPACE_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"[!] Auto-save error: {e}")

    return {
        "reply": reply
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
    for fname in ["FOUNDATION.md", "LESSON.md"]:
        fpath = sub_path / fname
        if fpath.exists():
            context_parts.append(fpath.read_text(encoding="utf-8")[:3000])

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

    master, slave = pty.openpty()
    # Default terminal size (80 cols, 24 rows)
    winsize = struct.pack("HHHH", 24, 80, 0, 0)
    fcntl.ioctl(slave, termios.TIOCSWINSZ, winsize)

    shell = os.environ.get("SHELL", "/bin/bash")
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
        env["PROMPT_COMMAND"] = ""
        os.execve(shell, [shell], env)

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
