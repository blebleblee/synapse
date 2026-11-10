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
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
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

@app.get("/api/topic")
def get_topic_details(query: str = Query(..., description="Subtopic query e.g. 'ebpf' or 'computing_and_engineering/infrastructure_and_ops/ebpf'")):
    target = resolve_subtopic(query)
    if not target:
        raise HTTPException(status_code=404, detail=f"Topic '{query}' not found")

    domain, cat, sub, sub_path = target
    persona = get_domain_persona(domain)

    foundation = ""
    lesson = ""
    labs = ""

    if (sub_path / "FOUNDATION.md").exists():
        foundation = (sub_path / "FOUNDATION.md").read_text(encoding="utf-8")
    if (sub_path / "LESSON.md").exists():
        lesson = (sub_path / "LESSON.md").read_text(encoding="utf-8")
    if (sub_path / "LABS.md").exists():
        labs = (sub_path / "LABS.md").read_text(encoding="utf-8")

    # If lesson is not in root, check artifacts folder
    if not lesson and (sub_path / "artifacts").exists():
        artifacts = list((sub_path / "artifacts").glob("lesson_*.md"))
        if artifacts:
            lesson = artifacts[0].read_text(encoding="utf-8")

    return {
        "domain": domain,
        "category": cat,
        "subtopic": sub,
        "path": str(sub_path.relative_to(WORKSPACE_ROOT)),
        "persona": persona,
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

    return {
        "reply": response_text.strip()
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
