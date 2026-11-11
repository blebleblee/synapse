#!/usr/bin/env python3
"""
Automated Clustered Curriculum Generator
Parallelizes multi-lesson curriculum generation across all available Ollama cluster nodes
(localhost, studio, ai, and maxi).
"""

import sys
import time
import argparse
import itertools
import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional, List, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from learning_engine.topic_manager import get_topic_tree, scan_subtopic_status, resolve_subtopic
from learning_engine.generator import generate_topic_parallel, generate_subtopic_content
from learning_engine.models import (
    OllamaProvider,
    OllamaCluster,
    CLUSTER_HOST_SPECS
)

git_lock = threading.Lock()

def process_subtopic_parallel(item, workers, total_count, force=False):
    idx, domain, cat, sub, sub_path = item

    status = scan_subtopic_status(sub_path)
    if status["complete"] and not force:
        print(f"[{idx:3d}/{total_count}] [↷] Skipping {domain}/{cat}/{sub} (Already Complete)", flush=True)
        return False

    print(f"[{idx:3d}/{total_count}] [*] Processing {domain} / {cat} / {sub} in parallel across {len(workers)} engines...", flush=True)
    t0 = time.time()

    try:
        results = generate_topic_parallel(
            domain=domain,
            category=cat,
            subtopic_id=sub,
            subtopic_dir=sub_path,
            force=force,
            workers=workers
        )
        created = [k for k, v in results.items() if v]
        elapsed = time.time() - t0
        if created:
            print(f"[{idx:3d}/{total_count}] [✔] Generated in {elapsed:.1f}s: {', '.join(created)}", flush=True)

            with git_lock:
                try:
                    subprocess.run(["git", "add", str(sub_path)], check=True, cwd=str(WORKSPACE_ROOT), capture_output=True)
                    commit_msg = f"content({domain}/{cat}): generate masterclass curriculum for {sub}"
                    subprocess.run(["git", "commit", "-m", commit_msg], check=True, cwd=str(WORKSPACE_ROOT), capture_output=True)
                    print(f"[{idx:3d}/{total_count}] [↑] Committed: {commit_msg}", flush=True)
                except Exception:
                    pass
            return True
        else:
            print(f"[{idx:3d}/{total_count}] [↷] Units up to date for {sub}.", flush=True)
            return False
    except Exception as e:
        print(f"[{idx:3d}/{total_count}] [✘] Error generating {sub}: {e}", flush=True)
        return False

def run_cluster_generation(target_query: Optional[str] = None, force: bool = False, test_run: bool = False):
    cluster = OllamaCluster()
    workers = cluster.get_parallel_workers()

    if not workers:
        print("[!] No Ollama cluster nodes online. Please check network/Ollama status.")
        return

    print("==================================================")
    print("   SYNAPSE 4-NODE PARALLEL GENERATION CLUSTER     ")
    print("==================================================")
    print(f"[*] Active Nodes in Cluster ({len(workers)}):")
    for host, m, _ in workers:
        spec = CLUSTER_HOST_SPECS.get(host, {})
        tier = spec.get("memory_tier", "auto")
        name = spec.get("name", host)
        print(f"    - [{name.upper():9s}] {host} (Tier: {tier:10s} | Model: {m})")
    print("==================================================")

    if test_run:
        test_target = target_query or "computing/data/database_internals"
        print(f"\n[*] Executing Test Run for: '{test_target}'...")
        target = resolve_subtopic(test_target)
        if not target:
            print(f"[!] Target '{test_target}' not found in topic tree.")
            return

        domain, cat, sub, sub_path = target
        process_subtopic_parallel((1, domain, cat, sub, sub_path), workers, 1, force=True)
        print("\n[✔] Test run finished!")
        return

    tree = get_topic_tree()
    all_subtopics = []
    idx = 1
    for domain, ddata in tree.items():
        for disc, disc_data in ddata.get("disciplines", {}).items():
            for course, c_data in disc_data.get("courses", {}).items():
                for unit, u_data in c_data.get("units", {}).items():
                    all_subtopics.append((idx, domain, f"{disc}/{course}", unit, Path(u_data["full_path"])))
                    idx += 1

    total = len(all_subtopics)
    print(f"[*] Total curriculum units: {total}\n")

    for item in all_subtopics:
        process_subtopic_parallel(item, workers, total, force=force)

    print("\n==================================================")
    print("[✔] CLUSTER BATCH GENERATION COMPLETED!")
    print("==================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synapse Clustered Multi-Node Curriculum Generator")
    parser.add_argument("--test-run", action="store_true", help="Execute single-topic test run across all 4 nodes")
    parser.add_argument("--topic", type=str, default=None, help="Target specific topic query e.g. 'database_internals'")
    parser.add_argument("--force", action="store_true", help="Force regenerate existing content")
    args = parser.parse_args()

    run_cluster_generation(target_query=args.topic, force=args.force, test_run=args.test_run)
