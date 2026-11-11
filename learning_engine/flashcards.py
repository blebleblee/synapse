"""
Anki Flashcard Generator & Exporter
Synthesizes active-recall flashcard decks (CSV format) from Foundation and Lesson units.
"""

import csv
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from .models import get_provider
from .topic_manager import resolve_subtopic, get_domain_persona, get_unit_lessons

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

def generate_flashcards(query: str, provider_type: Optional[str] = None, model: Optional[str] = None) -> Path:
    target = resolve_subtopic(query)
    if not target:
        raise ValueError(f"Topic '{query}' not found.")

    domain, cat, sub, sub_path = target
    persona = get_domain_persona(domain)

    context_parts = []
    if (sub_path / "FOUNDATION.md").exists():
        context_parts.append((sub_path / "FOUNDATION.md").read_text(encoding="utf-8")[:3000])

    discovered = get_unit_lessons(sub_path)
    for l in discovered[:4]:
        p = Path(l["path"])
        if p.exists():
            context_parts.append(p.read_text(encoding="utf-8")[:2000])

    if not context_parts:
        # Check leveled subfolders
        for lvl in ["beginner", "intermediate", "advanced"]:
            lvl_dir = sub_path / lvl
            if (lvl_dir / "FOUNDATION.md").exists():
                context_parts.append((lvl_dir / "FOUNDATION.md").read_text(encoding="utf-8")[:1500])
            for l in get_unit_lessons(lvl_dir)[:2]:
                p = Path(l["path"])
                if p.exists():
                    context_parts.append(p.read_text(encoding="utf-8")[:1500])

    prompt = f"""You are creating an Anki spaced-repetition active recall flashcard deck for '{sub.replace('_', ' ').title()}'.
Based on the curriculum text below, generate 8 high-impact active recall flashcards.
Each flashcard must test a single core invariant, architectural mechanism, formula, or common misconception.

Return strictly a valid JSON array of objects with 'front' (question) and 'back' (clear, concise answer):
[
  {{
    "front": "What is the primary role of the eBPF in-kernel verifier?",
    "back": "To statically prove memory safety, type consistency, and termination via DAG analysis before JIT compilation."
  }}
]

Curriculum Context:
{"".join(context_parts)[:6000]}

Output valid JSON only with no markdown formatting."""

    provider = get_provider(provider_type=provider_type, model=model, domain=domain)
    raw = provider.generate(prompt, system_instruction=persona).strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    cards = []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            cards = parsed.get("flashcards", parsed.get("cards", []))
        elif isinstance(parsed, list):
            cards = parsed
    except Exception:
        pass

    if not cards or not isinstance(cards, list):
        cards = [
            {"front": f"What is the foundational invariant of {sub.replace('_', ' ').title()}?", "back": "Refer to Foundation documentation for core structural axioms."}
        ]

    out_csv = sub_path / "flashcards.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["#separator:Comma", "#html:true", f"#tags:{domain} {cat} {sub}"])
        for c in cards:
            if isinstance(c, dict):
                writer.writerow([c.get("front", ""), c.get("back", ""), f"{domain}::{sub}"])

    return out_csv
