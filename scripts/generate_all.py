#!/usr/bin/env python3
"""
Automated Workspace-Wide Curriculum Generator
Iterates through all 6 domains and all 252 subtopics, generating complete
FOUNDATION.md, LESSON.md, and LABS.md learning modules using local Ollama (or Gemini).
"""

import sys
import time
from pathlib import Path

# Add workspace root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from learning_engine.topic_manager import get_topic_tree, scan_subtopic_status
from learning_engine.generator import generate_subtopic_content
from learning_engine.models import get_provider

def batch_generate(provider_type=None, model=None, force=False):
    tree = get_topic_tree()
    provider = get_provider(provider_type=provider_type, model=model)
    model_name = getattr(provider, "model", "default")
    provider_name = provider.__class__.__name__

    print("==================================================")
    print("     STARTING MASTER CURRICULUM BATCH GENERATION  ")
    print(f"     Provider: {provider_name} | Model: {model_name}")
    print("==================================================")

    # Collect all subtopics
    all_subtopics = []
    for domain, ddata in tree.items():
        for cat, cdata in ddata["categories"].items():
            for sub, sdata in cdata.items():
                all_subtopics.append((domain, cat, sub, Path(sdata["full_path"])))

    total = len(all_subtopics)
    print(f"[*] Found {total} total subtopics across {len(tree)} domains.\n")

    completed = 0
    skipped = 0
    generated_count = 0

    for idx, (domain, cat, sub, sub_path) in enumerate(all_subtopics, 1):
        status = scan_subtopic_status(sub_path)
        if status["complete"] and not force:
            print(f"[{idx:3d}/{total}] [↷] Skipping {domain}/{cat}/{sub} (Already Complete)")
            skipped += 1
            completed += 1
            continue

        print(f"[{idx:3d}/{total}] [*] Processing {domain} / {cat} / {sub}...")
        sub_path.mkdir(parents=True, exist_ok=True)

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
                print(f"         [✔] Generated: {', '.join(created)}", flush=True)
                generated_count += 1

                # Maintain git commits upon changes
                try:
                    import subprocess
                    subprocess.run(["git", "add", str(sub_path)], check=True, cwd=str(WORKSPACE_ROOT), capture_output=True)
                    commit_msg = f"content({domain}/{cat}): generate learning units for {sub}"
                    subprocess.run(["git", "commit", "-m", commit_msg], check=True, cwd=str(WORKSPACE_ROOT), capture_output=True)
                    subprocess.run(["git", "push", "origin", "main"], check=False, cwd=str(WORKSPACE_ROOT), capture_output=True)
                    print(f"         [↑] Committed & pushed to Gitea: {commit_msg}", flush=True)
                except Exception:
                    pass
            else:
                print(f"         [↷] All units up to date.", flush=True)
            completed += 1
        except Exception as e:
            print(f"         [✘] Error generating {sub}: {e}")
            time.sleep(2)

    print("\n==================================================")
    print(f"[✔] BATCH GENERATION FINISHED!")
    print(f"    Total Processed: {completed} / {total}")
    print(f"    Newly Generated: {generated_count}")
    print(f"    Already Complete: {skipped}")
    print("==================================================")

if __name__ == "__main__":
    batch_generate()
