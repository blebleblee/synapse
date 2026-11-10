#!/usr/bin/env python3
"""
Automated Clustered Curriculum Generator
Parallelizes multi-tier lesson generation across all available Ollama cluster nodes
(localhost, studio.2464.cz, and any configured remote machines).
"""

import sys
import time
import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional, List

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from learning_engine.topic_manager import get_topic_tree, scan_subtopic_status
from learning_engine.generator import generate_subtopic_content
from learning_engine.models import (
    OllamaProvider,
    OllamaCluster,
    get_configured_hosts,
    get_provider
)

git_lock = threading.Lock()

def process_subtopic(item, host_info, total_count, force=False):
    idx, domain, cat, sub, sub_path = item
    host, model = host_info

    status = scan_subtopic_status(sub_path)
    if status["complete"] and not force:
        print(f"[{idx:3d}/{total_count}] [↷] Skipping {domain}/{cat}/{sub} (Already Complete)", flush=True)
        return False

    print(f"[{idx:3d}/{total_count}] [*] [{host} - {model}] Processing {domain} / {cat} / {sub}...", flush=True)
    sub_path.mkdir(parents=True, exist_ok=True)

    provider = OllamaProvider(host=host, model=model)

    try:
        results = generate_subtopic_content(
            domain=domain,
            category=cat,
            subtopic_id=sub,
            subtopic_dir=sub_path,
            provider=provider,
            force=force
        )
        created = [k for k, v in results.items() if v]
        if created:
            print(f"[{idx:3d}/{total_count}] [✔] Generated on {host}: {', '.join(created)}", flush=True)

            # Thread-safe Git Commit & Push
            with git_lock:
                try:
                    subprocess.run(["git", "add", str(sub_path)], check=True, cwd=str(WORKSPACE_ROOT), capture_output=True)
                    commit_msg = f"content({domain}/{cat}): generate learning units for {sub}"
                    subprocess.run(["git", "commit", "-m", commit_msg], check=True, cwd=str(WORKSPACE_ROOT), capture_output=True)
                    subprocess.run(["git", "push", "origin", "main"], check=False, cwd=str(WORKSPACE_ROOT), capture_output=True)
                    print(f"[{idx:3d}/{total_count}] [↑] Pushed to Gitea: {commit_msg}", flush=True)
                except Exception as git_err:
                    pass
            return True
        else:
            print(f"[{idx:3d}/{total_count}] [↷] Units up to date for {sub}.", flush=True)
            return False
    except Exception as e:
        print(f"[{idx:3d}/{total_count}] [✘] Error on {host} for {sub}: {e}", flush=True)
        return False

def batch_generate(provider_type=None, model=None, force=False):
    tree = get_topic_tree()

    # Discover cluster nodes
    cluster = OllamaCluster()
    cluster_status = cluster.get_cluster_status()

    # Build active worker configurations
    workers = []
    for host, hdata in cluster_status.items():
        if hdata["online"] and hdata["models"]:
            # Pick best model for this host
            h_models = hdata["models"]
            chosen = model
            if not chosen:
                if "qwen2.5-coder:32b" in h_models:
                    chosen = "qwen2.5-coder:32b"
                elif "qwen2.5-coder:7b" in h_models:
                    chosen = "qwen2.5-coder:7b"
                elif "llama3.1:8b" in h_models:
                    chosen = "llama3.1:8b"
                elif "qwen3:4b" in h_models:
                    chosen = "qwen3:4b"
                else:
                    chosen = h_models[0]
            workers.append((host, chosen))

    if not workers:
        print("[!] No Ollama cluster nodes online. Falling back to default provider.")
        workers = [("http://localhost:11434", "qwen3:4b")]

    print("==================================================")
    print("   OLLAMA MULTI-NODE CLUSTER BATCH GENERATION     ")
    print("==================================================")
    print(f"[*] Active Nodes in Cluster ({len(workers)}):")
    for host, m in workers:
        print(f"    - Node: {host} (Model: {m})")
    print("==================================================")

    # Collect all subtopics
    all_subtopics = []
    idx = 1
    for domain, ddata in tree.items():
        for cat, cdata in ddata["categories"].items():
            for sub, sdata in cdata.items():
                all_subtopics.append((idx, domain, cat, sub, Path(sdata["full_path"])))
                idx += 1

    total = len(all_subtopics)
    print(f"[*] Total subtopics in curriculum: {total}\n")

    # Round-robin dispatch across cluster workers
    worker_cycle = itertools.cycle(workers) if "itertools" in globals() else None
    import itertools
    worker_cycle = itertools.cycle(workers)

    with ThreadPoolExecutor(max_workers=len(workers)) as executor:
        futures = []
        for item in all_subtopics:
            target_worker = next(worker_cycle)
            f = executor.submit(process_subtopic, item, target_worker, total, force)
            futures.append(f)

        for f in futures:
            f.result()

    print("\n==================================================")
    print("[✔] CLUSTER BATCH GENERATION COMPLETED!")
    print("==================================================")

if __name__ == "__main__":
    batch_generate()
