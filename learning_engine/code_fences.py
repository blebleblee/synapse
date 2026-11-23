"""Language labels for unlabelled code fences.

Models often open code blocks with a bare ``` fence. The reader then cannot
highlight them and `synapse lint` warns (UNTAGGED_CODE_BLOCK). The generator
labels fences before writing; scripts/normalize_code_fences.py applies the
same labels to existing files.
"""
from typing import Tuple


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


def tag_untagged_fences(text: str) -> Tuple[str, int]:
    """Return the text with every bare opening fence given a language, and the
    number of fences labelled. Fences that already name a language are kept."""
    out = []
    in_block = False
    start = -1
    body = []
    changed = 0
    for line in text.split("\n"):
        trimmed = line.strip()
        if trimmed.startswith("```"):
            if not in_block:
                in_block = True
                start = len(out) if not trimmed[3:].strip() else -1
                body = []
            else:
                in_block = False
                if start != -1:
                    out[start] = out[start].replace("```", "```" + classify_code_block("\n".join(body)), 1)
                    changed += 1
                    start = -1
            out.append(line)
            continue
        if in_block and start != -1:
            body.append(line)
        out.append(line)
    return "\n".join(out), changed
