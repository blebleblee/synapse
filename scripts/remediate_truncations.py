#!/usr/bin/env python3
"""
Automated Truncation Remediation & Completion Engine
Identifies curriculum lessons/labs that hit max_tokens ceilings and cleanly
synthesizes their concluding subsections and Summary & Verification Matrices.
"""

import os
import re
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from learning_engine.models import AnthropicProvider, load_env_file, validate_generation_output
from learning_engine.linter import lint_curriculum, lint_markdown_file

load_env_file()

def get_truncated_files():
    report = lint_curriculum()
    error_files = []
    seen = set()
    for iss in report["issues"]:
        if iss["severity"] == "error" and iss.get("code") in [
            "ABRUPT_TRUNCATION", "INCOMPLETE_SECTIONS", "TRUNCATED_OR_INCOMPLETE",
            "INCOMPLETE_LABS", "PROMPT_ECHO_LEAK", "UNCLOSED_CODE_FENCE"
        ]:
            p = WORKSPACE_ROOT / iss["file"]
            if p.exists() and p not in seen:
                seen.add(p)
                error_files.append(p)
    return error_files

def remediate_single_file(file_path: Path, provider: AnthropicProvider):
    file_path = file_path.resolve()
    rel_path = file_path.relative_to(WORKSPACE_ROOT)
    parts = file_path.relative_to(WORKSPACE_ROOT / "topics").parts
    domain = parts[0] if len(parts) > 0 else "general"
    category = parts[1] if len(parts) > 1 else ""
    subtopic = parts[2] if len(parts) > 2 else ""

    subtopic_title = subtopic.replace("_", " ").title()
    content = file_path.read_text(encoding="utf-8")
    sz = len(content.encode("utf-8"))

    # Extract first H1 heading
    h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    unit_title = h1_match.group(1).strip() if h1_match else file_path.stem.replace("_", " ").title()

    # Strategy 1: Truncated near end of an otherwise rich masterclass (>= 9KB)
    if sz >= 9000:
        # Find clean rollback boundary: look for last period followed by space/newline within last 600 chars
        search_window = content[-600:]
        last_period_offset = search_window.rfind(". ")
        if last_period_offset == -1:
            last_period_offset = search_window.rfind(".\n")

        if last_period_offset != -1:
            cut_idx = len(content) - 600 + last_period_offset + 1
            base_content = content[:cut_idx].rstrip()
        else:
            base_content = content.rstrip()

        trailing_context = base_content[-1800:]
        has_summary = bool(re.search(r"^##\s+(?:\d+\.\s*)?Summary", base_content, re.MULTILINE | re.IGNORECASE))

        summary_instruction = ""
        if not has_summary:
            summary_instruction = (
                "2. Append a final '## Summary & Verification Matrix' containing a comprehensive 4-6 row "
                "Markdown table summarizing the governing invariants, core mechanisms, and diagnostic criteria for this unit."
            )
        else:
            summary_instruction = "2. Conclude the current section cleanly with decisive, actionable takeaways."

        prompt = f"""You are a Principal Technical Fellow and authoritative masterclass author.
The following curriculum lesson was truncated at its conclusion due to token length limits.

Topic: {subtopic_title} (Domain: {domain})
Unit: {unit_title}

RECENT CONTEXT BEFORE TRUNCATION:
\"\"\"
{trailing_context}
\"\"\"

TASK:
1. Provide a rigorous, high-density conclusion (1-2 substantial paragraphs) that cleanly concludes the interrupted thoughts.
{summary_instruction}
3. Output ONLY the raw Markdown continuation text. Do not repeat the prompt or previous text.
4. Guarantee that your output ends with complete terminal punctuation."""

        for attempt in range(1, 4):
            try:
                res = provider.generate(prompt, max_tokens=2048)
                validated = validate_generation_output(res)
                if not validated:
                    continue

                # Ensure terminal punctuation
                clean_lines = [l.strip() for l in validated.splitlines() if l.strip()]
                if not clean_lines or not any(clean_lines[-1].endswith(c) for c in ('.', '!', '?', '"', "'", "```", "$$", "|", ")")):
                    continue

                new_full = base_content + "\n\n" + validated.strip() + "\n"
                file_path.write_text(new_full, encoding="utf-8")
                
                # Check if resolved
                issues = lint_markdown_file(file_path)
                errs = [i for i in issues if i["severity"] == "error"]
                if not errs:
                    return file_path, True, f"Remediated conclusion (+{len(validated.encode('utf-8'))} bytes)"
            except Exception as e:
                time.sleep(attempt * 2)

        return file_path, False, "Failed to resolve truncation after 3 attempts"

    # Strategy 2: Early truncation (< 9KB) - Re-author full masterclass
    else:
        prompt = f"""You are an authoritative domain specialist and textbook author.
Write the complete, publication-grade masterclass for:
Domain: {domain}
Topic: {subtopic_title}
File: {file_path.name}

OBJECTIVES:
1. Provide deep first-principles breakdown, physical/mathematical invariants, and architectural mechanics.
2. Structure into distinct numbered sections:
   ## 1. First-Principles Intuition & Invariants
   ## 2. Core Architecture & Mechanics
   ## 3. High-Performance Implementation & Failure Modes
   ## 4. Summary & Verification Matrix
3. Output raw Markdown only with complete terminal punctuation. No preambles or outer wrappers."""

        for attempt in range(1, 4):
            try:
                res = provider.generate(prompt, max_tokens=8192)
                validated = validate_generation_output(res)
                if validated and len(validated.encode("utf-8")) >= 2500:
                    clean_lines = [l.strip() for l in validated.splitlines() if l.strip()]
                    if clean_lines and any(clean_lines[-1].endswith(c) for c in ('.', '!', '?', '"', "'", "```", "$$", "|", ")")):
                        file_path.write_text(validated.strip() + "\n", encoding="utf-8")
                        issues = lint_markdown_file(file_path)
                        errs = [i for i in issues if i["severity"] == "error"]
                        if not errs:
                            return file_path, True, f"Re-authored from scratch ({len(validated.encode('utf-8'))} bytes)"
            except Exception as e:
                time.sleep(attempt * 2)

        return file_path, False, "Failed to re-author short file after 3 attempts"

def main():
    print("=" * 60)
    print(" 🛠️  SYNAPSE CURRICULUM TRUNCATION REMEDIATION ENGINE")
    print("=" * 60)

    truncated = get_truncated_files()
    print(f"[*] Found {len(truncated)} truncated files requiring remediation.")
    if not truncated:
        print("[✔] No truncated files found! Curriculum is 100% complete.")
        return

    v_url = os.environ.get("VNAIPRO_BASE_URL", "https://apikey.vnaipro.app")
    v_key = os.environ.get("VNAIPRO_API_KEY")
    if v_key:
        provider = AnthropicProvider(base_url=v_url, api_key=v_key, model="claude-sonnet-5")
    else:
        provider = AnthropicProvider(model="claude-sonnet-5")

    success_count = 0
    fail_count = 0
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(remediate_single_file, f, provider): f for f in truncated}
        for fut in as_completed(futures):
            f_path = futures[fut]
            rel_p = f_path.relative_to(WORKSPACE_ROOT)
            try:
                p, ok, msg = fut.result()
                if ok:
                    success_count += 1
                    print(f"  [✔] {rel_p}: {msg}", flush=True)
                else:
                    fail_count += 1
                    print(f"  [✘] {rel_p}: {msg}", flush=True)
            except Exception as e:
                fail_count += 1
                print(f"  [✘] {rel_p}: Exception: {e}", flush=True)

    elapsed = time.time() - t0
    print("=" * 60)
    print(f"[*] Remediation Complete in {elapsed:.1f}s ({elapsed/60:.1f} mins)!")
    print(f"    Successful: {success_count}/{len(truncated)}")
    print(f"    Failed:     {fail_count}/{len(truncated)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
