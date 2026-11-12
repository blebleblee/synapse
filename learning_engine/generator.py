"""
Curriculum Generation Engine (Multi-Lesson Masterclass Standard)
Generates high-density, authoritative curriculum modules using domain-native strategies,
parallel cluster drafting, and cross-node adversarial review.
"""

import os
import sys
import json
import time
import re
import shutil
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from .models import (
    get_provider,
    OllamaCluster,
    OllamaProvider,
    LLMProvider,
    validate_generation_output,
    CLUSTER_HOST_SPECS,
    AnthropicProvider
)
from .topic_manager import get_domain_persona
from .security import validate_canonical_topic_path
from .domain_strategies import build_topic_modules

# Global semaphore to limit concurrent LLM requests and avoid rate limits
_LLM_SEMAPHORE = threading.Semaphore(4)

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

def purge_legacy_topic_files(topic_dir: Path):
    """
    Aggressively purges everything in the topic directory to allow clean regeneration 
    with the canonical masterclass pipeline.
    """
    if not topic_dir.exists():
        return

    # Delete all markdown files and subdirectories
    for item in topic_dir.iterdir():
        if item.is_file() and item.suffix == ".md":
            try:
                item.unlink()
            except Exception:
                pass
        elif item.is_dir():
            shutil.rmtree(item, ignore_errors=True)

BOOK_STYLE_DIRECTIVE = """CRITICAL STYLE & TONE DIRECTIVE:
- This is a masterclass textbook chapter, NOT a slide-deck presentation or outline.
- STRICTLY AVOID endless bullet-point lists. Write in rich, articulated, flowing paragraphs of narrative prose.
- Connect concepts through deep exposition, historical context, and cause-and-effect mechanical reasoning.
- Write like an authoritative technical author (e.g. O'Reilly, MIT Press, No Starch Press): articulate, human, intellectually rigorous, and engaging.
- Use lists ONLY when providing sequential step-by-step commands or parameter reference tables. All conceptual and architectural explanations must be written in full narrative prose.
- RAW OUTPUT ONLY: Do NOT include conversational preambles (e.g., 'Here is your lesson', 'Sure', etc.), HTML tags, or code fences (e.g. ```markdown ... ```) around the entire output. Output the raw Markdown text directly."""

def scope_topic_curriculum(
    domain: str,
    category: str,
    subtopic_id: str,
    subtopic_title: str,
    scoping_provider: Optional[LLMProvider] = None
) -> List[Dict[str, str]]:
    """
    Pre-Flight AI Scoping:
    Dynamically analyzes the true surface area of the subject to size the curriculum:
      - Focused Primitives / Specific Tools: 2 Lessons + Labs
      - Standard Systems / Engines / Paradigms: 3-4 Lessons + Labs
      - Flagship Architectures / Large Distributed Systems: 5-6 Lessons + Labs
    """
    domain_title = domain.replace("_", " ").title()
    category_title = category.replace("_", " ").title()

    fallback_modules = build_topic_modules(domain, category, subtopic_id, subtopic_title)
    if not scoping_provider:
        return fallback_modules

    scoping_prompt = f"""You are a Principal Technical Curriculum Architect.
Analyze the subject: '{subtopic_title}' (Domain: '{domain_title}', Discipline/Course: '{category_title}').

Determine the exact number of theoretical masterclass lessons required to provide exhaustive coverage WITHOUT superficial padding or unnecessary filler:
- Tier 1 (Focused Primitives / Narrow Tools): 2 Lessons
- Tier 2 (Standard Engines / Frameworks / Core Protocols): 3-4 Lessons
- Tier 3 (Flagship Architectures / Massive Distributed Systems): 5-6 Lessons

Output JSON only in this exact format:
{{
  "scope_tier": "focused|standard|flagship",
  "lesson_count": <int between 2 and 6>,
  "rationale": "<1 sentence justifying the chosen depth>",
  "lessons": [
    {{
      "filename": "lesson_01_<clean_slug>.md",
      "title": "Lesson 1: <Descriptive Title without 'and'>",
      "focus": "<Core theoretical focus, mechanisms, and invariants>"
    }}
  ]
}}"""

    try:
        raw_res = scoping_provider.generate(scoping_prompt, system_instruction="Output valid JSON only.")
        clean_json = raw_res.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[-1].split("```")[0].strip()
        elif clean_json.startswith("```") and clean_json.endswith("```"):
            clean_json = clean_json.split("```")[1].strip()

        parsed = json.loads(clean_json)
        tier = parsed.get("scope_tier", "standard").upper()
        rationale = parsed.get("rationale", "")
        parsed_lessons = parsed.get("lessons", [])

        if len(parsed_lessons) >= 2:
            print(f"      [★] Pre-Flight Scoping: {tier} ({len(parsed_lessons)} Lessons + Labs) -> {rationale}", flush=True)
            dynamic_modules = []
            for i, l in enumerate(parsed_lessons):
                num = i + 1
                fname = l.get("filename") or f"lesson_{num:02d}.md"
                clean_name = fname.replace(".md", "")
                if not re.match(r"^lesson_\d{2}_", clean_name):
                    clean_slug = re.sub(r"^(?:lesson_)?\d*_*", "", clean_name).strip("_")
                    fname = f"lesson_{num:02d}_{clean_slug}.md" if clean_slug else f"lesson_{num:02d}.md"

                title = l.get("title") or f"Lesson {num}"
                focus = l.get("focus") or ""

                lesson_prompt = f"""Write {title} for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Senior software engineers, systems programmers, and domain architects.
Lesson Focus: {focus}

Structure:
# {title}

## 1. First-Principles Intuition & Invariants
(Deep narrative exposition establishing theoretical grounding, problem space, and invariants)

## 2. Core Architecture & Mechanics
(Dissect internal data structures, algorithms, or execution models with ASCII or clean Mermaid diagrams)

## 3. High-Performance Optimization & Failure Modes
(Concurrency, resource scaling, boundary edge cases, and failure mitigations)

Remember: Write in rich, continuous book prose like an O'Reilly or MIT Press author. Avoid lazy bullet point lists.
Output publication-grade Markdown only."""

                dynamic_modules.append({
                    "filename": fname,
                    "title": title,
                    "prompt": lesson_prompt
                })

            # Append the domain-adaptive lab module from fallback
            lab_mod = fallback_modules[-1]
            dynamic_modules.append(lab_mod)
            return dynamic_modules
    except Exception as e:
        print(f"      [!] Pre-flight scoping note ({e}), using standard adaptive template.", flush=True)

    return fallback_modules

def generate_topic_parallel(
    domain: str,
    category: str,
    subtopic_id: str,
    subtopic_dir: Path,
    force: bool = False,
    workers: Optional[List[Tuple[str, str, OllamaProvider]]] = None
) -> Dict[str, Any]:
    """
    Generates a dynamically-scoped multi-lesson masterclass curriculum unit across all active
    Ollama cluster engines in parallel with cross-node adversarial fact-checking.
    """
    subtopic_dir = validate_canonical_topic_path(subtopic_dir)
    subtopic_dir.mkdir(parents=True, exist_ok=True)
    subtopic_title = subtopic_id.replace("_", " ").title()
    domain_title = domain.replace("_", " ").title()
    category_title = category.replace("_", " ").title()
    persona = get_domain_persona(domain)
    system_instruction = persona + "\n\n" + BOOK_STYLE_DIRECTIVE

    if workers is None:
        cluster = OllamaCluster()
        workers = cluster.get_parallel_workers()

    scoping_prov = workers[0][2] if workers else None
    modules = scope_topic_curriculum(domain, category, subtopic_id, subtopic_title, scoping_provider=scoping_prov)

    tasks_to_run = []
    results = {}

    if force:
        purge_legacy_topic_files(subtopic_dir)

    for mod in modules:
        out_path = subtopic_dir / mod["filename"]
        if not out_path.exists() or force:
            tasks_to_run.append(mod)
        else:
            results[mod["filename"]] = False

    if not tasks_to_run:
        return results

    if workers and len(workers) > 0:
        # Build parallel drafting jobs (1 worker per module)
        jobs = []
        for i, mod in enumerate(tasks_to_run):
            w = workers[i % len(workers)]
            jobs.append((mod, w))

        print(f"      [▶] Dispatched {len(jobs)} parallel drafting jobs simultaneously across cluster:", flush=True)
        for mod_item, (w_host, w_model, _) in jobs:
            host_label = CLUSTER_HOST_SPECS.get(w_host, {}).get("name", w_host).upper()
            print(f"          ├── [{host_label:9s}] -> {mod_item['filename']} ({w_model})", flush=True)

        drafts = {}

        def run_draft_job(job):
            mod_item, (w_host, w_model, w_provider) = job
            host_label = CLUSTER_HOST_SPECS.get(w_host, {}).get("name", w_host).upper()
            t0 = time.time()
            try:
                with _LLM_SEMAPHORE:
                    content = w_provider.generate(mod_item["prompt"], system_instruction=system_instruction)
                validated = validate_generation_output(content)
                elapsed = time.time() - t0
                print(f"          [✔] [{host_label:9s}] Drafted {mod_item['filename']} in {elapsed:.1f}s", flush=True)
                return mod_item["filename"], True, validated, mod_item, host_label, w_host, elapsed, None
            except Exception as e:
                print(f"          [✘] [{host_label:9s}] Failed {mod_item['filename']}: {e}", flush=True)
                return mod_item["filename"], False, None, mod_item, host_label, w_host, time.time() - t0, str(e)

        # Phase 1: Concurrently draft all modules without cross-node lock contention
        is_cloud = any("anthropic" in w[0].lower() or "gemini" in w[0].lower() for w in workers)
        pool_size = min(3, len(tasks_to_run)) if is_cloud else min(len(workers), len(tasks_to_run))
        with ThreadPoolExecutor(max_workers=pool_size) as executor:
            future_to_mod = {executor.submit(run_draft_job, job): job[0]["filename"] for job in jobs}
            for fut in as_completed(future_to_mod):
                fname, ok, content, mod_item, host_label, w_host, elapsed, err = fut.result()
                if ok and content:
                    drafts[fname] = (content, mod_item, host_label, w_host, elapsed)
                else:
                    results[fname] = False

        # Phase 2: Concurrent Quality Audit & Fact-Checking + Prose Refinement
        def get_auditor_for_host(author_host: str):
            large_reviewers = [w for w in workers if ("32b" in w[1] or "30b" in w[1]) and w[0] != author_host]
            if large_reviewers:
                return large_reviewers[0]
            distinct = [w for w in workers if w[0] != author_host]
            return distinct[0] if distinct else workers[0]

        def run_audit_and_refine_job(item):
            fname, (content, mod_item, host_label, author_host, elapsed) = item
            r_host, r_model, r_provider = get_auditor_for_host(author_host)
            r_name = CLUSTER_HOST_SPECS.get(r_host, {}).get("name", r_host).upper()
            
            final_content = content
            audit_note = "Verified"

            try:
                latex_constraint = ""
                if any(d in domain for d in ["computing", "engineering", "business", "crafts", "humanities"]):
                    latex_constraint = "3. FORMATTING: STRICTLY NO LaTeX ($...$ or $$...$$). Use plain text or code blocks for math. "
                else:
                    latex_constraint = "3. FORMATTING: Use LaTeX ($...$) for mathematical formulas where appropriate."

                refine_prompt = f"""You are a master technical author and rigorous adversarial auditor.
Audit and rewrite this masterclass chapter for '{mod_item['title']}' on '{subtopic_title}'.

AUDIT & REFINE REQUIREMENTS:
1. FACT-CHECK: Fix any fabricated APIs, hallucinated invariants, or technical inaccuracies.
2. PROSE STYLE: Rewrite all prose to be authoritative, engaging, and articulate (e.g., O'Reilly/MIT Press style). Remove all 'AI-isms' (e.g., 'In conclusion', 'It is important to note', 'I hope this helps'). Ensure continuous flow, depth, and structural coherence.
{latex_constraint}
4. DIAGRAMS & SYNTAX: Mermaid diagrams MUST use strict syntax.
   - All labels MUST be enclosed in double quotes (e.g., A -->| "Label Text" | B).
   - Use simple, linear flowcharts. Do NOT use complex subgraphs or nested nodes.
   - Examples of correct Mermaid syntax:
     - `graph TD; A -->| "Start" | B; B -->| "End" | C;`
     - `sequenceDiagram; participant A; participant B; A->>B: "Request"; B-->>A: "Response";`
5. PLACEHOLDERS: Eliminate all lazy placeholders (// TODO, ..., TBD) and bullet-point lists. Convert to rich narrative paragraphs.

DRAFT TO AUDIT & REFINE:
\"\"\"
{content[:7000]}
\"\"\"

Output the fully corrected, publication-grade, raw Markdown only."""

                refinement_res = ""
                with _LLM_SEMAPHORE:
                    refinement_res = r_provider.generate(refine_prompt, system_instruction="You are a master technical author and ruthless peer reviewer.")
                final_content = validate_generation_output(refinement_res)
                audit_note = f"Audited & Refined by [{r_name}]"
            except Exception as e:
                audit_note = f"Audit/Refine failed: {e}"

            target_file = subtopic_dir / fname
            target_file.write_text(final_content.strip() + "\n", encoding="utf-8")
            print(f"      [✔] {fname} published ({host_label} -> {audit_note})", flush=True)
            return fname, True

        if not drafts:
            return results

        with ThreadPoolExecutor(max_workers=min(4, len(drafts))) as audit_executor:
            for fname, ok in audit_executor.map(run_audit_and_refine_job, drafts.items()):
                results[fname] = ok
    else:
        provider = get_provider(domain=domain)
        for mod in tasks_to_run:
            try:
                content = provider.generate(mod["prompt"], system_instruction=system_instruction)
                validated = validate_generation_output(content)
                (subtopic_dir / mod["filename"]).write_text(validated.strip() + "\n", encoding="utf-8")
                results[mod["filename"]] = True
            except Exception:
                results[mod["filename"]] = False

    return results

def generate_subtopic_content(
    domain: str,
    category: str,
    subtopic_id: str,
    subtopic_dir: Path,
    provider: Optional[LLMProvider] = None,
    force: bool = False,
    level: Optional[str] = None
) -> Dict[str, Any]:
    """
    Standardized entrypoint for curriculum unit generation.
    Always enforces canonical 3-level taxonomy and multi-lesson masterclass generation.
    """
    subtopic_dir = validate_canonical_topic_path(subtopic_dir)
    workers = None
    if provider:
        workers = [("custom", "override", provider)]
    return generate_topic_parallel(
        domain=domain,
        category=category,
        subtopic_id=subtopic_id,
        subtopic_dir=subtopic_dir,
        force=force,
        workers=workers
    )
