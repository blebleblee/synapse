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
GIT_LOCK = threading.Lock()

def worker(task_queue: Queue):
    while True:
        task = task_queue.get()
        if task is None:
            break
        
        domain, category, subtopic_id, subtopic_dir = task
        print(f"[*] Drafting: {domain}/{category}/{subtopic_id}...")
        
        try:
            generate_subtopic_content(
                domain=domain,
                category=category,
                subtopic_id=subtopic_id,
                subtopic_dir=subtopic_dir,
                force=False
            )
            
            with GIT_LOCK:
                subprocess.run(["git", "add", str(subtopic_dir)], check=True, cwd=str(WORKSPACE_ROOT))
                subprocess.run(["git", "commit", "-m", f"gen({subtopic_id}): masterclass curriculum"], check=False, cwd=str(WORKSPACE_ROOT))
            print(f"[✔] Published: {subtopic_id}")
            
        except Exception as e:
            print(f"[✘] Failed {subtopic_id}: {e}")
            
        task_queue.task_done()

def main():
    tree = get_topic_tree()
    task_queue = Queue()
    
    # Fill queue
    for domain, ddata in tree.items():
        for disc, categories in ddata.get("categories", {}).items():
            for sub_slug, sdata in categories.items():
                task_queue.put((domain, disc, sub_slug, Path(sdata["full_path"])))

    # Start workers (equal to cluster node count)
    num_workers = 4
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        for _ in range(num_workers):
            executor.submit(worker, task_queue)
        
        task_queue.join()
        
        for _ in range(num_workers):
            task_queue.put(None)

    subprocess.run(["git", "push", "origin", "main"], check=False, cwd=str(WORKSPACE_ROOT))
    print("[✔] All topics drafted and pushed.")

if __name__ == "__main__":
    main()
