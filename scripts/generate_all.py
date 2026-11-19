#!/usr/bin/env python3
"""
Multi-Topic Parallel Curriculum Generator
Uses a work-stealing queue to saturate all Ollama cluster nodes simultaneously.
"""

import os
import sys
import argparse
import threading
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

sys.stdout = TeeLogger(LOG_FILE)
sys.stderr = sys.stdout

from learning_engine.topic_manager import get_topic_tree
from learning_engine.generator import generate_subtopic_content
from learning_engine.models import OllamaCluster, AnthropicProvider, load_env_file
from learning_engine.enhancer import enhance_existing_topic
load_env_file()
TOPICS_DIR = WORKSPACE_ROOT / "topics"
GIT_QUEUE = Queue()

import re

def git_worker():
    while True:
        task = GIT_QUEUE.get()
        if task is None:
            GIT_QUEUE.task_done()
            break
        try:
            subtopic_dir, subtopic_id, prefix = task
            
            # Security: validate subtopic_id to prevent commit message injection
            if not re.match(r"^[a-zA-Z0-9_\-]+$", subtopic_id):
                print(f"[✘] Git error: Invalid subtopic_id '{subtopic_id}'")
                continue

            published = False
            for attempt in range(5):
                try:
                    # Add a timeout to prevent hanging git processes
                    subprocess.run(["git", "add", str(subtopic_dir)], check=True, cwd=str(WORKSPACE_ROOT), capture_output=True, timeout=15)
                    
                    # Check=False on commit because it fails if there are no changes, which is fine
                    subprocess.run(
                        ["git", "commit", "-m", f"{prefix}({subtopic_id}): masterclass curriculum"],
                        check=False, cwd=str(WORKSPACE_ROOT), capture_output=True, timeout=15
                    )
                    
                    # Push with check=True so we actually detect failures
                    res = subprocess.run(
                        ["git", "push", "origin", "main"],
                        check=True, cwd=str(WORKSPACE_ROOT), capture_output=True, timeout=30, text=True
                    )
                    print(f"[✔] Published & Pushed: {subtopic_id}")
                    published = True
                    break
                except subprocess.TimeoutExpired:
                    print(f"      [!] Git operation timed out for {subtopic_id} (attempt {attempt+1}/5)")
                    time.sleep(2)
                except subprocess.CalledProcessError:
                    # Could be remote rejection, fast-forward error, etc.
                    time.sleep(2)
                except Exception as e:
                    print(f"      [!] Unexpected Git error for {subtopic_id}: {e}")
                    time.sleep(2)
                    
            if not published:
                print(f"[✘] Git error for {subtopic_id}: Failed to publish after 5 attempts")
        except Exception as e:
            print(f"[✘] Git worker encountered unhandled error: {e}")
        finally:
            GIT_QUEUE.task_done()

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

def worker(task_queue: Queue, total_tasks: int, progress_counter: list, provider_override=None, enhance_mode=False):
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
                        GIT_QUEUE.put((subtopic_dir, subtopic_id, "enhance"))
                else:
                    generate_subtopic_content(
                        domain=domain,
                        category=category,
                        subtopic_id=subtopic_id,
                        subtopic_dir=subtopic_dir,
                        provider=provider_override,
                        force=False
                    )
                    GIT_QUEUE.put((subtopic_dir, subtopic_id, "gen"))
                    print(f"[✔] Successfully generated topic: {subtopic_id}")
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
    args = parser.parse_args()

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
    threading.Thread(target=git_worker, daemon=True).start()
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        for _ in range(num_workers):
            executor.submit(worker, task_queue, total_tasks, progress_counter, provider_override, args.enhance)
        
        task_queue.join()
        
        for _ in range(num_workers):
            task_queue.put(None)
    
    GIT_QUEUE.put(None)
    GIT_QUEUE.join()

    subprocess.run(["git", "push", "origin", "main"], check=False, cwd=str(WORKSPACE_ROOT))
    print(f"[✔] All topics processed and pushed.")

if __name__ == "__main__":
    main()
