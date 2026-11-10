"""
Progressive Multi-Level Lesson and Content Generator
Generates Beginner, Intermediate, and Advanced tiers for any subtopic
where each level strictly builds upon the knowledge of the previous level.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from .models import LLMProvider, get_provider
from .topic_manager import get_domain_persona

LEVELS = ["beginner", "intermediate", "advanced"]

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
    Generates Beginner, Intermediate, and Advanced tiers in subtopic_dir.
    Each tier contains FOUNDATION.md, LESSON.md, and LABS.md.
    """
    if not provider:
        provider = get_provider(domain=domain)

    system_instruction = get_domain_persona(domain)
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
                prompt = f"""Write the BEGINNER FOUNDATION guide for '{subtopic_title}'.
Domain: '{domain_title}' | Category: '{category_title}'.

Target Audience: Beginners with zero prior experience in this specific topic.
Goal: Build an unshakeable intuitive mental model and clear foundational vocabulary.

Structure:
# Beginner Foundation: {subtopic_title}
## 1. Everyday Intuition & First Principles (Simple, high-impact analogies explaining why this exists)
## 2. Foundational Vocabulary & Glossary (6-8 fundamental terms defined simply with examples)
## 3. Visual System Flow (Clean ASCII diagram and Mermaid flowchart of the basic workflow)
## 4. Common Beginner Misconceptions & Mental Traps
## 5. Socratic Discussion Starters (Basic questions to explore with your AI tutor)

Output publication-grade Markdown only."""
            elif lvl == "intermediate":
                prompt = f"""Write the INTERMEDIATE FOUNDATION guide for '{subtopic_title}'.
Domain: '{domain_title}' | Category: '{category_title}'.

Target Audience: Engineers and practitioners who already understand beginner concepts and need architectural depth.
Goal: Expand beyond the basics into system design, standard design patterns, and formal taxonomies.

Structure:
# Intermediate Foundation: {subtopic_title}
## 1. Architectural Mental Model (Assumes beginner concepts; focuses on production architecture)
## 2. Systems Taxonomy & Component Protocols (Standard interfaces, protocols, and data models)
## 3. Multi-Component Interaction Flow (Detailed ASCII and Mermaid sequence diagram)
## 4. Architectural Trade-offs & Production Pitfalls
## 5. Socratic Discussion Starters (Questions bridging architecture to low-level implementation)

Output publication-grade Markdown only."""
            else: # advanced
                prompt = f"""Write the ADVANCED FOUNDATION guide for '{subtopic_title}'.
Domain: '{domain_title}' | Category: '{category_title}'.

Target Audience: Staff Engineers, Security Researchers, and Theoretical Specialists.
Goal: Invariant analysis, formal mathematical/kernel frameworks, and extreme edge-case theory.

Structure:
# Advanced Foundation: {subtopic_title}
## 1. Theoretical Invariants & Formal Frameworks (Formal proofs, kernel or physical invariants)
## 2. Low-Level Invariant Taxonomy (Deep registers, memory models, hardware constraints, or axiomatic definitions)
## 3. Micro-Architecture & Concurrency Dynamics (Mermaid and ASCII state machines / cache / race condition diagrams)
## 4. Subtle Failure Modes & Boundary Conditions
## 5. Master Socratic Inquiries (Research-grade discussion questions)

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
                prompt = f"""Write the BEGINNER LESSON on '{subtopic_title}'.
Domain: '{domain_title}' | Category: '{category_title}'.

Target Audience: Beginners learning the fundamentals.
Goal: Clear, step-by-step technical breakdown of basic mechanics with simple working examples.

Structure:
# Beginner Technical Lesson: {subtopic_title}
## 1. Core Mechanics & Basic Principles (How it works under the hood at a fundamental level)
## 2. Step-by-Step Component Breakdown
## 3. First Working Implementation (Complete, clean, commented starter code or configuration)
## 4. What Can Go Wrong (Simple common mistakes and how to spot them)
## 5. Key Takeaways & Review Checklist

Output publication-grade Markdown only."""
            elif lvl == "intermediate":
                prompt = f"""Write the INTERMEDIATE LESSON on '{subtopic_title}'.
Domain: '{domain_title}' | Category: '{category_title}'.

Target Audience: Practitioners building production systems.
Goal: Production-grade implementation, standard design patterns, and operational robustness.

Structure:
# Intermediate Technical Lesson: {subtopic_title}
## 1. Production Architecture & Invariant Mechanisms
## 2. Data Structures, Protocols & Wire Formats
## 3. Full Production Implementation (Enterprise-grade, zero-placeholder code or manifests)
## 4. Performance Tuning, Scaling & Edge Cases
## 5. Architectural Summary & Production Checklist

Output publication-grade Markdown only."""
            else: # advanced
                prompt = f"""Write the ADVANCED TECHNICAL LESSON on '{subtopic_title}'.
Domain: '{domain_title}' | Category: '{category_title}'.

Target Audience: Principal Architects, Kernel Developers, and Security Researchers.
Goal: Deep low-level mechanics, CPU/kernel/hardware invariants, formal proofs, and extreme failure domains.

Structure:
# Advanced Technical Lesson: {subtopic_title}
## 1. Low-Level Internals & Deep Theory (Hardware registers, kernel memory, formal proofs)
## 2. Critical Data Structures, Byte-Level Encodings & Invariants
## 3. High-Value Advanced Code / Proof Implementation (Exhaustive, production-hardened)
## 4. Extreme Failure Domains, Race Conditions, Memory Corruption & Mitigation
## 5. Mastery Invariants & Executive Summary

Output publication-grade Markdown only."""

            content = provider.generate(prompt, system_instruction=system_instruction)
            lesson_path.write_text(content.strip() + "\n", encoding="utf-8")
            results[lvl]["lesson"] = True
        else:
            results[lvl]["lesson"] = False

        # 3. LABS.md
        labs_path = lvl_dir / "LABS.md"
        if not labs_path.exists() or force:
            if lvl == "beginner":
                prompt = f"""Write the BEGINNER HANDS-ON LAB for '{subtopic_title}'.
Domain: '{domain_title}' | Category: '{category_title}'.

Target: A gentle, guided hands-on lab verifying basic environment and executing first commands.

Structure:
# Beginner Hands-On Lab: {subtopic_title}
## Objective & Prerequisites
## Exercise 1: Environment Setup & Sanity Check (Exact commands to verify tools)
## Exercise 2: Your First Working Experiment (Step-by-step guided instructions with expected outputs)
## Exercise 3: Inspecting Basic State (Reading logs or simple outputs)
## Challenge Exercise (Simple self-test for beginners)

Output clean, executable Markdown only."""
            elif lvl == "intermediate":
                prompt = f"""Write the INTERMEDIATE HANDS-ON LAB for '{subtopic_title}'.
Domain: '{domain_title}' | Category: '{category_title}'.

Target: A realistic production deployment and operational troubleshooting lab.

Structure:
# Intermediate Operational Lab: {subtopic_title}
## Objective & Prerequisites
## Exercise 1: Advanced Environment Configuration & Diagnostics
## Exercise 2: Building & Deploying a Production Scenario (Multi-step operational workflow)
## Exercise 3: Troubleshooting Standard Failure Modes
## Challenge Exercise (Real-world operational scenario)

Output clean, executable Markdown only."""
            else: # advanced
                prompt = f"""Write the ADVANCED HANDS-ON LAB for '{subtopic_title}'.
Domain: '{domain_title}' | Category: '{category_title}'.

Target: A high-level debugging, fault injection, and low-level diagnostic lab.

Structure:
# Advanced Operational Lab: {subtopic_title}
## Objective & Deep Prerequisites
## Exercise 1: Low-Level State Inspection (Hardware/kernel registers, debuggers, memory dumps)
## Exercise 2: Advanced Scenario & Performance Stress Testing
## Exercise 3: Intentional Fault Injection & Root-Cause Crash Analysis
## Master Challenge Exercise (Research-grade problem)

Output clean, executable Markdown only."""

            content = provider.generate(prompt, system_instruction=system_instruction)
            labs_path.write_text(content.strip() + "\n", encoding="utf-8")
            results[lvl]["labs"] = True
        else:
            results[lvl]["labs"] = False

    return results
