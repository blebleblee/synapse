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
from typing import Callable, Optional, Dict, Any, List, Tuple

from .models import (
    get_provider,
    OllamaCluster,
    OllamaProvider,
    LLMProvider,
    validate_generation_output,
    repair_mermaid_diagrams,
    validate_lesson_completeness,
    CLUSTER_HOST_SPECS,
    AnthropicProvider,
    GenerationStopped,
)
from .topic_manager import get_domain_persona
from .security import validate_canonical_topic_path, get_workspace_root
from .rewrite_safety import split_markdown_chunks, check_rewrite, clean_model_markdown
from .code_fences import tag_untagged_fences
from .domain_strategies import build_topic_modules, GLOBAL_REGISTRY

# Global semaphore to limit concurrent LLM requests and avoid rate limits
_LLM_SEMAPHORE = threading.Semaphore(24)

WORKSPACE_ROOT = get_workspace_root()

BOOK_STYLE_DIRECTIVE = """CRITICAL STYLE & TONE DIRECTIVE:
- This is a masterclass textbook chapter, NOT a slide-deck presentation or outline.
- STRICTLY AVOID endless bullet-point lists. Write in rich, articulated, flowing paragraphs of narrative prose.
- Connect concepts through deep exposition, historical context, and cause-and-effect mechanical reasoning.
- Write like an authoritative technical author (e.g. O'Reilly, MIT Press, No Starch Press): articulate, human, intellectually rigorous, and engaging.
- Use lists ONLY when providing sequential step-by-step commands or parameter reference tables. All conceptual and architectural explanations must be written in full narrative prose.
- RAW OUTPUT ONLY: Do NOT include conversational preambles (e.g., 'Here is your lesson', 'Sure', etc.), HTML tags, or code fences (e.g. ```markdown ... ```) around the entire output. Output the raw Markdown text directly."""

def _is_music_course(domain: str, category: str, subtopic_id: str = "") -> bool:
    """Music courses: the music-like domains of the outline flow, and arts
    categories other than the visual ones."""
    from .domain_strategies import VISUAL_ARTS_CATEGORIES, VISUAL_ARTS_COURSES
    if domain in ("composing", "songwriting", "daw", "music"):
        return True
    return (domain == "arts" and category.lower() not in VISUAL_ARTS_CATEGORIES
            and subtopic_id.lower() not in VISUAL_ARTS_COURSES)


def scope_topic_curriculum(
    domain: str,
    category: str,
    subtopic_id: str,
    subtopic_title: str,
    subtopic_dir: Optional[Path] = None,
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

    if subtopic_dir:
        outline_path = subtopic_dir / "TOPIC_OUTLINE.md"
        if outline_path.exists():
            try:
                content = outline_path.read_text(encoding="utf-8")
                pattern = r"\*\s+\*\*Lesson\s+(\d+):\s+(.*?)(?:\s+\(.*?\))?\*\*"
                matches = list(re.finditer(pattern, content))
                if len(matches) >= 3:
                    parsed_lessons = []
                    for i, m in enumerate(matches):
                        num = int(m.group(1))
                        raw_title = m.group(2).strip()
                        slug = re.sub(r"[^a-z0-9]+", "_", raw_title.lower()).strip("_")
                        filename = f"lesson_{num:02d}_{slug}.md"
                        start_pos = m.end()
                        end_pos = matches[i+1].start() if i + 1 < len(matches) else len(content)
                        block = content[start_pos:end_pos]
                        focus_match = re.search(r"\*\s+\*Focus:\*\s+(.*?)(?=\n\s*\*|\n\n|\Z)", block, re.DOTALL)
                        focus = focus_match.group(1).strip() if focus_match else raw_title
                        hands_match = re.search(r"\*\s+\*(?:Hands-On|Practice|Terminal Lab|Written Practice|Oral Practice|DAW Exercise):\*\s+(.*?)(?=\n\s*\*|\n\n|\Z)", block, re.DOTALL)
                        hands_on = hands_match.group(1).strip() if hands_match else ""
                        parsed_lessons.append({"num": num, "title": f"Lesson {num}: {raw_title}", "filename": filename, "focus": focus, "hands_on": hands_on})

                    print(f"      [★] Using Blueprint Outline: {len(parsed_lessons)} Curated Lessons from TOPIC_OUTLINE.md", flush=True)
                    strategy = GLOBAL_REGISTRY.get_strategy(domain, category, subtopic_id)
                    blueprint = strategy.get_blueprint(subtopic_title, category_title)
                    default_audience = blueprint.lessons[0].audience if blueprint.lessons else f"Practitioners and specialists in {category_title}"

                    dynamic_modules = []
                    for l in parsed_lessons:
                        fname = l["filename"]
                        title = l["title"]
                        focus = l["focus"]
                        hands_on = l["hands_on"]

                        if domain in ["suse", "suse-bootcamp"] or "suse" in domain.lower():
                            structure_text = f"""ENTERPRISE MASTERCLASS CHAPTER BLUEPRINT:
Author a full-length, authoritative, deeply technical masterclass chapter (~1,800 to 2,400 words) on '{title}'.
Write like a Senior SUSE Enterprise Solutions Architect and Linux Systems Specialist: deeply articulate, intellectually rigorous, and immediately practical.

CRITICAL DYNAMIC BALANCE & STRUCTURE MANDATE:
- Blend rich, insightful narrative prose with clean, scannable bullet points, numbered step-by-step procedures, and actionable checklists.
- DO NOT write an unbroken wall of dense text. Break down concepts with clear bullet points, comparative tables, YAML/CLI blocks, and bold highlights.
- Structure your chapter with these organic, topic-specific headings (DO NOT use generic numbered labels like 'Section 1' or 'The Enterprise Problem'):
  1. The Enterprise Context & Architectural Foundations: Deep systems-level exposition explaining why this technology/subsystem matters. Explain the problem space, official SUSE documentation invariants, and core concepts in plain, precise technical English.
  2. Subsystem Architecture & Low-Level Mechanics: Clear narrative exposition on daemon lifecycles, kernel/systemd interactions, network datapath, or resource reconciliation. You MUST include a richly styled Mermaid diagram (```mermaid ... ```) visualizing the component topology, state transitions, or dataflow.
  3. Step-by-Step Command Walkthrough & Configuration: Numbered step-by-step procedures with exact CLI commands, configuration stanzas (/etc/ configs, systemd units, zypper, yast2, kubectl, crmsh), and detailed explanations of all flags and parameters.
  4. Core Reference Matrix Table: Include a clear Markdown table summarizing configuration parameters, CLI flags, port numbers, or system states.
  5. Practical Hands-On Terminal Lab: A concrete 15-minute terminal lab ({hands_on}) with exact commands, expected output blocks, and verification commands.
  6. Production Hardening & Troubleshooting Pro-Tips: Conclude with 4-5 memorable 'Golden Rules' of production administration, common failure signatures, and log debugging."""
                            relevance_mandate = f"""CRITICAL RELEVANCE & DOMAIN ISOLATION MANDATE:
- Focus 80% on actionable, hands-on Linux system administration, Kubernetes orchestration, and official SUSE documentation workflows for '{subtopic_title}' in '{category_title}'.
- STRICT TOOLCHAIN ISOLATION: Utilize ONLY official Linux, SUSE, and Kubernetes tools, commands, and configuration schemas native to '{category_title}'. ABSOLUTELY NEVER mention music production, DAWs, Ableton, Cubase, or audio engineering."""

                        elif domain == "studio_equipment" or category in ["hardware_synthesizers", "drum_machines_and_grooveboxes", "audio_interfaces_and_mixers", "guitar_pedals_and_outboard_fx", "midi_controllers_and_sequencers", "studio_monitors_and_acoustics", "studio_routing_and_utilities"]:
                            structure_text = f"""HARDWARE MASTERCLASS CHAPTER BLUEPRINT:
Author a full-length, authoritative, highly engaging hardware masterclass chapter (~1,800 to 2,400 words) on '{title}'.
Write like a Senior Recording Studio Hardware Technician and Audio Engineer: deeply articulate, passionate, and immediately practical.

CRITICAL DYNAMIC BALANCE & STRUCTURE MANDATE:
- Blend rich, insightful narrative prose with clean, scannable bullet points, numbered step-by-step procedures, and actionable checklists.
- DO NOT write an unbroken wall of dense text.
- Structure your chapter with these organic, topic-specific headings:
  1. The Hardware Dilemma & Circuit Foundations: Plain-English exposition of what this hardware circuit/engine does, demystifying audio engineering jargon.
  2. Circuit Topography & Signal Flow Mechanics: Dissect physical controls, signal path from inputs to converters, or DSP engine. You MUST include a richly styled Mermaid diagram (```mermaid ... ```) visualizing signal flow or routing.
  3. Step-by-Step Physical Controls & Menu Navigation: Numbered steps detailing exact knob names, switch positions, and secondary shift-functions.
  4. Core Hardware Parameter Reference Table: A clear Markdown table summarizing knob functions, dB ranges, I/O levels, or MIDI CCs.
  5. Hybrid Studio Rig Integration (Mackie, Apollo & Midihub): Dedicated cabling and routing steps connecting this unit into the Mackie 1202 mixer, UAD Apollo Twin, and Blokas Midihub.
  6. Hands-On Studio Lab & Calibration: A concrete 15-minute patching and calibration drill ({hands_on}).
  7. Technician Golden Rules & Traps: 4-5 bulleted pro-tips on gain staging, +22 dBu headroom, and ground loops."""
                            relevance_mandate = f"""CRITICAL RELEVANCE & DOMAIN ISOLATION MANDATE:
- Focus 80% on physical hardware manipulation, analog/digital signal flow, and authentic studio routing for '{subtopic_title}' in '{category_title}'.
- STRICT TOOLCHAIN ISOLATION: Utilize ONLY physical hardware controls, jacks, and circuits native to this specific unit. NEVER mention enterprise software or IT infrastructure."""

                        elif domain == "languages":
                            structure_text = f"""LINGUISTIC MASTERCLASS CHAPTER BLUEPRINT:
Author a full-length, authoritative, highly engaging masterclass chapter (~1,800 to 2,400 words) on '{title}'.
Write like a Senior Applied Linguist and Native-Speaker Coach: articulate, culturally grounded, and immediately practical for a native Czech speaker.

CRITICAL DYNAMIC BALANCE & STRUCTURE MANDATE:
- Blend rich, insightful narrative prose with clean, scannable bullet points, grammatical tables, and conversational dialogues.
- Structure your chapter with these organic, topic-specific headings:
  1. The Communicative Challenge & Czech Contrastive Foundations: Explain the communicative problem, demystify grammatical jargon, and contrast directly with Czech linguistic patterns and Slavic traps.
  2. Phonetic & Grammatical Mechanics: Dissect the phonetic articulation, morphological declension, or syntactic word order. You MUST include a richly styled Mermaid diagram (```mermaid ... ```) visualizing the grammatical decision tree or phonological map.
  3. Authentic Conversational Dialogues & Register Nuance: Realistic colloquial and professional dialogues demonstrating the concept in action with side-by-side translations.
  4. Core Declension / Conjugation / Vocabulary Reference Table: Comprehensive Markdown reference table.
  5. Practical Oral & Written Lab: A concrete 15-minute active recall drill ({hands_on}).
  6. Linguist Golden Rules & Slavic Traps: 4-5 bulleted pro-tips on false friends, word order (slovosled), and pronunciation."""
                            relevance_mandate = f"""CRITICAL RELEVANCE & DOMAIN ISOLATION MANDATE:
- Focus 80% on authentic language acquisition, phonetic accuracy, and conversational fluency for '{subtopic_title}' in '{category_title}'.
- Contrast directly against Czech native speaker patterns. NEVER mention unrelated IT or audio tools."""

                        elif domain in ["mathematics", "physics", "chemistry"]:
                            domain_cz = {"mathematics": "matematika", "physics": "fyzika", "chemistry": "chemie"}.get(domain, domain)
                            teacher_cz = {
                                "mathematics": "špičkový český gymnaziální profesor matematiky a autor gymnaziálních sbírek úloh",
                                "physics": "špičkový český gymnaziální profesor fyziky a autor učebnic pro gymnázia",
                                "chemistry": "špičkový český gymnaziální profesor chemie a autor gymnaziálních učebnic"
                            }.get(domain, "český středoškolský profesor a didaktik")

                            structure_text = f"""ČESKÁ GYMNAZIÁLNÍ UČEBNICE – STRUKTURA LEKCE:
Napište plnohodnotnou, autoritativní a didakticky propracovanou kapitolu gymnaziální učebnice (~1,800 až 2,400 slov) na téma '{title}'.
Pište jako {teacher_cz}: spisovnou češtinou, srozumitelně, pedagogicky poutavě a s maximální odbornou přesností podle RVP pro gymnázia v ČR.

KRITICKÁ PRAVIDLA PRO DYNAMICKOU ROVNOVÁHU A STRUKTURU:
- Pište bohatým, souvislým výkladovým textem v odstavcích, doplněným o přehledné odrážky, rámečky s definicemi, tabulky a detailně komentované vzorové příklady.
- NEPIŠTE pouze heslovitý přehled ani suché shrnutí. Každý pojem důkladně vysvětlete na reálné a geometrické intuici.
- Každou lekci strukturuujte podle následujících tematických sekcí (v češtině):
  1. Motivace a reálná/geometrická intuice: Proč tento koncept potřebujeme, kde vzniká v praxi nebo v přírodě a jaký problém řeší.
  2. Přesná vědecká teorie, definice a vzorce: Formální matematické/fyzikální/chemické definice, věty, předpoklady platnosti, význam všech symbolů a jednotek SI / názvosloví.
  3. Názorné schéma / Myšlenková mapa (Mermaid diagram): Přehledný diagram (```mermaid ... ```) znázorňující rozhodovací strom řešení, silový rozklad, reakční mechanismus nebo myšlenkový postup.
  4. Krok za krokem řešené vzorové příklady: Detailní didaktický rozbor (zadání, podmínky řešitelnosti / zápis veličin, algebraické odvození / výpočet, kontrolní zkouška, grafická či věcná interpretace).
  5. Samostatná cvičení s výsledky: Sada úloh od základních po maturitní chytáky s uvedenými výsledky pro sebekontrolu ({hands_on}).
  6. Časté chyby u písemek a maturitní chytáky: 4-5 konkrétních varování před typickými omyly studentů (znaménka, dělení nulou, jednotky, oxidační čísla)."""

                            relevance_mandate = f"""KRITICKÝ MANDÁT PRO ČISTOTU OBORU A JAZYKA:
- Pište VÝHRADNĚ 100% SPISOVNOU ČEŠTINOU s použitím standardního českého názvosloví pro obor {domain_cz} (RVP pro gymnázia v ČR).
- STRIKTNÍ IZOLACE OBORU: Zaměřte se výhradně na {domain_cz} pro téma '{subtopic_title}' v okruhu '{category_title}'.
- ABSOLUTNĚ ZAKÁZÁNO: Jakýkoliv IT žargon (Linux, servery, Kubernetes, Docker, kódování) a jakýkoliv hudební žargon (hudba, DAW, Berklee, syntezátory, kytary)."""
                        elif not _is_music_course(domain, category, subtopic_id):
                            # Every other course used to fall through to the music
                            # template below (Berklee professor, DAW shortcuts).
                            structure_text = f"""MASTERCLASS CHAPTER BLUEPRINT:
Author a full-length, authoritative, highly engaging masterclass chapter (~1,800 to 2,400 words) on '{title}' in {category_title}.
Write like an experienced practitioner and teacher of {category_title}: articulate, rigorous, and immediately practical.

CRITICAL DYNAMIC BALANCE & STRUCTURE MANDATE:
- Blend rich, insightful narrative prose with clean, scannable bullet points, numbered step-by-step procedures, and actionable checklists.
- DO NOT write an unbroken wall of dense text. Break down concepts with clear bullet points, comparative tables, and bold highlights.
- Structure your chapter with these organic, topic-specific headings:
  1. Why It Matters: The problem this concept solves and the intuition behind it, with all jargon explained in plain English.
  2. How It Works: Clear exposition of the core mechanics and principles. Include a Mermaid diagram (```mermaid ... ```) when a process or structure is easier to see than to read.
  3. Worked Examples: Two concrete, realistic examples worked through step by step.
  4. Reference Table: A clear Markdown table summarizing the key parameters, options or distinctions.
  5. Common Mistakes & How to Fix Them.
  6. Practice Exercise: A concrete exercise the learner can do now ({hands_on}).
  7. Key Takeaways: Conclude with 4-5 memorable rules of thumb."""
                            relevance_mandate = f"""CRITICAL RELEVANCE & DOMAIN ISOLATION MANDATE:
- Focus 80% on actionable, hands-on practice of '{subtopic_title}' in '{category_title}'.
- STRICT TOOLCHAIN ISOLATION: Use ONLY tools, techniques, and vocabulary native to '{category_title}'. Do not borrow examples, tools or jargon from unrelated fields."""
                        else: # composing, music, daw
                            structure_text = f"""MUSIC PRODUCTION MASTERCLASS CHAPTER BLUEPRINT:
Author a full-length, authoritative, highly engaging masterclass chapter (~1,800 to 2,400 words) on '{title}'.
Write like a world-class Berklee professor and master producer: deeply articulate, passionate, intellectually rigorous, and immediately practical.

CRITICAL DYNAMIC BALANCE & STRUCTURE MANDATE:
- Blend rich, insightful narrative prose with clean, scannable bullet points, numbered step-by-step procedures, and actionable checklists.
- DO NOT write an unbroken wall of dense text. Break down concepts with clear bullet points, comparative tables, and bold highlights.
- Structure your chapter with these organic, topic-specific headings:
  1. The Core Creative Dilemma & Human Perception: Deep psychoacoustic and emotional exposition explaining why this concept matters. Demystify all jargon in plain English.
  2. The Acoustic & Musical Mechanics: Clear narrative exposition on voice-leading, frequency real estate, rhythm, or arrangement dynamics. You MUST include a richly styled Mermaid diagram (```mermaid ... ```) visualizing the musical structure or decision tree.
  3. Measure-by-Measure Commercial Case Studies: Multi-paragraph breakdowns of 2 real-world commercial records with exact timestamps, tracking measure-by-measure what stems enter/exit and why it works.
  4. Core Reference Matrix Table: Include a clear Markdown table summarizing parameters, frequency allocations, or structural metrics.
  5. Compact DAW Quick Reference Box: A concise 10-line bullet cheat-sheet giving exact shortcuts and track setups for Ableton Live (e.g. [A] for Automation, Utility) and Steinberg Cubase (e.g. [V] Volume Automation, Draw tool [8]). Keep this compact so software steps never overshadow the musical lesson.
  6. Practical Listening & Production Lab: A concrete 15-minute auditory audit drill on the student's own project ({hands_on}).
  7. Golden Mentor Invariants: Conclude with 4-5 memorable 'Golden Rules' of the craft."""
                            relevance_mandate = f"""CRITICAL RELEVANCE & DOMAIN ISOLATION MANDATE:
- Focus 80% on actionable, hands-on music production, arrangement, and audio engineering workflows for '{subtopic_title}' in '{category_title}'.
- STRICT TOOLCHAIN ISOLATION: Utilize ONLY musical instruments, composition techniques, and DAW tools native to '{category_title}'. NEVER mention Linux, Kubernetes, or enterprise IT software."""

                        lesson_prompt = f"""Write {title} for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: {default_audience}
Lesson Focus: {focus}
Hands-On Goal: {hands_on}

{relevance_mandate}

{structure_text}

CRITICAL BUDGETING & TERMINAL INVARIANT:
- Budget your response to approximately 1,800 to 2,400 words so that all sections and the final mentor rules are completely and cleanly finished BEFORE reaching output limits.
- ABSOLUTELY NEVER cut off mid-sentence. You MUST cleanly conclude with valid terminal punctuation.
Output publication-grade Markdown only."""

                        dynamic_modules.append({
                            "filename": fname,
                            "title": title,
                            "prompt": lesson_prompt
                        })

                    # Extract focused Capstone Challenge directly from TOPIC_OUTLINE.md
                    cap_match = re.search(r"##\s+🏁\s+Capstone Challenge:\s+(.*?)\n\*\s+\*\*Objective:\*\*\s+(.*?)\n\*\s+\*\*Deliverable:\*\*\s+(.*?)(?=\n\n|\Z)", content, re.DOTALL)
                    if cap_match:
                        cap_title = cap_match.group(1).strip()
                        cap_obj = cap_match.group(2).strip()
                        cap_del = cap_match.group(3).strip()
                    else:
                        cap_title = f"{subtopic_title} Capstone Sprint"
                        cap_obj = f"Deploy and verify {subtopic_title} in a realistic production scenario."
                        cap_del = "Verifiable implementation passing diagnostic health checks."

                    if domain in ["mathematics", "physics", "chemistry"]:
                        domain_cz = {"mathematics": "matematika", "physics": "fyzika", "chemistry": "chemie"}.get(domain, domain)
                        capstone_prompt = f"""Napište průvodce praktickým maturitním projektem / laboratorní výzvou: '{cap_title}' pro '{subtopic_title}'.
Obor: '{domain_title}' | Okruh: '{category_title}'.

Cílová skupina: Studenti a maturanti gymnázií v ČR
Cíl výzvy: {cap_obj}
Požadovaný výstup: {cap_del}

STRUKTURA ZADÁNÍ MATURITNÍHO / LABORATORNÍHO PROJEKTU (~1,000 až 1,400 slov):
Navrhněte ucelený, didakticky promyšlený praktický projekt / laboratorní měření ověřující hluboké zvládnutí látky.

Struktura dokumentu v češtině:
# Praktický projekt / Maturitní sprint: {cap_title}

## 1. Cíl projektu, kontext a teoretická východiska
(Formulace problému, význam v praxi/přírodě, myšlenková mapa / schéma v Mermaid (```mermaid ... ```) a předpoklady)

## 2. Krok za krokem řešený postup a metodika
(Podrobný metodický postup řešení, odvození vztahů, bilance, laboratorní postup měření bez vynechání kroků)

## 3. Komentované vzorové řešení a výpočetní protokol
(Kompletní numerické či algebraické řešení s dosazením, jednotkami SI / chemickými rovnicemi a mezivýpočty)

## 4. Analýza chyb, mezních stavů a diskuze výsledků
(Rozbor možných nepřesností, diskuze fyzikálního/chemického/matematického smyslu výsledku, zkouška správnosti)

## 5. Závěrečná hodnoticí kritéria a kontrolní přehled
(Přehledná tabulka v Markdownu s kritérii úspěšného splnění a ověřovacími body)

KRITICKÝ MANDÁT:
- Pište výhradně 100% spisovnou češtinou s platným českým názvoslovím pro {domain_cz}.
- Žádný IT žargon (žádný Linux, Kubernetes, skripty), žádný hudební žargon.
Rozpočet: cca 1,000 až 1,400 slov s čistým formátováním.
Výstupem je pouze čistý Markdown."""
                    else:
                        capstone_prompt = f"""Author the Practical Capstone Challenge Guide: '{cap_title}' for '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: {default_audience}
Challenge Objective: {cap_obj}
Required Deliverable: {cap_del}

CAPSTONE LAB BLUEPRINT (~1,000 to 1,400 words):
Design a focused, hands-on 15–20 minute implementation sprint that allows the practitioner to prove mastery of {subtopic_title}.

Structure your capstone lab guide with these organic headings:
# Capstone Challenge: {cap_title}

## 1. Challenge Architecture & Objective
(Provide a crisp, realistic production scenario, the architectural topology diagram (```mermaid ... ```), and prerequisites)

## 2. Step-by-Step Implementation Procedure
(Numbered step-by-step CLI commands, YAML stanzas, or routing patches with exact flags and zero placeholders)

## 3. Automated Verification & Diagnostic Health Checks
(Concrete verification commands and expected terminal output blocks proving the system is healthy)

## 4. Failure Injection & Resilience Triage
(Inject a realistic edge failure, demonstrate the triage command, and restore the service)

## 5. Production Sign-Off Checklist
(A clean Markdown table with verification criteria and pass/fail indicators)

CRITICAL BUDGETING & TERMINAL INVARIANT:
- Budget your response to approximately 1,000 to 1,400 words so that all 5 sections are cleanly concluded BEFORE reaching output limits.
- ABSOLUTELY NEVER cut off mid-sentence. You MUST cleanly conclude with valid terminal punctuation.
Output publication-grade Markdown only."""

                    dynamic_modules.append({
                        "filename": "labs.md",
                        "title": f"Capstone Challenge: {cap_title}",
                        "prompt": capstone_prompt
                    })
                    return dynamic_modules
            except Exception as e:
                print(f"      [!] Note on parsing TOPIC_OUTLINE.md ({e}), falling back to AI scoping.", flush=True)

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
            
            strategy = GLOBAL_REGISTRY.get_strategy(domain, category, subtopic_id)
            blueprint = strategy.get_blueprint(subtopic_title, category_title)
            default_audience = blueprint.lessons[0].audience if blueprint.lessons else f"Practitioners and specialists in {category_title}"

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

                if domain in ["composing", "songwriting", "daw", "music"] or category in ["songwriting", "orchestral_composing", "daw_arrangement", "music_theory", "film_and_game_scoring"]:
                    structure_text = f"""MASTERCLASS CHAPTER BLUEPRINT:
Author a full-length, deeply authoritative textbook chapter (~2,800 to 3,500 words) on '{title}'.
Write like a world-class Berklee professor and master producer: deeply articulate, passionate, intellectually rigorous, and immediately practical.

MANDATORY SECTIONS TO DEVELOP WITH ORGANIC, BESPOKE HEADINGS (DO NOT use generic numbered labels like 'Section 1' or 'The Creative Problem'):
1. The Core Creative Dilemma & Human Perception: Deep psychoacoustic exposition on auditory habituation, emotional narrative, and why naive approaches fail. Demystify all jargon in plain English.
2. The Acoustic & Musical Mechanics: Deep narrative exposition on voice-leading, frequency real estate, internal velocity, and arrangement dynamics. You MUST include a richly styled Mermaid diagram (```mermaid ... ```) visualizing the musical structure or decision tree.
3. Measure-by-Measure Commercial Case Studies: Provide exhaustive, multi-paragraph breakdowns of 2-3 well-known commercial records across genres with exact timestamps, tracking measure-by-measure what stems enter/exit and why it works.
4. Comprehensive Reference Matrix Table: Include a detailed Markdown reference table summarizing parameters, frequency allocations, or structural metrics.
5. Compact DAW Quick Reference Box: A concise 10-12 line bullet cheat-sheet giving the exact shortcuts and track setups for Ableton Live (e.g. [A] for Automation, Utility Gain/Width) and Steinberg Cubase (e.g. Marker Track, [V] Volume Automation, Draw tool [8]). Keep this compact so software steps never overshadow the musical lesson.
6. Practical Listening & Production Lab: A concrete 15-minute auditory audit drill on the student's own project.
7. Mentor Invariants: Conclude with 4-5 memorable 'Golden Rules' of the craft."""
                elif domain == "studio_equipment" or category in ["hardware_synthesizers", "drum_machines_and_grooveboxes", "audio_interfaces_and_mixers", "guitar_pedals_and_outboard_fx", "midi_controllers_and_sequencers", "studio_monitors_and_acoustics", "studio_routing_and_utilities"]:
                    structure_text = f"""Structure:
# {title}

## 1. The Hardware Dilemma & The "Why"
(Plain-English exposition of what this hardware function or circuit does, demystifying any technical audio engineering jargon, and explaining why it matters in a modern studio workflow)

## 2. Circuit Architecture & Signal Flow Mechanics
(Dissect the physical hardware controls, signal path from input/oscillators to output converters, or DSP engine. You MUST include an authoritative, richly styled Mermaid diagram (```mermaid ... ```) showing signal flow, knob routing, or patch architecture. NEVER use raw ASCII art boxes)

## 3. Physical Control Walkthrough & Menu Navigation
(Exact knob names, button combinations, secondary shift-functions, and display menu paths)

## 4. Hybrid Studio Rig Integration (Apollo, Mackie & Midihub)
(Explicit step-by-step instructions on patching and routing into the Mackie 1202 mixer, UAD Apollo Twin audio interface, and Blokas Midihub MIDI matrix)

## 5. Hands-On Hardware Lab & Calibration
(A concrete 15-minute patching/calibration exercise with verification steps and auditory checks)

## 6. Technician Advice & Common Traps
(Highlight the #1 mistake users make with this unit, ground loop / gain staging warnings, and maintenance tips)"""
                elif domain == "languages":
                    structure_text = f"""Structure:
# {title}

## 1. The Linguistic Challenge & The "Why"
(Plain-English exposition of the communicative problem, demystifying linguistic jargon, and explaining why this concept is vital for natural fluency, framed specifically for a native Czech speaker)

## 2. Phonetic & Grammatical Mechanics (Czech Contrastive Framework)
(Deep narrative exposition dissecting the phonetic articulation, morphological declension, or syntactic word order. Contrast directly against Czech patterns, highlighting Slavic false friends and common traps. You MUST include an authoritative Mermaid diagram (```mermaid ... ```) illustrating the grammatical decision tree or phonological map)

## 3. Authentic Conversational Dialogues & Contexts
(Rich, realistic colloquial and professional dialogues demonstrating the concept in action with side-by-side translations and register notes)

## 4. Guided Spoken & Written Lab
(Concrete 15-minute active recall exercise, minimal pair drills, and sentence reconstruction tasks)

## 5. Linguist Advice & Slavic Native Traps
(Highlight the #1 mistake Czech speakers make with this concept and mnemonic tricks to internalize native pronunciation and syntax)"""
                else:
                    structure_text = f"""Structure:
# {title}

## 1. Enterprise Problem & Architectural Foundations
(Deep narrative exposition establishing theoretical grounding, problem space, and official documentation invariants)

## 2. Core Architecture & Mechanics
(Dissect internal data structures, daemon lifecycles, or execution models. You MUST include an authoritative, richly styled Mermaid diagram (```mermaid ... ```) showing component topology, dataflow, or state transitions)

## 3. Step-by-Step Command Walkthrough & Configuration
(Exact CLI commands, configuration stanzas, and verification procedures with detailed explanations of flags and parameters)

## 4. Guided Hands-On Lab
(A concrete hands-on terminal exercise with verification commands, expected outputs, and triage steps)

## 5. Administrator Pro-Tips & Production Hardening
(Production guidelines, common gotchas, and security/performance hardening recommendations)"""

                lesson_prompt = f"""Write {title} for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: {default_audience}
Lesson Focus: {focus}

CRITICAL RELEVANCE & ANTI-BLEED MANDATE:
- Focus 80% on actionable, hands-on practitioner execution, physical/software mechanics, and authentic workflows for '{subtopic_title}' in '{category_title}'.
- STRICT TOOLCHAIN ISOLATION: Utilize ONLY tools, software, instruments, and concepts native to '{category_title}'. ABSOLUTELY NEVER mention bpftool, eBPF, Linux kernel tracing, or unrelated software boilerplate in arts, music, visual media, or business topics.

{structure_text}

CRITICAL BUDGETING & TERMINAL INVARIANT:
- Budget your response to approximately 2,800 to 3,500 words so that all sections and the final mentor rules are completely and cleanly finished BEFORE reaching output limits.
- ABSOLUTELY NEVER cut off mid-sentence. You MUST cleanly conclude with valid terminal punctuation.
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

STAGING_DIRNAME = ".regen"


class GenerationResults(dict):
    """{filename: written?}. Files that were already on disk (and so not
    generated) are False too, for compatibility; `skipped` names them so
    callers can tell them apart from failures."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.skipped = set()


def generate_topic_parallel(
    domain: str,
    category: str,
    subtopic_id: str,
    subtopic_dir: Path,
    force: bool = False,
    workers: Optional[List[Tuple[str, str, OllamaProvider]]] = None,
    fallback_provider: Optional[LLMProvider] = None,
    should_stop: Optional[Callable[[], bool]] = None,
) -> Dict[str, Any]:
    """
    Generates a dynamically-scoped multi-lesson masterclass curriculum unit across all active
    Ollama cluster engines in parallel with cross-node adversarial fact-checking.

    Regeneration (force) used to delete the course's lessons and every
    subfolder, including the learner's chat sessions, before drafting, so a
    failure or Stop left the course empty. It now writes into a staging folder
    and replaces the old lesson files only when every file succeeded (a course
    with no lessons yet keeps the files that succeeded); subfolders are never
    touched. `should_stop` cancels: no further files are written and
    GenerationStopped is raised; a regeneration publishes nothing.
    """
    subtopic_dir = validate_canonical_topic_path(subtopic_dir)
    subtopic_dir.mkdir(parents=True, exist_ok=True)
    stop = should_stop or (lambda: False)
    if not force:
        results = _generate_topic_parallel(domain, category, subtopic_id, subtopic_dir, subtopic_dir,
                                           False, workers, fallback_provider, stop)
        if stop():
            raise GenerationStopped()
        return results

    def lesson_files():
        return [f for f in subtopic_dir.iterdir()
                if f.is_file() and f.suffix == ".md" and f.name != "TOPIC_OUTLINE.md"]

    had_lessons = bool(lesson_files())
    staging = subtopic_dir / STAGING_DIRNAME
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir()
    try:
        results = _generate_topic_parallel(domain, category, subtopic_id, subtopic_dir, staging,
                                           True, workers, fallback_provider, stop)
        if stop():
            raise GenerationStopped()
        staged = sorted(f for f in staging.iterdir() if f.is_file() and f.suffix == ".md")
        complete = bool(staged) and bool(results) and all(results.values())
        if not complete and had_lessons:
            print("      [!] Regeneration incomplete: the existing lessons were kept unchanged.", flush=True)
            return results
        # Every file succeeded: replace the old lesson files. A new course
        # keeps whatever succeeded, so a rerun only generates what is missing.
        if complete:
            for old in lesson_files():
                old.unlink()
        for f in staged:
            os.replace(f, subtopic_dir / f.name)
        return results
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _generate_topic_parallel(
    domain: str,
    category: str,
    subtopic_id: str,
    subtopic_dir: Path,
    out_dir: Path,
    force: bool,
    workers: Optional[List[Tuple[str, str, OllamaProvider]]],
    fallback_provider: Optional[LLMProvider],
    stop: Callable[[], bool],
) -> Dict[str, Any]:
    subtopic_title = subtopic_id.replace("_", " ").title()
    domain_title = domain.replace("_", " ").title()
    category_title = category.replace("_", " ").title()
    persona = get_domain_persona(domain)
    system_instruction = persona + "\n\n" + BOOK_STYLE_DIRECTIVE

    if workers is None:
        cluster = OllamaCluster()
        workers = cluster.get_parallel_workers()

    scoping_prov = (workers[0][2] if workers else fallback_provider)
    modules = scope_topic_curriculum(domain, category, subtopic_id, subtopic_title, subtopic_dir=subtopic_dir, scoping_provider=scoping_prov)

    tasks_to_run = []
    results = GenerationResults()

    for mod in modules:
        out_path = subtopic_dir / mod["filename"]
        if not out_path.exists() or force:
            tasks_to_run.append(mod)
        else:
            results[mod["filename"]] = False
            results.skipped.add(mod["filename"])

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
            active_provider = w_provider
            active_label = host_label

            for attempt in range(1, 4):
                if stop():
                    return mod_item["filename"], False, None, mod_item, active_label, w_host, time.time() - t0, "stopped"
                try:
                    with _LLM_SEMAPHORE:
                        content = active_provider.generate(mod_item["prompt"], system_instruction=system_instruction, max_tokens=8192)
                    validated = validate_lesson_completeness(content)
                    elapsed = time.time() - t0
                    w_count = len(validated.split())
                    kb_size = len(validated.encode("utf-8")) / 1024
                    print(f"          [✔] [{active_label:10s}] Drafted {mod_item['filename']} ({w_count} words, {kb_size:.1f} KB) in {elapsed:.1f}s", flush=True)
                    return mod_item["filename"], True, validated, mod_item, active_label, w_host, elapsed, None
                except Exception as e:
                    print(f"          [!] [{active_label:10s}] Quality Gate Reject on {mod_item['filename']} (Attempt {attempt}/3): {e}", flush=True)
                    # Gateway failover: if active provider fails and fallback is available, failover immediately
                    if fallback_provider and active_provider != fallback_provider:
                        print(f"          [!] [{active_label:9s}] Gateway error on {mod_item['filename']}: {e}. Failing over to backup gateway...", flush=True)
                        active_provider = fallback_provider
                        active_label = "BACKUP"
                        time.sleep(1)
                        continue

                    if attempt < 3:
                        wait_s = attempt * 6
                        print(f"          [!] [{active_label:9s}] Transient error on {mod_item['filename']}: {e} (retrying in {wait_s}s, attempt {attempt}/3)...", flush=True)
                        time.sleep(wait_s)
                        continue
                    print(f"          [✘] [{active_label:9s}] Failed {mod_item['filename']} after 3 attempts: {e}", flush=True)
                    return mod_item["filename"], False, None, mod_item, active_label, w_host, time.time() - t0, str(e)

        # Phase 1: Draft modules across parallel worker pool
        is_cloud = any("anthropic" in w[0].lower() or "gemini" in w[0].lower() or "vnaipro" in w[0].lower() for w in workers)
        pool_size = min(len(workers), len(tasks_to_run))
        with ThreadPoolExecutor(max_workers=pool_size) as executor:
            future_to_mod = {executor.submit(run_draft_job, job): job[0]["filename"] for job in jobs}
            for fut in as_completed(future_to_mod):
                try:
                    fname, ok, content, mod_item, host_label, w_host, elapsed, err = fut.result()
                    if ok and content:
                        drafts[fname] = (content, mod_item, host_label, w_host, elapsed)
                    else:
                        results[fname] = False
                except Exception as e:
                    fname = future_to_mod.get(fut, "unknown")
                    print(f"      [✘] Failed future for {fname}: {e}", flush=True)
                    results[fname] = False

        if stop():
            return results

        if is_cloud:
            # Single-pass masterclass authoring for cloud frontier models:
            # Direct publication eliminates redundant full-text re-drafting, cutting time and costs by 50%.
            for fname, (content, mod_item, host_label, w_host, elapsed) in drafts.items():
                clean_content = content.strip()
                fence_count = sum(1 for line in clean_content.splitlines() if line.strip().startswith("```"))
                if fence_count % 2 != 0:
                    clean_content += "\n```"
                if stop():
                    return results
                target_file = out_dir / fname
                target_file.write_text(tag_untagged_fences(clean_content)[0] + "\n", encoding="utf-8")
                print(f"      [✔] {fname} published ({host_label} -> Masterclass Draft in {elapsed:.1f}s)", flush=True)
                results[fname] = True
            return results

        # Phase 2: Concurrent Quality Audit & Fact-Checking + Prose Refinement (for local cluster models)
        def get_auditor_for_host(author_host: str):
            large_reviewers = [w for w in workers if ("32b" in w[1] or "30b" in w[1]) and w[0] != author_host]
            if large_reviewers:
                return large_reviewers[0]
            distinct = [w for w in workers if w[0] != author_host]
            return distinct[0] if distinct else workers[0]

        def run_audit_and_refine_job(item):
            fname, (content, mod_item, host_label, author_host, elapsed) = item
            if stop():
                return fname, False
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

                # Refine the draft part by part: a long chapter does not fit a
                # local model's context, and a reply covering only a prefix must
                # never replace the full draft.
                chunks = split_markdown_chunks(content.strip() + "\n")
                refined_chunks = []
                kept_original = 0
                for ci, chunk in enumerate(chunks):
                    part_note = (
                        f"This is part {ci + 1} of {len(chunks)} of the chapter. Rewrite ONLY this part, "
                        "keeping every heading exactly as written and in the same order."
                        if len(chunks) > 1 else
                        "Keep every heading exactly as written and in the same order."
                    )
                    refine_prompt = f"""You are a master technical author and rigorous adversarial auditor.
Audit and rewrite this masterclass chapter for '{mod_item['title']}' on '{subtopic_title}'.
{part_note}

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
6. COMPLETENESS: Do not shorten, summarize or omit any part of the text.

DRAFT TO AUDIT & REFINE:
\"\"\"
{chunk}
\"\"\"

Output the fully corrected, publication-grade, raw Markdown only."""

                    try:
                        with _LLM_SEMAPHORE:
                            refinement_res = r_provider.generate(refine_prompt, system_instruction="You are a master technical author and ruthless peer reviewer.")
                        candidate = clean_model_markdown(refinement_res)
                        ok, reason = check_rewrite(chunk, candidate)
                    except Exception as chunk_err:
                        ok, reason = False, str(chunk_err)
                    if ok:
                        refined_chunks.append(repair_mermaid_diagrams(candidate).rstrip() + "\n\n")
                    else:
                        kept_original += 1
                        print(f"      [!] {fname} part {ci + 1}/{len(chunks)}: kept draft text ({reason})", flush=True)
                        refined_chunks.append(chunk.rstrip() + "\n\n")

                final_content = "".join(refined_chunks)
                if kept_original == len(chunks):
                    audit_note = f"Refinement rejected by safety checks [{r_name}]; draft kept"
                elif kept_original:
                    audit_note = f"Audited & Refined by [{r_name}] ({kept_original}/{len(chunks)} parts kept as drafted)"
                else:
                    audit_note = f"Audited & Refined by [{r_name}]"
            except Exception as e:
                audit_note = f"Audit/Refine failed: {e}"

            if stop():
                return fname, False
            target_file = out_dir / fname
            target_file.write_text(tag_untagged_fences(final_content.strip())[0] + "\n", encoding="utf-8")
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
            if stop():
                return results
            try:
                content = provider.generate(mod["prompt"], system_instruction=system_instruction)
                validated = validate_generation_output(content)
                if stop():
                    return results
                (out_dir / mod["filename"]).write_text(tag_untagged_fences(validated.strip())[0] + "\n", encoding="utf-8")
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
    level: Optional[str] = None,
    should_stop: Optional[Callable[[], bool]] = None,
) -> Dict[str, Any]:
    """
    Standardized entrypoint for curriculum unit generation.
    Always enforces canonical 3-level taxonomy and multi-lesson masterclass generation.
    """
    subtopic_dir = validate_canonical_topic_path(subtopic_dir)
    workers = None
    cloud_url = os.environ.get("ANTHROPIC_BASE_URL") or os.environ.get("VNAIPRO_BASE_URL") or "https://api.anthropic.com"
    cloud_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("VNAIPRO_API_KEY")
    cloud_key_2 = os.environ.get("ANTHROPIC_API_KEY_2") or os.environ.get("VNAIPRO_API_KEY_2")
    cloud_key_3 = os.environ.get("ANTHROPIC_API_KEY_3") or os.environ.get("VNAIPRO_API_KEY_3")
    cloud_key_4 = os.environ.get("ANTHROPIC_API_KEY_4") or os.environ.get("VNAIPRO_API_KEY_4")

    if cloud_key:
        workers = []
        p_cloud_1 = AnthropicProvider(base_url=cloud_url, api_key=cloud_key, model="claude-sonnet-5")
        p_cloud_2 = AnthropicProvider(base_url=cloud_url, api_key=cloud_key_2, model="claude-sonnet-5") if cloud_key_2 else p_cloud_1
        p_cloud_3 = AnthropicProvider(base_url=cloud_url, api_key=cloud_key_3, model="claude-sonnet-5") if cloud_key_3 else None
        p_cloud_4 = AnthropicProvider(base_url=cloud_url, api_key=cloud_key_4, model="claude-sonnet-5") if cloud_key_4 else None

        if p_cloud_4:
            # 4-Key Architecture: Deploy 11 parallel workers across 4 keys (3 on Key 1, 3 on Key 2, 3 on Key 3, 2 on Key 4)
            workers.append(("ANTHROPIC-A1", "claude-sonnet-5", p_cloud_1))
            workers.append(("ANTHROPIC-B1", "claude-sonnet-5", p_cloud_2))
            workers.append(("ANTHROPIC-C1", "claude-sonnet-5", p_cloud_3))
            workers.append(("ANTHROPIC-D1", "claude-sonnet-5", p_cloud_4))
            workers.append(("ANTHROPIC-A2", "claude-sonnet-5", p_cloud_1))
            workers.append(("ANTHROPIC-B2", "claude-sonnet-5", p_cloud_2))
            workers.append(("ANTHROPIC-C2", "claude-sonnet-5", p_cloud_3))
            workers.append(("ANTHROPIC-D2", "claude-sonnet-5", p_cloud_4))
            workers.append(("ANTHROPIC-A3", "claude-sonnet-5", p_cloud_1))
            workers.append(("ANTHROPIC-B3", "claude-sonnet-5", p_cloud_2))
            workers.append(("ANTHROPIC-C3", "claude-sonnet-5", p_cloud_3))
        elif p_cloud_3:
            # 3-Key Architecture: Deploy 11 parallel workers across 3 keys (4 on Key 1, 4 on Key 2, 3 on Key 3)
            # This drafts all 10 lessons + 1 lab simultaneously in a single wave!
            workers.append(("ANTHROPIC-A1", "claude-sonnet-5", p_cloud_1))
            workers.append(("ANTHROPIC-B1", "claude-sonnet-5", p_cloud_2))
            workers.append(("ANTHROPIC-C1", "claude-sonnet-5", p_cloud_3))
            workers.append(("ANTHROPIC-A2", "claude-sonnet-5", p_cloud_1))
            workers.append(("ANTHROPIC-B2", "claude-sonnet-5", p_cloud_2))
            workers.append(("ANTHROPIC-C2", "claude-sonnet-5", p_cloud_3))
            workers.append(("ANTHROPIC-A3", "claude-sonnet-5", p_cloud_1))
            workers.append(("ANTHROPIC-B3", "claude-sonnet-5", p_cloud_2))
            workers.append(("ANTHROPIC-C3", "claude-sonnet-5", p_cloud_3))
            workers.append(("ANTHROPIC-A4", "claude-sonnet-5", p_cloud_1))
            workers.append(("ANTHROPIC-B4", "claude-sonnet-5", p_cloud_2))
        elif cloud_key_2:
            # 2-Key Architecture: Deploy 8 parallel workers (4 on Key 1, 4 on Key 2 = fast 2 waves)
            workers.append(("ANTHROPIC-A1", "claude-sonnet-5", p_cloud_1))
            workers.append(("ANTHROPIC-B1", "claude-sonnet-5", p_cloud_2))
            workers.append(("ANTHROPIC-A2", "claude-sonnet-5", p_cloud_1))
            workers.append(("ANTHROPIC-B2", "claude-sonnet-5", p_cloud_2))
            workers.append(("ANTHROPIC-A3", "claude-sonnet-5", p_cloud_1))
            workers.append(("ANTHROPIC-B3", "claude-sonnet-5", p_cloud_2))
            workers.append(("ANTHROPIC-A4", "claude-sonnet-5", p_cloud_1))
            workers.append(("ANTHROPIC-B4", "claude-sonnet-5", p_cloud_2))
        else:
            # Single-Key Architecture: Deploy 4 parallel workers safely on the active key
            workers.append(("ANTHROPIC-1", "claude-sonnet-5", p_cloud_1))
            workers.append(("ANTHROPIC-2", "claude-sonnet-5", p_cloud_1))
            workers.append(("ANTHROPIC-3", "claude-sonnet-5", p_cloud_1))
            workers.append(("ANTHROPIC-4", "claude-sonnet-5", p_cloud_1))
    elif provider:
        p_model = getattr(provider, "model", "custom")
        workers = [(p_model, p_model, provider)]
    return generate_topic_parallel(
        domain=domain,
        category=category,
        subtopic_id=subtopic_id,
        subtopic_dir=subtopic_dir,
        force=force,
        workers=workers,
        fallback_provider=provider,
        should_stop=should_stop,
    )
