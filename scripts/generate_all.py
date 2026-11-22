#!/usr/bin/env python3
"""
Multi-Topic Parallel Curriculum Generator
Uses a work-stealing queue to saturate all Ollama cluster nodes simultaneously.

The script only writes topic files. It never pushes. With --commit it commits
each finished topic locally (core domains only); review and push yourself.
"""

import os
import sys
import argparse
import re
import subprocess
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

LOG_FILE = WORKSPACE_ROOT / "generator.log"

class TeeLogger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.logfile = open(filename, "a", encoding="utf-8", buffering=1)

    def write(self, message):
        if self.terminal:
            try:
                self.terminal.write(message)
                self.terminal.flush()
            except (BrokenPipeError, OSError):
                self.terminal = None
        try:
            self.logfile.write(message)
            self.logfile.flush()
        except Exception:
            pass

    def flush(self):
        if self.terminal:
            try:
                self.terminal.flush()
            except (BrokenPipeError, OSError):
                self.terminal = None
        try:
            self.logfile.flush()
        except Exception:
            pass

from learning_engine.topic_manager import get_topic_tree
from learning_engine.generator import generate_subtopic_content
from learning_engine.models import OllamaCluster, AnthropicProvider, load_env_file
from learning_engine.enhancer import enhance_existing_topic
from learning_engine.packages import CORE_DOMAINS
TOPICS_DIR = WORKSPACE_ROOT / "topics"
SAFE_ID = re.compile(r"^[a-zA-Z0-9_\-]+$")

def commit_topic(subtopic_dir: Path, domain: str, subtopic_id: str, prefix: str, enabled: bool) -> bool:
    """Commit one finished topic locally when --commit was given. Never pushes."""
    if not enabled:
        return False
    if domain not in CORE_DOMAINS:
        print(f"[!] Not committing {subtopic_id}: its domain is not a public core domain")
        return False
    if not SAFE_ID.match(subtopic_id):
        print(f"[✘] Not committing: invalid subtopic_id '{subtopic_id}'")
        return False
    try:
        subprocess.run(["git", "add", "--", str(subtopic_dir)], check=True,
                       cwd=str(WORKSPACE_ROOT), capture_output=True, timeout=15)
        res = subprocess.run(
            ["git", "commit", "-m", f"{prefix}({subtopic_id}): masterclass curriculum", "--", str(subtopic_dir)],
            check=False, cwd=str(WORKSPACE_ROOT), capture_output=True, timeout=15, text=True,
        )
    except (subprocess.SubprocessError, OSError) as e:
        print(f"[✘] Git commit failed for {subtopic_id}: {e}")
        return False
    if res.returncode != 0:
        # Non-zero also means "nothing to commit", which is fine.
        detail = (res.stdout or res.stderr or "").strip().splitlines()
        print(f"[i] No commit for {subtopic_id}: {detail[-1] if detail else 'git commit returned ' + str(res.returncode)}")
        return False
    print(f"[✔] Committed locally: {subtopic_id}")
    return True

def is_topic_complete(subtopic_dir: Path) -> bool:
    """
    Checks if a topic is fully authored and complete.
    A topic is complete if:
    1. Directory exists and contains at least one lesson_*.md with valid masterclass depth (> 1,000 bytes)
    2. Has a valid labs.md file (> 800 bytes)
    """
    if not subtopic_dir.exists():
        return False
    try:
        lessons = [f for f in subtopic_dir.glob("lesson_*.md") if f.stat().st_size > 1000]
        labs_file = subtopic_dir / "labs.md"
        has_labs = labs_file.exists() and labs_file.stat().st_size > 800
        return bool(lessons) and has_labs
    except Exception:
        return False

def is_topic_enhanced(subtopic_id: str) -> bool:
    """Checks if a masterclass enhancement has already been committed to git for this topic."""
    try:
        res = subprocess.run(
            ["git", "log", f"--grep=enhance({subtopic_id}):", "-n", "1", "--format=%H"],
            capture_output=True, text=True, cwd=str(WORKSPACE_ROOT)
        )
        return bool(res.stdout.strip())
    except Exception:
        return False

def worker(task_queue: Queue, total_tasks: int, progress_counter: list, provider_override=None, enhance_mode=False, commit=False):
    while True:
        task = task_queue.get()
        if task is None:
            break
        
        try:
            domain, category, subtopic_id, subtopic_dir = task
            progress_counter[0] += 1
            idx = progress_counter[0]
            
            mode_str = "Enhancing" if enhance_mode else "Generating"
            print(f"\n==================================================")
            print(f"[*] [{idx}/{total_tasks}] {mode_str}: {domain}/{category}/{subtopic_id}...")
            print(f"==================================================")
            
            try:
                if enhance_mode:
                    success = enhance_existing_topic(domain, subtopic_id, subtopic_dir, provider_override)
                    if success:
                        commit_topic(subtopic_dir, domain, subtopic_id, "enhance", commit)
                else:
                    generate_subtopic_content(
                        domain=domain,
                        category=category,
                        subtopic_id=subtopic_id,
                        subtopic_dir=subtopic_dir,
                        provider=provider_override,
                        force=False
                    )
                    print(f"[✔] Successfully generated topic: {subtopic_id}")
                    commit_topic(subtopic_dir, domain, subtopic_id, "gen", commit)
            except Exception as e:
                print(f"[✘] Failed {subtopic_id}: {e}")
        except Exception as e:
            print(f"[✘] Worker encountered unhandled exception on task {task}: {e}")
        finally:
            task_queue.task_done()

def main():
    parser = argparse.ArgumentParser(description="Multi-Topic Parallel Curriculum Generator")
    parser.add_argument("--provider", choices=["anthropic", "ollama", "auto"], default="auto", help="Provider to use for generation")
    parser.add_argument("--model", type=str, default=None, help="Model override (e.g. claude-opus-5-5)")
    parser.add_argument("--domain", type=str, default=None, help="Target specific domain only")
    parser.add_argument("--enhance", action="store_true", help="Enhance existing (completed) topics instead of generating new ones")
    parser.add_argument("--force", action="store_true", help="Force re-processing even if already completed or enhanced")
    parser.add_argument("--commit", action="store_true", help="Commit each finished core-domain topic locally (never pushes)")
    args = parser.parse_args()

    sys.stdout = TeeLogger(LOG_FILE)
    sys.stderr = sys.stdout
    load_env_file()

    provider_override = None
    if args.provider == "anthropic" or (args.provider == "auto" and (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("VNAIPRO_API_KEY"))):
        target_model = args.model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
        v_url = os.environ.get("ANTHROPIC_BASE_URL") or os.environ.get("VNAIPRO_BASE_URL") or "https://api.anthropic.com"
        v_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("VNAIPRO_API_KEY")
        provider_override = AnthropicProvider(base_url=v_url, api_key=v_key, model=target_model)
        print(f"[*] Engine: Anthropic Claude [{provider_override.model}] via {provider_override.base_url}")
    else:
        print("[*] Engine: Ollama Multi-Node Local Cluster")

    tree = get_topic_tree()
    task_queue = Queue()
    
    # Identify pending or completed topics based on mode
    tasks = []
    for domain, ddata in tree.items():
        if args.domain and domain != args.domain:
            continue
        for disc, categories in ddata.get("categories", {}).items():
            for sub_slug, sdata in categories.items():
                p = Path(sdata["full_path"])
                is_complete = is_topic_complete(p)
                
                if args.enhance and is_complete:
                    if args.force or not is_topic_enhanced(sub_slug):
                        tasks.append((domain, disc, sub_slug, p))
                elif not args.enhance and not is_complete:
                    tasks.append((domain, disc, sub_slug, p))

    total_tasks = len(tasks)
    mode_label = "completed topics queued for ENHANCEMENT" if args.enhance else "unwritten topics queued for GENERATION"
    print(f"[*] Queue initialized: {total_tasks} {mode_label}.")

    for item in tasks:
        task_queue.put(item)

    # Use 1 worker for Claude to avoid extreme rate limit saturation, or standard logic for Ollama
    num_workers = 1
    progress_counter = [0]
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        for _ in range(num_workers):
            executor.submit(worker, task_queue, total_tasks, progress_counter, provider_override, args.enhance, args.commit)
        
        task_queue.join()
        
        for _ in range(num_workers):
            task_queue.put(None)
    
    print("[✔] All topics processed.")
    if args.commit:
        print("[i] Commits are local only. Review them, then push yourself.")
    else:
        print("[i] Nothing was committed. Review the changes under topics/ and commit them yourself.")

if __name__ == "__main__":
    main()
