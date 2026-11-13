#!/usr/bin/env python3
from pathlib import Path
import sys

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from learning_engine.models import AnthropicProvider, validate_generation_output

p = AnthropicProvider(model="claude-opus-5-5")

targets = [
    ("computing", "postgresql", WORKSPACE_ROOT / "topics/computing/data/postgresql/lesson_03_mvcc_wal_and_vacuum.md"),
    ("computing", "big_data", WORKSPACE_ROOT / "topics/computing/data/big_data/lesson_01_distributed_systems_architecture.md"),
    ("computing", "cloud_native", WORKSPACE_ROOT / "topics/computing/infrastructure/cloud_native/lesson_02_containerization_technologies.md"),
    ("computing", "devsecops", WORKSPACE_ROOT / "topics/computing/infrastructure/devsecops/lesson_01_security_foundations_shift_left.md"),
    ("computing", "chatgpt_and_openai_apis", WORKSPACE_ROOT / "topics/computing/ai/chatgpt_and_openai_apis/labs.md")
]

for domain, subtopic, path in targets:
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
    res = p.generate(prompt, max_tokens=7000)
    validated = validate_generation_output(res)
    path.write_text(validated.strip() + "\n", encoding="utf-8")
    lines = len(validated.splitlines())
    print(f"[✔] Successfully authored {path.name}: {lines} lines!", flush=True)

print("\n[✔] All 5 truncated files successfully re-authored!")
