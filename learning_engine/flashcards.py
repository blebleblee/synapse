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
    discovered = get_unit_lessons(sub_path)
    for l in discovered[:4]:
        p = Path(l["path"])
        if p.exists():
            context_parts.append(p.read_text(encoding="utf-8")[:2000])

    labs_file = sub_path / "labs.md"
    if labs_file.exists():
        context_parts.append(labs_file.read_text(encoding="utf-8")[:2000])

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

    cards = [c for c in cards if isinstance(c, dict) and c.get("front") and c.get("back")] if isinstance(cards, list) else []
    if not cards:
        # Don't cache a placeholder deck: the next open should try again.
        raise ValueError("The AI model did not return any flashcards. Try again or pick another model.")

    out_csv = sub_path / "flashcards.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        # Anki file headers: one "#key:value" per line, before the CSV rows.
        f.write("#separator:Comma\n#html:true\n")
        f.write(f"#tags:{domain} {cat} {sub}\n#tags column:3\n")
        writer = csv.writer(f, lineterminator="\n")
        for c in cards:
            writer.writerow([c["front"], c["back"], f"{domain}::{sub}"])

    return out_csv


def anki_csv_text(text: str) -> str:
    """Returns deck text with Anki headers one per line. Decks written before
    this fix put them on one CSV row ("#separator:Comma,#html:true,#tags:..."),
    which Anki reads as a single, invalid separator value."""
    lines = text.splitlines()
    if lines and lines[0].startswith("#separator:") and ",#" in lines[0]:
        headers = lines[0].split(",#")
        lines[0:1] = [headers[0]] + ["#" + h for h in headers[1:]] + ["#tags column:3"]
    return "\n".join(lines) + "\n"
