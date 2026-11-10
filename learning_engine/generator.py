"""
Lesson and Content Generator
Generates Foundation, Lesson, and Lab guides for any subtopic using domain personas.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from .models import LLMProvider, get_provider
from .topic_manager import get_domain_persona

def generate_subtopic_content(
    domain: str,
    category: str,
    subtopic_id: str,
    subtopic_dir: Path,
    provider: Optional[LLMProvider] = None,
    force: bool = False
) -> Dict[str, bool]:
    """
    Generates FOUNDATION.md, LESSON.md, and LABS.md in subtopic_dir.
    Returns status dict indicating which files were generated or skipped.
    """
    if not provider:
        provider = get_provider()

    system_instruction = get_domain_persona(domain)
    subtopic_title = subtopic_id.replace("_", " ").title()
    domain_title = domain.replace("_", " ").title()

    results = {}

    # 1. FOUNDATION.md
    foundation_path = subtopic_dir / "FOUNDATION.md"
    if not foundation_path.exists() or force:
        prompt = f"""You are authoring a rigorous, comprehensive FOUNDATION textbook chapter on '{subtopic_title}'.
Domain: '{domain_title}' | Category: '{category.replace('_', ' ').title()}'.

REQUIREMENTS:
- Do NOT provide brief or superficial bullet points. Deliver an exhaustive, deep-dive conceptual breakdown.
- Ground everything in first principles, historical motivations, and underlying physical or architectural mechanisms.
- Provide a clean, detailed ASCII diagram and a Mermaid sequence or flowchart diagram illustrating internal workflows.
- Detail 5-8 foundational terms with full mathematical or system-level definitions.
- Analyze subtle misconceptions and mental traps that trip up practitioners.
- Provide 3 deep, provocative Socratic discussion questions.

Structure:
# Foundation: {subtopic_title}
## 1. Conceptual Mental Model (First principles, historical context, and fundamental paradigm shifts)
## 2. Essential Terminology & Taxonomy (Comprehensive architectural definitions)
## 3. Architecture & Core Workflow (Detailed ASCII and Mermaid diagrams with step-by-step dataflow)
## 4. Common Misconceptions & Mental Traps (Subtle edge cases and flawed mental models)
## 5. Socratic Discussion Starters (Advanced questions for deep Socratic exploration)

Output clean, exhaustive, publication-grade Markdown only."""
        content = provider.generate(prompt, system_instruction=system_instruction)
        foundation_path.write_text(content.strip() + "\n", encoding="utf-8")
        results["foundation"] = True
    else:
        results["foundation"] = False

    # 2. LESSON.md
    lesson_path = subtopic_dir / "LESSON.md"
    if not lesson_path.exists() or force:
        prompt = f"""You are authoring an exhaustive, production-grade technical LESSON on '{subtopic_title}'.
Domain: '{domain_title}' | Category: '{category.replace('_', ' ').title()}'.

REQUIREMENTS:
- Deliver deep technical exposition at the level of a Principal Systems Architect, Staff Security Researcher, or Mathematics Professor.
- Cover low-level mechanics: memory layouts, kernel subsystems, hardware registers, protocols, mathematical derivations, or data structures.
- Provide fully realized, complete production code, configurations, or mathematical proofs. NEVER use placeholders like '// TODO' or '...'.
- Exhaustively explore failure domains, edge cases, race conditions, memory bottlenecks, or counterexamples.
- Ensure 100% technical accuracy. Do not hallucinate or use hand-waving explanations.

Structure:
# In-Depth Technical Lesson: {subtopic_title}
## 1. Underlying Mechanics & Deep Theory
## 2. Architecture, Data Structures, Protocols & Invariants
## 3. Production Implementations & Concrete Real-World Code / Proofs
## 4. Failure Domains, Edge Cases & Performance Tradeoffs
## 5. Executive Summary & Key Takeaways

Output exhaustive, verified, publication-grade Markdown only."""
        content = provider.generate(prompt, system_instruction=system_instruction)
        lesson_path.write_text(content.strip() + "\n", encoding="utf-8")
        results["lesson"] = True
    else:
        results["lesson"] = False

    # 3. LABS.md
    labs_path = subtopic_dir / "LABS.md"
    if not labs_path.exists() or force:
        prompt = f"""You are authoring an exhaustive, hands-on operational LAB guide on '{subtopic_title}'.
Domain: '{domain_title}' | Category: '{category.replace('_', ' ').title()}'.

REQUIREMENTS:
- Provide concrete, fully runnable terminal commands, code scripts, or diagnostic workflows.
- Include explicit, realistic expected command outputs and state inspection steps.
- Include a dedicated fault injection and debugging exercise demonstrating how to diagnose failures.
- Provide challenging self-guided lab scenarios for testing with an AI mentor.

Structure:
# Hands-On Operational Lab: {subtopic_title}
## Objective & Lab Prerequisites
## Exercise 1: Exploration, Diagnostics & System State Inspection
## Exercise 2: Building, Configuring & Deploying a Production Scenario
## Exercise 3: Fault Injection, Failure Analysis & Debugging
## Challenge Lab: Independent Advanced Scenarios

Output clean, executable, publication-grade Markdown only."""
        content = provider.generate(prompt, system_instruction=system_instruction)
        labs_path.write_text(content.strip() + "\n", encoding="utf-8")
        results["labs"] = True
    else:
        results["labs"] = False

    return results
