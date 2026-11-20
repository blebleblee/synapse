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

def classify_code_block(block_text: str) -> str:
    lines = [l.strip() for l in block_text.splitlines() if l.strip()]
    if not lines:
        return "text"
    
    first_line = lines[0]
    full_text = "\n".join(lines)
    
    # Heuristic 1: JSON
    if full_text.startswith("{") and full_text.endswith("}") and '"' in full_text:
        return "json"
    if full_text.startswith("[") and full_text.endswith("]") and '"' in full_text:
        return "json"
        
    # Heuristic 2: YAML / Kubernetes
    if "apiVersion:" in full_text and "kind:" in full_text:
        return "yaml"
    if first_line == "---":
        return "yaml"
        
    # Heuristic 3: Bash / Shell commands
    bash_indicators = ["$ ", "# ", "apt-get ", "apt ", "yum ", "zypper ", "zypper", "kubectl ", "docker ", "podman ", "curl ", "git ", "systemctl ", "journalctl ", "ping ", "ip ", "tar ", "export "]
    if any(first_line.startswith(ind) for ind in bash_indicators):
        return "bash"
    if any(full_text.startswith(ind) for ind in bash_indicators):
        return "bash"
        
    # Heuristic 4: Python
    if "def " in full_text and ":" in full_text:
        if "import " in full_text or "print(" in full_text:
            return "python"
            
    # Heuristic 5: SQL
    sql_indicators = ["SELECT ", "CREATE TABLE ", "INSERT INTO ", "UPDATE ", "DELETE FROM "]
    if any(full_text.upper().startswith(ind) for ind in sql_indicators):
        return "sql"
        
    # Heuristic 6: C / C++ (common in eBPF or low-level topics)
    if "#include" in full_text and ("int main" in full_text or "struct " in full_text):
        return "c"
        
    # Default to raw text (for command output, logs, tables, unidentifiable config)
    return "text"

def normalize_file(file_path: Path):
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return 0

    new_content = []
    lines = content.splitlines()
    in_block = False
    block_lines = []
    fence_start_idx = -1
    changed_count = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        trimmed = line.strip()
        
        if trimmed.startswith("```"):
            if not in_block:
                # Opening fence
                lang = trimmed[3:].strip()
                if not lang:
                    in_block = True
                    fence_start_idx = len(new_content)
                    block_lines = []
                    new_content.append(line)
                else:
                    new_content.append(line)
                    in_block = True
                    fence_start_idx = -1 # Already tagged, ignore
            else:
                # Closing fence
                in_block = False
                if fence_start_idx != -1:
                    # It was an untagged block. Let's classify it.
                    block_text = "\n".join(block_lines)
                    detected_lang = classify_code_block(block_text)
                    # Replace the opening fence
                    new_content[fence_start_idx] = new_content[fence_start_idx].replace("```", f"```{detected_lang}")
                    changed_count += 1
                    fence_start_idx = -1
                
                new_content.append(line)
        else:
            if in_block and fence_start_idx != -1:
                block_lines.append(line)
            new_content.append(line)
            
        i += 1

    if changed_count > 0:
        file_path.write_text("\n".join(new_content) + "\n", encoding="utf-8")
        
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
