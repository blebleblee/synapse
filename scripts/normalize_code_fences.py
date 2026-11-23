#!/usr/bin/env python3
"""
Synapse Curriculum Code-Fence Normalizer
Heuristically inspects all 4,840+ untagged markdown code fences in the workspace
and assigns appropriate language tags (bash, yaml, json, sql, python, c, text)
to achieve zero warnings in the linter while improving UI syntax highlighting.
"""

import re
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
TOPICS_DIR = WORKSPACE_ROOT / "topics"

import sys

sys.path.insert(0, str(WORKSPACE_ROOT))
from learning_engine.code_fences import classify_code_block, tag_untagged_fences  # noqa: E402,F401


def normalize_file(file_path: Path):
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return 0
    new_text, changed_count = tag_untagged_fences(content.rstrip("\n"))
    if changed_count > 0:
        file_path.write_text(new_text + "\n", encoding="utf-8")
    return changed_count

def in_code_block_toggle(current_state: bool, line: str) -> bool:
    # A simple toggle check. If currently in block, a ``` ends it. If not, it begins it.
    return not current_state

def main():
    print("[*] Normalizing all untagged markdown code fences...")
    total_files = 0
    total_blocks_fixed = 0
    
    for p in TOPICS_DIR.rglob("*.md"):
        if not p.is_file(): continue
        # Only process if not explicitly excluded
        if "node_modules" in p.parts or ".venv" in p.parts:
            continue
            
        fixed = normalize_file(p)
        if fixed > 0:
            total_files += 1
            total_blocks_fixed += fixed

    print(f"[✔] Fixed {total_blocks_fixed} untagged code blocks across {total_files} files.")

if __name__ == "__main__":
    main()
