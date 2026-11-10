"""
Lesson and Content Generator
Generates Beginner-to-Advanced Foundation, Lesson, and Lab guides for any subtopic
using domain personas and clustered Ollama/Gemini models.
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
    Generates FOUNDATION.md, LESSON.md, and LABS.md in subtopic_dir
    with an exhaustive Beginner -> Intermediate -> Advanced learning progression.
    """
    if not provider:
        provider = get_provider(domain=domain)

    system_instruction = get_domain_persona(domain)
    subtopic_title = subtopic_id.replace("_", " ").title()
    domain_title = domain.replace("_", " ").title()

    results = {}

    # 1. FOUNDATION.md (Beginner to Intermediate Ramp)
    foundation_path = subtopic_dir / "FOUNDATION.md"
    if not foundation_path.exists() or force:
        prompt = f"""You are authoring an exhaustive, publication-grade FOUNDATION chapter on '{subtopic_title}'.
Domain: '{domain_title}' | Category: '{category.replace('_', ' ').title()}'.

PEDAGOGICAL PROGRESSION:
Structure the content to bridge from complete beginner intuition to intermediate architectural understanding.

REQUIREMENTS:
- Do NOT provide brief summaries. Provide rich, deep technical and conceptual explanations.
- Ground everything in first principles, historical motivations, and real-world intuitive analogies.
- Include a comprehensive terminology table (6-8 terms with clear definitions and system context).
- Include both an ASCII diagram and a clean Mermaid sequence or flowchart diagram illustrating core workflows.
- Detail subtle misconceptions and mental traps that confuse learners.
- Provide 3 deep, provocative Socratic discussion questions.

Structure:
# Foundation: {subtopic_title}
## 1. Conceptual Mental Model (Beginner Intuition & First Principles)
## 2. Essential Terminology & Taxonomy (Foundational Glossary)
## 3. Architecture & Core Workflow (Detailed ASCII & Mermaid Diagrams)
## 4. Common Misconceptions & Mental Traps (Beginner & Intermediate Pitfalls)
## 5. Socratic Discussion Starters (Bridging to Intermediate Mastery)

Output exhaustive, publication-grade Markdown only."""
        content = provider.generate(prompt, system_instruction=system_instruction)
        foundation_path.write_text(content.strip() + "\n", encoding="utf-8")
        results["foundation"] = True
    else:
        results["foundation"] = False

    # 2. LESSON.md (Intermediate to Advanced Mastery)
    lesson_path = subtopic_dir / "LESSON.md"
    if not lesson_path.exists() or force:
        prompt = f"""You are authoring an exhaustive, production-grade technical LESSON on '{subtopic_title}'.
Domain: '{domain_title}' | Category: '{category.replace('_', ' ').title()}'.

PEDAGOGICAL PROGRESSION:
Take the student from intermediate operational mechanics through advanced low-level internals, mathematical proofs, and production invariants.

REQUIREMENTS:
- Deliver deep technical exposition at the level of a Principal Systems Architect, Staff Security Researcher, or Mathematics Professor.
- Low-Level Internals: Cover exact memory layouts, kernel subsystems, hardware registers, protocols, mathematical derivations, or data structures.
- Concrete Implementations: Provide fully realized, production-ready code, configurations, or proofs. NEVER use placeholders like '// TODO' or '...'.
- Advanced Invariants: Exhaustively analyze failure domains, edge cases, race conditions, memory bottlenecks, or counterexamples.
- 100% Technical Accuracy: Zero hallucinations, verified mechanisms only.

Structure:
# In-Depth Technical Lesson: {subtopic_title}
## 1. Underlying Mechanics & Intermediate Theory
## 2. Advanced Low-Level Architecture, Data Structures, Protocols & Invariants
## 3. Concrete Production Implementations & Real-World Code / Proofs
## 4. Advanced Failure Domains, Edge Cases & Performance Tradeoffs
## 5. Executive Summary & Key Takeaways for Advanced Mastery

Output exhaustive, publication-grade Markdown only."""
        content = provider.generate(prompt, system_instruction=system_instruction)
        lesson_path.write_text(content.strip() + "\n", encoding="utf-8")
        results["lesson"] = True
    else:
        results["lesson"] = False

    # 3. LABS.md (Progressive Hands-On Operational Lab)
    labs_path = subtopic_dir / "LABS.md"
    if not labs_path.exists() or force:
        prompt = f"""You are authoring an exhaustive, hands-on operational LAB guide on '{subtopic_title}'.
Domain: '{domain_title}' | Category: '{category.replace('_', ' ').title()}'.

PEDAGOGICAL PROGRESSION:
Guide the student through 4 progressive tiers of operational mastery:
Level 1: Beginner Exploration & Smoke Testing
Level 2: Intermediate Deployment & Practical Real-World Scenario
Level 3: Advanced Fault Injection, Failure Analysis & Root-Cause Debugging
Level 4: Master Challenge Exercises

REQUIREMENTS:
- Provide concrete, fully runnable terminal commands, code scripts, or diagnostic workflows.
- Include explicit, realistic expected command outputs and state inspection steps.
- The fault injection exercise must demonstrate how to diagnose failures using real system tools (logs, metrics, debuggers).
- Provide challenging self-guided lab scenarios for testing with an AI mentor.

Structure:
# Hands-On Operational Lab: {subtopic_title}
## Objective & Lab Prerequisites
## Lab Level 1 (Beginner): Exploration, Diagnostics & System State Inspection
## Lab Level 2 (Intermediate): Building, Configuring & Deploying a Production Scenario
## Lab Level 3 (Advanced): Fault Injection, Failure Analysis & Root-Cause Debugging
## Lab Level 4 (Master Challenge): Independent Advanced Scenarios

Output clean, executable, publication-grade Markdown only."""
        content = provider.generate(prompt, system_instruction=system_instruction)
        labs_path.write_text(content.strip() + "\n", encoding="utf-8")
        results["labs"] = True
    else:
        results["labs"] = False

    return results
