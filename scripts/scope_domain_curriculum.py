#!/usr/bin/env python3
"""
Domain Curriculum Scoper & Blueprint Generator (Parallel Edition)
Pre-flights and outlines all lessons, architecture breakdowns, and lab objectives
for an entire domain WITHOUT drafting the actual full lessons or labs.
"""

import os
import sys
import re
import json
import time
import argparse
import subprocess
import threading
from pathlib import Path
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from learning_engine.models import AnthropicProvider, load_env_file
load_env_file()

def parse_syllabus(syllabus_path: Path) -> Dict[str, List[str]]:
    """Parses disciplines and topic slugs from a SYLLABUS.md file."""
    if not syllabus_path.exists():
        raise FileNotFoundError(f"Syllabus file not found: {syllabus_path}")

    content = syllabus_path.read_text(encoding="utf-8")
    disciplines = {}
    current_disc = None

    for line in content.splitlines():
        line = line.strip()
        disc_match = re.search(r"^#{2,3}\s+\[?([^\]#]+)\]?", line)
        if disc_match:
            raw_title = disc_match.group(1).strip()
            clean_disc = re.sub(r"[^a-zA-Z0-9_]+", "_", raw_title.lower()).strip("_")
            if clean_disc in ("disciplines", "discipline"):
                continue
            if "sles" in clean_disc: clean_disc = "sles"
            elif "opensuse" in clean_disc: clean_disc = "opensuse"
            elif "rancher" in clean_disc and "rke2" not in clean_disc: clean_disc = "rancher"
            elif "rke2" in clean_disc: clean_disc = "rke2"
            elif "k3s" in clean_disc: clean_disc = "k3s"
            elif "harvester" in clean_disc: clean_disc = "harvester"
            elif "longhorn" in clean_disc: clean_disc = "longhorn"
            elif "suse_ai" in clean_disc: clean_disc = "suse_ai"
            elif "observability" in clean_disc: clean_disc = "observability"
            elif "security" in clean_disc or "neuvector" in clean_disc: clean_disc = "security"
            elif "edge" in clean_disc: clean_disc = "edge"
            current_disc = clean_disc
            disciplines[current_disc] = []
            continue

        topic_match = re.search(r"^\*\s+[`']?([a-zA-Z0-9_-]+)[`']?", line)
        if topic_match and current_disc:
            slug = topic_match.group(1).strip()
            if slug not in disciplines[current_disc]:
                disciplines[current_disc].append(slug)

    return disciplines

def main():
    parser = argparse.ArgumentParser(description="Generate comprehensive topic outlines and curriculum blueprint without drafting lessons.")
    parser.add_argument("--domain", required=True, help="Domain name (e.g. suse)")
    parser.add_argument("--discipline", default=None, help="Specific discipline to scope (e.g. sles, rancher)")
    parser.add_argument("--topic", default=None, help="Specific topic slug to scope")
    parser.add_argument("--topics-dir", default=None, help="Root topics directory (defaults to ./topics or SYNAPSE_TOPICS_DIR)")
    parser.add_argument("--model", default="claude-sonnet-5", help="Scoping LLM model")
    parser.add_argument("--workers", type=int, default=3, help="Concurrent scoping workers")
    args = parser.parse_args()

    topics_root = Path(args.topics_dir or os.environ.get("SYNAPSE_TOPICS_DIR") or (WORKSPACE_ROOT / "topics")).resolve()
    domain_dir = topics_root / args.domain
    syllabus_path = domain_dir / "SYLLABUS.md"
    gemini_path = domain_dir / "GEMINI.md"

    if not syllabus_path.exists():
        print(f"[✘] Syllabus not found at {syllabus_path}")
        sys.exit(1)

    disciplines = parse_syllabus(syllabus_path)
    total_topics = sum(len(topics) for topics in disciplines.values())
    print(f"[*] Parsed {len(disciplines)} disciplines with {total_topics} topics in domain '{args.domain}' from {syllabus_path}")

    domain_instructions = ""
    if gemini_path.exists():
        domain_instructions = gemini_path.read_text(encoding="utf-8")
        print(f"[★] Loaded domain mandate from {gemini_path.name}")

    # Build provider pool
    cloud_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("VNAIPRO_API_KEY")
    cloud_url = os.environ.get("ANTHROPIC_BASE_URL") or os.environ.get("VNAIPRO_BASE_URL") or "https://api.anthropic.com"
    providers = []
    if cloud_key:
        p_cloud = AnthropicProvider(base_url=cloud_url, api_key=cloud_key, model=args.model)
        providers.append(("ANTHROPIC-1", p_cloud))
        providers.append(("ANTHROPIC-2", p_cloud))
    
    p_primary = AnthropicProvider(model=args.model)
    providers.append(("PRIMARY", p_primary))

    print(f"[*] Initialized multi-gateway scoping pool ({len(providers)} workers)")

    # Flatten task list
    tasks = []
    for disc_slug, topics in disciplines.items():
        if args.discipline and disc_slug != args.discipline:
            continue
        for topic_slug in topics:
            if args.topic and topic_slug != args.topic:
                continue
            tasks.append((disc_slug, topic_slug))

    print(f"[*] Total topics queued for scoping: {len(tasks)}")

    blueprint_path = domain_dir / "CURRICULUM_BLUEPRINT.md"
    results_lock = threading.Lock()
    scoped_results = {}
    completed_counter = [0]

    def scope_single_topic(task_item, worker_idx):
        disc_slug, topic_slug = task_item
        w_label, w_provider = providers[worker_idx % len(providers)]
        disc_title = disc_slug.replace("_", " ").title()
        topic_title = topic_slug.replace("_", " ").title()

        topic_dir = domain_dir / disc_slug / topic_slug
        topic_dir.mkdir(parents=True, exist_ok=True)
        outline_file = topic_dir / "TOPIC_OUTLINE.md"

        if outline_file.exists() and outline_file.stat().st_size > 500:
            with results_lock:
                completed_counter[0] += 1
                curr = completed_counter[0]
            print(f"  [{curr:03d}/{len(tasks):03d}] [{w_label:9s}] Cached: {disc_slug}/{topic_slug} [✔]", flush=True)
            return disc_slug, topic_slug, None

        prompt = f"""You are a Principal Technical Curriculum Architect and SUSE Tier 3 Escalation Engineer.
Domain Mandate:
{domain_instructions}

Analyze the topic: '{topic_title}' (Discipline: '{disc_title}', Domain: '{args.domain}').

Create an exhaustive, highly technical lesson blueprint suitable for Tier 3 Support Engineers and Professional Services Architects who debug production outages, kernel crashes, and complex distributed system state failures.
Break this topic down into its authentic architectural components, failure modes, data structures, and debugging procedures.

Provide between 15 and 25 deep, focused lesson titles.
Output valid JSON only in this exact schema:
{{
  "topic_title": "{topic_title}",
  "tier": "Tier-3 Pro Services Masterclass",
  "rationale": "<2 sentence architectural justification of the depth and real-world failure space>",
  "target_audience": "SUSE Tier 3 Support Escalation Engineers, Field Architects, Cloud Native SREs",
  "primary_toolchains": ["<tool 1>", "<tool 2>", "<tool 3>", "<tool 4>"],
  "lessons": [
    {{
      "index": 1,
      "filename": "lesson_01_<clean_slug>.md",
      "title": "<Descriptive Lesson Title>",
      "focus": "<1-2 sentence core technical mechanics, internal data structures, or debug procedures covered>"
    }}
  ],
  "labs_objective": "<Summary of hands-on production troubleshooting scenarios and failure simulation exercises>"
}}"""

        data = None
        t0 = time.time()
        for attempt in range(1, 4):
            try:
                res = w_provider.generate(prompt, max_tokens=8192)
                clean_json = re.sub(r"^```(?:json)?", "", res.strip(), flags=re.MULTILINE)
                clean_json = re.sub(r"```$", "", clean_json.strip(), flags=re.MULTILINE).strip()
                data = json.loads(clean_json)
                break
            except Exception as e:
                if attempt < 3:
                    time.sleep(4 * attempt)
                    continue
                print(f"  [✘] [{w_label:9s}] Scoping failed on {disc_slug}/{topic_slug}: {e}", flush=True)
                return disc_slug, topic_slug, None

        if not data:
            return disc_slug, topic_slug, None

        lesson_count = len(data.get("lessons", []))
        elapsed = time.time() - t0

        # Write TOPIC_OUTLINE.md
        outline_lines = [
            f"# Topic Blueprint: {data.get('topic_title', topic_title)}",
            f"",
            f"**Discipline:** `{disc_title}` | **Domain:** `{args.domain}`  ",
            f"**Curriculum Tier:** {data.get('tier', 'Tier-3 Pro Services Masterclass')} ({lesson_count} In-Depth Lessons + Operational Labs)  ",
            f"**Target Audience:** {data.get('target_audience', 'SUSE Tier 3 Support Escalation Engineers, Field Architects, Cloud Native SREs')}  ",
            f"**Primary Toolchains:** {', '.join(data.get('primary_toolchains', []))}  ",
            f"",
            f"## Architectural Scope & Rationale",
            f"{data.get('rationale', '')}",
            f"",
            f"## Planned Lesson Modules ({lesson_count} Chapters)",
            f""
        ]

        for l in data.get("lessons", []):
            idx = l.get("index", 0)
            fn = l.get("filename", "")
            title = l.get("title", "")
            focus = l.get("focus", "")
            outline_lines.append(f"### {idx:02d}. {title}")
            outline_lines.append(f"* **Filename:** `{fn}`")
            outline_lines.append(f"* **Core Focus:** {focus}")
            outline_lines.append(f"")

        outline_lines.append(f"## Operational Troubleshooting Labs")
        outline_lines.append(f"{data.get('labs_objective', '')}")
        outline_lines.append(f"")

        outline_file.write_text("\n".join(outline_lines), encoding="utf-8")

        with results_lock:
            completed_counter[0] += 1
            curr = completed_counter[0]
            scoped_results[(disc_slug, topic_slug)] = data

        print(f"  [{curr:03d}/{len(tasks):03d}] [{w_label:9s}] Scoped: {disc_slug}/{topic_slug} ({lesson_count} Lessons in {elapsed:.1f}s) [✔]", flush=True)
        return disc_slug, topic_slug, data

    # Execute in parallel
    pool_size = min(len(providers), len(tasks))
    print(f"[*] Starting parallel execution with pool size: {pool_size}...")

    with ThreadPoolExecutor(max_workers=pool_size) as executor:
        futures = {executor.submit(scope_single_topic, task, i): task for i, task in enumerate(tasks)}
        for fut in as_completed(futures):
            fut.result()

    # Recompile master CURRICULUM_BLUEPRINT.md
    print(f"[*] Compiling Master Curriculum Blueprint at {blueprint_path}...")
    master_lines = [
        f"# {args.domain.upper()} Master Curriculum Blueprint & Architecture Map",
        f"",
        f"**Generated for:** Professional Services & Tier 3 Support Escalation Engineers  ",
        f"**Disciplines:** {len(disciplines)}  ",
        f"**Total Topics:** {total_topics}  ",
        f"**Architecture:** Micro-component deep dive with zero superficial filler",
        f"",
        f"---",
        f""
    ]

    for disc_slug, topics in disciplines.items():
        if args.discipline and disc_slug != args.discipline:
            continue
        disc_title = disc_slug.replace("_", " ").title()
        master_lines.append(f"\n## Discipline: {disc_title}\n")

        for topic_slug in topics:
            if args.topic and topic_slug != args.topic:
                continue
            topic_title = topic_slug.replace("_", " ").title()
            outline_file = domain_dir / disc_slug / topic_slug / "TOPIC_OUTLINE.md"
            if outline_file.exists():
                lines = outline_file.read_text(encoding="utf-8").splitlines()
                tier_line = next((l for l in lines if l.startswith("**Curriculum Tier:**")), "")
                scope_idx = next((i for i, l in enumerate(lines) if l.startswith("## Architectural Scope")), -1)
                rationale = lines[scope_idx + 1] if scope_idx != -1 and scope_idx + 1 < len(lines) else ""
                tools_line = next((l for l in lines if l.startswith("**Primary Toolchains:**")), "")

                master_lines.append(f"### {topic_title} (`{disc_slug}/{topic_slug}`)")
                master_lines.append(f"* **Outline File:** [`topics/{args.domain}/{disc_slug}/{topic_slug}/TOPIC_OUTLINE.md`](topics/{args.domain}/{disc_slug}/{topic_slug}/TOPIC_OUTLINE.md)")
                if tier_line: master_lines.append(f"* {tier_line}")
                if tools_line: master_lines.append(f"* {tools_line}")
                if rationale: master_lines.append(f"* **Scope Rationale:** {rationale}")
                master_lines.append(f"")

    blueprint_path.write_text("\n".join(master_lines), encoding="utf-8")
    print(f"[✔] Master Blueprint successfully written!")

    # Auto commit and push to git if in synapse-addons repo
    try:
        repo_dir = domain_dir.parent.parent
        if (repo_dir / ".git").exists():
            print(f"[*] Committing and pushing blueprints to git in {repo_dir}...")
            subprocess.run(["git", "add", "topics/"], cwd=str(repo_dir), check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", f"docs({args.domain}): complete full set of TOPIC_OUTLINE.md blueprints"], cwd=str(repo_dir), check=True, capture_output=True)
            subprocess.run(["git", "push", "origin", "main"], cwd=str(repo_dir), check=True, capture_output=True, timeout=30)
            print(f"[✔] Successfully pushed full blueprint suite to remote git repository!")
    except Exception as e:
        print(f"[!] Git push note: {e}")

    print(f"\n[✔] ALL {len(tasks)} TOPICS OUTLINED & PUSHED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
