#!/usr/bin/env python3
"""
Domain Curriculum Scoper & Blueprint Generator
Pre-flights and outlines all lessons, architecture breakdowns, and lab objectives
for an entire domain WITHOUT drafting the actual full lessons or labs.
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any

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
        # Discipline header (e.g. ### [SLES](#sles) or ## SLES)
        disc_match = re.search(r"^#{2,3}\s+\[?([^\]#]+)\]?", line)
        if disc_match:
            raw_title = disc_match.group(1).strip()
            # Normalize to clean slug
            clean_disc = re.sub(r"[^a-zA-Z0-9_]+", "_", raw_title.lower()).strip("_")
            if clean_disc in ("disciplines", "discipline"):
                continue
            # Handle common acronyms
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

        # Topic item (e.g. * `kernel_tuning_and_kdump`)
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
    parser.add_argument("--topic", default=None, help="Specific topic slug to scope (e.g. kernel_tuning_and_kdump)")
    parser.add_argument("--topics-dir", default=None, help="Root topics directory (defaults to ./topics or SYNAPSE_TOPICS_DIR)")
    parser.add_argument("--model", default="claude-sonnet-5", help="Scoping LLM model")
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

    # Read custom domain instructions if available
    domain_instructions = ""
    if gemini_path.exists():
        domain_instructions = gemini_path.read_text(encoding="utf-8")
        print(f"[★] Loaded domain mandate from {gemini_path.name}")

    provider = AnthropicProvider(model=args.model)
    print(f"[*] Initialized scoping provider: {provider.model} via {provider.base_url}")

    blueprint_path = domain_dir / "CURRICULUM_BLUEPRINT.md"
    master_blueprint_entries = []
    
    master_header = f"""# {args.domain.upper()} Curriculum Blueprint & Topic Coverage Map

**Generated for:** Professional Services & Tier 3 Support Escalation Engineers  
**Disciplines:** {len(disciplines)}  
**Total Topics:** {total_topics}  
**Architecture:** Micro-component deep dive with zero superficial filler

---
"""
    master_blueprint_entries.append(master_header)

    completed_count = 0

    for disc_slug, topics in disciplines.items():
        if args.discipline and disc_slug != args.discipline:
            continue
        disc_title = disc_slug.replace("_", " ").title()
        print(f"\n==================================================")
        print(f"[*] Discipline: {disc_title} ({len(topics)} topics)")
        print(f"==================================================")
        
        master_blueprint_entries.append(f"\n## Discipline: {disc_title}\n")

        for topic_slug in topics:
            if args.topic and topic_slug != args.topic:
                continue
            completed_count += 1
            topic_title = topic_slug.replace("_", " ").title()
            topic_dir = domain_dir / disc_slug / topic_slug
            topic_dir.mkdir(parents=True, exist_ok=True)
            outline_file = topic_dir / "TOPIC_OUTLINE.md"

            print(f"  [{completed_count:02d}/{total_topics:02d}] Scoping: {disc_slug}/{topic_slug}...", end="", flush=True)

            prompt = f"""You are a Principal Technical Curriculum Architect and SUSE Tier 3 Escalation Engineer.
Domain Mandate:
{domain_instructions}

Analyze the topic: '{topic_title}' (Discipline: '{disc_title}', Domain: '{args.domain}').

Create an exhaustive, highly technical lesson blueprint suitable for Tier 3 Support Engineers and Professional Services Architects who debug production outages, kernel crashes, and complex distributed system state failures.
Break this topic down into its authentic architectural components, failure modes, data structures, and debugging procedures.

Provide between 15 and 30 deep, focused lesson titles.
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

            try:
                res = provider.generate(prompt, max_tokens=4000)
                clean_json = re.sub(r"^```(?:json)?", "", res.strip(), flags=re.MULTILINE)
                clean_json = re.sub(r"```$", "", clean_json.strip(), flags=re.MULTILINE).strip()
                data = json.loads(clean_json)

                lesson_count = len(data.get("lessons", []))
                print(f" -> Scoped {lesson_count} Lessons [✔]", flush=True)

                # Format TOPIC_OUTLINE.md
                outline_lines = [
                    f"# Topic Blueprint: {data.get('topic_title', topic_title)}",
                    f"",
                    f"**Discipline:** `{disc_title}` | **Domain:** `{args.domain}`  ",
                    f"**Curriculum Tier:** {data.get('tier', 'L3 Support Masterclass')} ({lesson_count} In-Depth Lessons + Operational Labs)  ",
                    f"**Target Audience:** {data.get('target_audience', 'Support Escalation Engineers')}  ",
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

                # Add to master blueprint
                master_blueprint_entries.append(f"### {topic_title} (`{disc_slug}/{topic_slug}`)")
                master_blueprint_entries.append(f"* **Depth:** {lesson_count} Masterclass Lessons + Troubleshooting Labs")
                master_blueprint_entries.append(f"* **Scope:** {data.get('rationale', '')}")
                master_blueprint_entries.append(f"* **Key Tools:** {', '.join(data.get('primary_toolchains', []))}")
                master_blueprint_entries.append(f"")

            except Exception as e:
                print(f" -> Scoping Error: {e} [✘]", flush=True)

    blueprint_path.write_text("\n".join(master_blueprint_entries), encoding="utf-8")
    print(f"\n[✔] ALL TOPICS SCOPED SUCCESSFULLY!")
    print(f"    Master Blueprint: {blueprint_path}")

if __name__ == "__main__":
    main()
