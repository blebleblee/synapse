"""
Curriculum Generation Engine (Progressive 3-Tier Model)
Generates Beginner -> Intermediate -> Advanced content units.
Enforces human, narrative book-like prose (O'Reilly / MIT Press textbook style)
and strictly bans lazy slide-deck bullet point lists.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from .models import get_provider, LLMProvider
from .topic_manager import get_domain_persona, LEVELS

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

BOOK_STYLE_DIRECTIVE = """CRITICAL STYLE & TONE DIRECTIVE:
- This is a masterclass textbook chapter, NOT a slide-deck presentation or outline.
- STRICTLY AVOID endless bullet-point lists. Write in rich, articulated, flowing paragraphs of narrative prose.
- Connect concepts through deep exposition, historical context, and cause-and-effect mechanical reasoning.
- Write like an authoritative technical author (e.g. O'Reilly, MIT Press, No Starch Press): articulate, human, intellectually rigorous, and engaging.
- Use lists ONLY when providing sequential step-by-step CLI commands in labs or parameter reference tables. All conceptual and architectural explanations must be written in full narrative prose."""

def generate_subtopic_content(
    domain: str,
    category: str,
    subtopic_id: str,
    subtopic_dir: Path,
    provider: Optional[LLMProvider] = None,
    force: bool = False,
    level: Optional[str] = None
) -> Dict[str, Any]:
    if not provider:
        provider = get_provider(domain=domain)

    system_instruction = get_domain_persona(domain) + "\n\n" + BOOK_STYLE_DIRECTIVE
    subtopic_title = subtopic_id.replace("_", " ").title()
    domain_title = domain.replace("_", " ").title()
    category_title = category.replace("_", " ").title()

    results = {}
    target_levels = [level.lower()] if level and level.lower() in LEVELS else LEVELS

    for lvl in target_levels:
        lvl_dir = subtopic_dir / lvl
        lvl_dir.mkdir(parents=True, exist_ok=True)
        results[lvl] = {}

        # 1. FOUNDATION.md
        foundation_path = lvl_dir / "FOUNDATION.md"
        if not foundation_path.exists() or force:
            if lvl == "beginner":
                prompt = f"""Write the BEGINNER FOUNDATION textbook chapter for '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Beginners seeking an intuitive, unshakeable mental model.
Goal: Build intuition from first principles using compelling narrative exposition and visual diagrams.

Structure:
# Beginner Foundation: {subtopic_title}
## 1. The Core Mental Model & First Principles (An engaging narrative explaining why this concept exists and what fundamental problem it solves)
## 2. Foundational Architecture & Mechanics (Flowing paragraphs detailing how components interact)
## 3. Visual System Flow (Clean ASCII diagram and Mermaid flowchart of the basic workflow)
## 4. Subtle Misconceptions & Mental Traps (Common false assumptions analyzed in depth)
## 5. Socratic Discussion Inquiries (Deep conceptual questions to explore with your AI mentor)

Remember: Write in continuous, articulate book prose. Avoid bullet point lists for explanations.
Output publication-grade Markdown only."""
            elif lvl == "intermediate":
                prompt = f"""Write the INTERMEDIATE FOUNDATION textbook chapter for '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Practicing engineers and scholars expanding into systems architecture and production design.
Goal: Deepen the mental model into multi-component interaction, formal taxonomies, and architectural trade-offs.

Structure:
# Intermediate Foundation: {subtopic_title}
## 1. Architectural Invariants & Design Principles (Deep narrative prose exploring production architecture)
## 2. Systems Protocols, Data Contracts & Wire Formats (Exposition of standard interfaces and protocols)
## 3. Multi-Component Interaction Flow (Detailed ASCII and Mermaid sequence diagram)
## 4. Architectural Trade-offs & Production Failure Modes (Prose analysis of failure domains)
## 5. Socratic Discussion Inquiries (Bridging high-level architecture to low-level implementation)

Remember: Write in continuous, articulate book prose. Avoid bullet point lists for explanations.
Output publication-grade Markdown only."""
            else: # advanced
                prompt = f"""Write the ADVANCED FOUNDATION textbook chapter for '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Principal Architects, Kernel Developers, and Security Researchers.
Goal: Graduate-level mathematical proofs, hardware invariants, CPU execution semantics, and formal state machines.

Structure:
# Advanced Foundation: {subtopic_title}
## 1. Formal Mathematical Axioms & Hardware Invariants (Rigorous narrative grounding)
## 2. Kernel & CPU Execution Semantics (Deep exposition of memory models and synchronization)
## 3. State Machine & Execution Invariants (Mermaid state diagram and ASCII register/memory layout)
## 4. Boundary Conditions & Catastrophic Failure Modes
## 5. Research-Grade Socratic Inquiries

Remember: Write in continuous, articulate book prose. Avoid bullet point lists for explanations.
Output publication-grade Markdown only."""

            content = provider.generate(prompt, system_instruction=system_instruction)
            foundation_path.write_text(content.strip() + "\n", encoding="utf-8")
            results[lvl]["foundation"] = True
        else:
            results[lvl]["foundation"] = False

        # 2. LESSON.md
        lesson_path = lvl_dir / "LESSON.md"
        if not lesson_path.exists() or force:
            if lvl == "beginner":
                prompt = f"""Write the BEGINNER TECHNICAL LESSON on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Beginners learning the concrete mechanics.
Goal: In-depth technical breakdown written as an authoritative book chapter with complete working code or configuration.

Structure:
# Beginner Technical Lesson: {subtopic_title}
## 1. Core Mechanics & Execution Flow (How it operates under the hood, explained in rich paragraphs)
## 2. In-Depth Component Breakdown (Narrative exploration of each mechanism)
## 3. Working Implementation (Exhaustive, fully documented, compilable starter code or configuration)
## 4. Diagnosis & Common Pitfalls (Detailed prose explaining common bugs and remediation)
## 5. Conceptual Synthesis & Master Takeaways

Remember: Write in continuous, articulate book prose. Avoid bullet point lists for explanations.
Output publication-grade Markdown only."""
            elif lvl == "intermediate":
                prompt = f"""Write the INTERMEDIATE TECHNICAL LESSON on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Practitioners building enterprise systems.
Goal: Production-grade implementation, architectural invariants, and high-load performance characteristics.

Structure:
# Intermediate Technical Lesson: {subtopic_title}
## 1. Production Mechanics & Invariant Guarantees (Rigorous narrative exposition)
## 2. Protocol Internals, Data Layout & Wire Invariants
## 3. Complete Production Implementation (Enterprise-grade, zero-placeholder code or manifests)
## 4. Performance Tuning, Latency Profiles & Boundary Conditions
## 5. Architectural Synthesis & Production Playbook

Remember: Write in continuous, articulate book prose. Avoid bullet point lists for explanations.
Output publication-grade Markdown only."""
            else: # advanced
                prompt = f"""Write the ADVANCED TECHNICAL LESSON on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Principal Engineers, Kernel Specialists, and Systems Researchers.
Goal: Low-level mechanics, hardware registers, kernel memory management, formal proofs, and race condition mitigations.

Structure:
# Advanced Technical Lesson: {subtopic_title}
## 1. Low-Level Internals & Theoretical Grounding (In-depth prose on hardware registers, kernel memory, or proofs)
## 2. Critical Data Structures, Byte-Level Encodings & Memory Layouts
## 3. Hardened Production Code / Formal Proof (Exhaustive, fully implemented with zero placeholders)
## 4. Extreme Failure Domains, Race Conditions & Memory Safety Analysis
## 5. Invariant Synthesis & Systems Summary

Remember: Write in continuous, articulate book prose. Avoid bullet point lists for explanations.
Output publication-grade Markdown only."""

            content = provider.generate(prompt, system_instruction=system_instruction)
            lesson_path.write_text(content.strip() + "\n", encoding="utf-8")
            results[lvl]["lesson"] = True
        else:
            results[lvl]["lesson"] = False

        # 3. LABS.md
        labs_path = lvl_dir / "LABS.md"
        if not labs_path.exists() or force:
            prompt = f"""Write the {lvl.upper()} HANDS-ON OPERATIONAL LAB for '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Hands-on practitioner at {lvl} level.
Goal: Concrete terminal lab with real commands, step-by-step verification, failure reproduction, and diagnostic analysis.

Structure:
# Hands-On Operational Lab: {subtopic_title} ({lvl.upper()})
## Objective & Prerequisites (Exact tools, dependencies, and environment setup)
## Exercise 1: Environment Verification & Basic State Inspection
## Exercise 2: Hands-On Implementation & Live Execution
## Exercise 3: Deliberate Failure Injection & Diagnostic Isolation
## Exercise 4: Clean Up & Verification
## Socratic Challenge Questions (Thought experiments testing deep operational understanding)

Rules: Provide full, runnable commands, configurations, or manifests with zero placeholders.
Output publication-grade Markdown only."""

            content = provider.generate(prompt, system_instruction=system_instruction)
            labs_path.write_text(content.strip() + "\n", encoding="utf-8")
            results[lvl]["labs"] = True
        else:
            results[lvl]["labs"] = False

    return results
