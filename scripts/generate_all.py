#!/usr/bin/env python3
"""
Multi-Topic Parallel Curriculum Generator
Uses a work-stealing queue to saturate all Ollama cluster nodes simultaneously.
"""

import threading
import subprocess
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from learning_engine.topic_manager import get_topic_tree
from learning_engine.generator import generate_subtopic_content
from learning_engine.models import OllamaCluster

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
TOPICS_DIR = WORKSPACE_ROOT / "topics"
GIT_QUEUE = Queue()

def git_worker():
    while True:
        task = GIT_QUEUE.get()
        if task is None:
            break
        subtopic_dir, subtopic_id = task
        try:
            subprocess.run(["git", "add", str(subtopic_dir)], check=True, cwd=str(WORKSPACE_ROOT))
            subprocess.run(["git", "commit", "-m", f"gen({subtopic_id}): masterclass curriculum"], check=False, cwd=str(WORKSPACE_ROOT))
            print(f"[✔] Published: {subtopic_id}")
        except Exception as e:
            print(f"[✘] Git error for {subtopic_id}: {e}")
        GIT_QUEUE.task_done()

def is_topic_complete(subtopic_dir: Path) -> bool:
    """Checks if topic already has a masterclass lesson and operational labs."""
    if not subtopic_dir.exists():
        return False
    has_lesson = any(f.name.startswith("lesson_01_") for f in subtopic_dir.glob("*.md"))
    has_labs = (subtopic_dir / "labs.md").exists()
    return has_lesson and has_labs

def worker(task_queue: Queue, total_tasks: int, progress_counter: list):
    while True:
        task = task_queue.get()
        if task is None:
            break
        
        domain, category, subtopic_id, subtopic_dir = task
        progress_counter[0] += 1
        idx = progress_counter[0]
        print(f"\n==================================================")
        print(f"[*] [{idx}/{total_tasks}] Generating: {domain}/{category}/{subtopic_id}...")
        print(f"==================================================")
        
        try:
            generate_subtopic_content(
                domain=domain,
                category=category,
                subtopic_id=subtopic_id,
                subtopic_dir=subtopic_dir,
                force=False
            )
            GIT_QUEUE.put((subtopic_dir, subtopic_id))
            print(f"[✔] Successfully generated topic: {subtopic_id}")
            
        except Exception as e:
            print(f"[✘] Failed {subtopic_id}: {e}")
            
        task_queue.task_done()

def main():
    tree = get_topic_tree()
    task_queue = Queue()
    
    # Identify pending topics
    pending_tasks = []
    for domain, ddata in tree.items():
        for disc, categories in ddata.get("categories", {}).items():
            for sub_slug, sdata in categories.items():
                p = Path(sdata["full_path"])
                if not is_topic_complete(p):
                    pending_tasks.append((domain, disc, sub_slug, p))

    total_unwritten = len(pending_tasks)
    print(f"[*] Queue initialized: {total_unwritten} unwritten topics queued for cluster generation.")

    for item in pending_tasks:
        task_queue.put(item)

    # Concurrency: 1 topic at a time allows generate_topic_parallel to
    # fully saturate all cluster nodes simultaneously across its 4-6 lessons without socket collisions.
    num_workers = 1
    progress_counter = [0]
    threading.Thread(target=git_worker, daemon=True).start()
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        for _ in range(num_workers):
            executor.submit(worker, task_queue, total_unwritten, progress_counter)
        
        task_queue.join()
        
        for _ in range(num_workers):
            task_queue.put(None)
    
    GIT_QUEUE.put(None)
    GIT_QUEUE.join()

    subprocess.run(["git", "push", "origin", "main"], check=False, cwd=str(WORKSPACE_ROOT))
    print("[✔] All topics drafted and pushed.")

if __name__ == "__main__":
    main()
