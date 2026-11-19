#!/usr/bin/env python3
"""
Selective ASCII & Unicode Box to Mermaid Diagram Upgrade Engine
Scans curriculum markdown files for text box-and-arrow diagrams and converts them
into authoritative, richly styled vector Mermaid flowcharts with strict rollback guards.
"""

import os
import re
import sys
import time
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from learning_engine.models import AnthropicProvider, load_env_file, repair_mermaid_diagrams
from learning_engine.linter import lint_markdown_file

load_env_file()

def is_convertible_diagram(header: str, body: str) -> bool:
    b = body.strip()
    if b.startswith(("flowchart", "sequenceDiagram", "graph")):
        return False

    lang = header.strip().lstrip("`").strip().lower()
    if lang in ["python", "bash", "sh", "c", "cpp", "rust", "go", "json", "yaml", "toml", "sql", "html", "css", "js", "ts"]:
        return False

    has_boxes = any(c in b for c in ["┌", "─", "┐", "│", "└", "┘", "╔", "═", "╗", "║", "╚", "╝"]) or bool(re.search(r"\+[-=]{3,}\+", b))
    has_arrows = any(a in b for a in ["-->", "==>", "──>", "▼", "►", "|-->"]) or ("│" in b and "v" in b)

    if not (has_boxes or has_arrows):
        return False

    # Skip directory trees
    if bool(re.search(r"^[A-Za-z]:[\\\/]|\b(?:RawLogs|Session_|\.log|\.csv)\b", b)) or ("├──" in b and "└──" in b):
        return False

    # Skip analog plot curves / coordinate charts
    if bool(re.search(r"Speed \(km\/h\)|BRAKE PRESSURE \(bar\)|Ride Height \(mm\)|Telemetry Trace|bar\) \d", b, re.IGNORECASE)):
        return False

    return True

def find_diagram_files(target_dir: Path):
    diagram_files = []
    for p in target_dir.glob("**/*.md"):
        if any(part.startswith(".") for part in p.parts):
            continue
        if p.name in ["GEMINI.md", "SYLLABUS.md", "README.md", "TOPIC_OUTLINE.md", "CURRICULUM_BLUEPRINT.md"]:
            continue
        if "sessions" in p.parts:
            continue

        txt = p.read_text(encoding="utf-8")
        blocks = re.findall(r"(```[^\n]*\n)([\s\S]*?)```", txt)
        has_diagram = any(is_convertible_diagram(h, b) for h, b in blocks)
        if has_diagram:
            diagram_files.append(p)
    return diagram_files

def convert_diagrams_in_file(file_path: Path, provider: AnthropicProvider):
    file_path = file_path.resolve()
    txt = file_path.read_text(encoding="utf-8")
    rel_p = file_path.relative_to(WORKSPACE_ROOT)

    pattern = r"(```[^\n]*\n)([\s\S]*?)(```)"
    matches = list(re.finditer(pattern, txt))

    upgraded_count = 0
    new_txt = txt

    for m in matches:
        header = m.group(1)
        body = m.group(2)

        if not is_convertible_diagram(header, body):
            continue

        prompt = f"""You are a Principal Software Architect and Mermaid.js specialist.
Convert the following box diagram into an authoritative, clean, vector Mermaid diagram (`flowchart TD` or `flowchart LR`).

DIAGRAM CONTENT:
\"\"\"
{body.strip()}
\"\"\"

INVARIANTS:
1. Output MUST be valid Mermaid syntax wrapped in ```mermaid ... ```
2. Use descriptive node IDs and quoted labels: e.g. A["Component Name"]
3. If subgraphs are present, use standard format: subgraph sub_id ["Group Title"]
4. Output ONLY the ```mermaid ... ``` code block. No explanations or conversational text."""

        try:
            res = provider.generate(prompt, max_tokens=1500)
            clean_res = res.strip()
            if "```mermaid" in clean_res:
                m_body = clean_res.split("```mermaid")[-1].split("```")[0].strip()
            elif clean_res.startswith("flowchart") or clean_res.startswith("sequenceDiagram") or clean_res.startswith("graph"):
                m_body = clean_res
            else:
                m_body = None

            if m_body:
                mermaid_block = repair_mermaid_diagrams(f"```mermaid\n{m_body}\n```")
                full_match_text = m.group(0)
                new_txt = new_txt.replace(full_match_text, mermaid_block, 1)
                upgraded_count += 1
        except Exception:
            pass

    if upgraded_count > 0:
        file_path.write_text(new_txt, encoding="utf-8")
        issues = lint_markdown_file(file_path)
        errs = [i for i in issues if i["severity"] == "error"]
        if not errs:
            return file_path, True, f"Upgraded {upgraded_count} diagram(s) to Mermaid"
        else:
            # Safe instant rollback on any linter error
            file_path.write_text(txt, encoding="utf-8")
            return file_path, False, "Linter error after conversion, safely reverted"

    return file_path, False, "No convertible diagrams"

def main():
    parser = argparse.ArgumentParser(description="Convert ASCII/Unicode box diagrams to vector Mermaid flowcharts.")
    parser.add_argument("--target", default="topics", help="Directory or domain to process (default: topics)")
    parser.add_argument("--workers", type=int, default=8, help="Number of concurrent conversion workers (default: 8)")
    args = parser.parse_args()

    target_path = (WORKSPACE_ROOT / args.target).resolve()
    print("=" * 60)
    print(" 🎨  SYNAPSE SELECTIVE DIAGRAM TO MERMAID UPGRADE ENGINE")
    print(f" Target:  {target_path.relative_to(WORKSPACE_ROOT)}")
    print(f" Workers: {args.workers}")
    print("=" * 60)

    files = find_diagram_files(target_path)
    total_count = len(files)
    print(f"[*] Found {total_count} files with convertible box diagrams in target.")
    if not files:
        print("[✔] No convertible box diagrams found.")
        return

    v_url = os.environ.get("ANTHROPIC_BASE_URL") or os.environ.get("VNAIPRO_BASE_URL") or "https://api.anthropic.com"
    v_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("VNAIPRO_API_KEY")
    provider = AnthropicProvider(base_url=v_url, api_key=v_key, model="claude-sonnet-5")

    success = 0
    done = 0
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(convert_diagrams_in_file, f, provider): f for f in files}
        for fut in as_completed(futures):
            done += 1
            p = futures[fut]
            rel_p = p.relative_to(WORKSPACE_ROOT)
            try:
                _, ok, msg = fut.result()
                if ok:
                    success += 1
                    print(f"  [{done:>3}/{total_count}] [✔] {rel_p}: {msg}", flush=True)
                else:
                    print(f"  [{done:>3}/{total_count}] [-] {rel_p}: {msg}", flush=True)
            except Exception as e:
                print(f"  [{done:>3}/{total_count}] [!] {rel_p}: {e}", flush=True)

    elapsed = time.time() - t0
    print("=" * 60)
    print(f"[*] Upgrade pass complete in {elapsed:.1f}s ({elapsed/60:.1f} mins)!")
    print(f"    Upgraded: {success}/{len(files)} files")
    print("=" * 60)

if __name__ == "__main__":
    main()
