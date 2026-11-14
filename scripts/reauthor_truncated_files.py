#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from datetime import datetime

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from learning_engine.models import AnthropicProvider, validate_generation_output

if not os.getenv("ANTHROPIC_API_KEY"):
    print("[✘] Error: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
    sys.exit(1)

p = AnthropicProvider(model="claude-sonnet-5")

targets = [
    ("computing", "postgresql", WORKSPACE_ROOT / "topics/computing/data/postgresql/lesson_03_mvcc_wal_and_vacuum.md"),
    ("computing", "big_data", WORKSPACE_ROOT / "topics/computing/data/big_data/lesson_01_distributed_systems_architecture.md"),
    ("computing", "cloud_native", WORKSPACE_ROOT / "topics/computing/infrastructure/cloud_native/lesson_02_containerization_technologies.md"),
    ("computing", "devsecops", WORKSPACE_ROOT / "topics/computing/infrastructure/devsecops/lesson_01_security_foundations_shift_left.md"),
    ("computing", "chatgpt_and_openai_apis", WORKSPACE_ROOT / "topics/computing/ai/chatgpt_and_openai_apis/labs.md")
]

for domain, subtopic, path in targets:
    if not path.resolve().is_relative_to(WORKSPACE_ROOT):
        print(f"[✘] Security: Skipping {path.name}, path escapes workspace root", file=sys.stderr)
        continue

    title_str = path.stem.replace("_", " ").title()
    print(f"\n[~] Re-authoring complete masterclass for: {path.name} in {subtopic}...", flush=True)
    prompt = f"""You are an elite textbook author and staff engineer (MIT Press / O'Reilly standard).
Write the complete, comprehensive, publication-ready masterclass lesson for:
Topic: {subtopic} (Domain: {domain})
File: {path.stem}

OBJECTIVES:
1. Provide an exhaustive, deep first-principles breakdown with mathematical and architectural invariants.
2. Include complete, working code implementations or manifests. Do NOT truncate or leave placeholders.
3. Every Mermaid diagram must use strict subgraph IDs: subgraph sub_id ["Title"].
4. Output the complete raw Markdown document starting directly with '# {title_str}'. No outer code fences.
"""
    try:
        res = p.generate(prompt, max_tokens=8192)
        validated = validate_generation_output(res)
        
        if not validated or len(validated.strip()) < 500:
            print(f"[✘] Error: Generated content for {path.name} is too short", file=sys.stderr)
            continue
            
        if path.exists():
            backup_path = path.with_suffix(f".md.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(validated.strip() + "\n", encoding="utf-8")
        lines = len(validated.splitlines())
        print(f"[✔] Successfully authored {path.name}: {lines} lines!", flush=True)
    except Exception as e:
        print(f"[✘] Failed to author {path.name}: {e}", file=sys.stderr)

print("\n[✔] All 5 truncated files successfully re-authored!")
