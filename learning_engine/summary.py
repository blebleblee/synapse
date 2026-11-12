"""
Topic Summary Engine
Generates, maintains, and dynamically regenerates SUMMARY.md for canonical masterclasses,
incorporating sequential lessons, operational labs, and ongoing Socratic AI discussion sessions.
"""

from pathlib import Path
from typing import Optional
from .models import get_provider, LLMProvider
from .topic_manager import resolve_subtopic, get_domain_persona, get_unit_lessons

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

def generate_initial_summary(domain: str, category: str, subtopic_id: str, subtopic_dir: Path, provider: Optional[LLMProvider] = None) -> str:
    if not provider:
        provider = get_provider(domain=domain)

    persona = get_domain_persona(domain)
    subtopic_title = subtopic_id.replace("_", " ").title()

    # Collect available masterclass context
    context = []
    for l in get_unit_lessons(subtopic_dir)[:4]:
        p = Path(l["path"])
        if p.exists():
            context.append(f"\n--- {l['title']} ---\n" + p.read_text(encoding="utf-8")[:2000])

    labs_path = subtopic_dir / "labs.md"
    if labs_path.exists():
        context.append(f"\n--- Operational Labs ---\n" + labs_path.read_text(encoding="utf-8")[:2000])

    prompt = f"""You are writing an Executive Summary textbook chapter for '{subtopic_title}'.
Domain: '{domain.replace('_', ' ').title()}' | Discipline: '{category.replace('_', ' ').title()}'.

CRITICAL STYLE MANDATE:
- Write in continuous, articulate narrative book prose (O'Reilly / MIT Press textbook style).
- DO NOT use lazy bullet-point lists for conceptual explanations. Use full, flowing paragraphs.
- Build cause-and-effect reasoning explaining the fundamental 'why' and architectural trade-offs.

Structure:
# Executive Summary: {subtopic_title}
## 1. Core Invariants & Mental Model (In-depth narrative explaining the problem space and theoretical foundation)
## 2. Key Architecture & Mechanisms (Detailed prose detailing component interaction, protocols, or formulas)
## 3. Practical Applications & Production Relevance (Rich exposition of real-world use cases)
## 4. Synthesis of Discussions & Key Takeaways (Overview of conceptual insights)
## 5. Next Steps & Recommended Milestones

Curriculum Excerpts:
{"".join(context)[:5000] if context else "Foundational masterclass curriculum module."}

Output clean, publication-grade Markdown only."""

    summary_text = provider.generate(prompt, system_instruction=persona).strip()
    out_file = subtopic_dir / "SUMMARY.md"
    out_file.write_text(summary_text + "\n", encoding="utf-8")
    return summary_text

def regenerate_summary(query: str, provider_type: Optional[str] = None, model: Optional[str] = None) -> str:
    target = resolve_subtopic(query)
    if not target:
        raise ValueError(f"Topic '{query}' not found.")

    domain, cat, sub, sub_path = target
    persona = get_domain_persona(domain)
    subtopic_title = sub.replace("_", " ").title()

    # Ingest sequential lessons
    curriculum_parts = []
    for l in get_unit_lessons(sub_path)[:4]:
        p = Path(l["path"])
        if p.exists():
            curriculum_parts.append(f"--- {l['title']} ---\n" + p.read_text(encoding="utf-8")[:2000])

    labs_path = sub_path / "labs.md"
    if labs_path.exists():
        curriculum_parts.append("--- Operational Labs ---\n" + labs_path.read_text(encoding="utf-8")[:2500])

    # Ingest all session logs from user-AI discussions
    session_parts = []
    sessions_dir = sub_path / "sessions"
    if sessions_dir.exists():
        for sfile in sorted(sessions_dir.glob("*.md")):
            session_parts.append(f"--- Session: {sfile.name} ---\n" + sfile.read_text(encoding="utf-8")[:2000])

    prompt = f"""You are updating and regenerating the Executive SUMMARY.md for '{subtopic_title}'.
Domain: '{domain.replace('_', ' ').title()}' | Discipline: '{cat.replace('_', ' ').title()}'.

CRITICAL STYLE MANDATE:
- Write in continuous, articulate narrative book prose (O'Reilly / MIT Press textbook style).
- DO NOT write in lazy slide-deck bullet-point lists. Use full, flowing paragraphs.
- Synthesize both the formal curriculum knowledge AND all insights, student questions, and breakthroughs from the discussion logs into a cohesive, readable chapter.

Structure:
# Executive Summary: {subtopic_title}
## 1. Core Invariants & Mental Model (In-depth narrative explaining the foundational intuition and theory)
## 2. Key Architecture, Mechanisms & Derivations (Flowing paragraphs detailing technical design and protocols)
## 3. Practical Applications & Production Best Practices (Concrete real-world engineering context)
## 4. Discussion Insights & Breakthrough Takeaways (Synthesizing questions and answers explored with the AI tutor)
## 5. Mastery Review & Next Milestones

Curriculum Knowledge:
{"".join(curriculum_parts)[:4000]}

Discussion Session Transcripts:
{"".join(session_parts)[:4000] if session_parts else "No active discussion sessions logged yet."}

Output clean, publication-grade Markdown only."""

    provider = get_provider(provider_type=provider_type, model=model, domain=domain)
    summary_text = provider.generate(prompt, system_instruction=persona).strip()

    out_file = sub_path / "SUMMARY.md"
    out_file.write_text(summary_text + "\n", encoding="utf-8")

    # Git commit and push
    try:
        import subprocess
        subprocess.run(["git", "add", str(out_file)], check=True, cwd=str(WORKSPACE_ROOT), capture_output=True)
        subprocess.run(["git", "commit", "-m", f"summary({sub}): regenerate executive topic summary"], check=True, cwd=str(WORKSPACE_ROOT), capture_output=True)
        subprocess.run(["git", "push", "origin", "main"], check=False, cwd=str(WORKSPACE_ROOT), capture_output=True)
    except Exception:
        pass

    return summary_text
