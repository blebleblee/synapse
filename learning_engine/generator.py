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
        prompt = f"""Write an essential FOUNDATION guide for the topic of '{subtopic_title}'.
This belongs to the '{domain_title}' domain under '{category.replace('_', ' ').title()}'.

Structure the document with:
# Foundation: {subtopic_title}
## 1. Conceptual Mental Model (Core intuition, analogies, and first principles)
## 2. Essential Terminology & Taxonomy (Definitions of 5-8 foundational terms)
## 3. Architecture & Core Workflow (Visual ASCII or Mermaid diagram illustrating the system flow)
## 4. Common Misconceptions & Mental Traps
## 5. Socratic Discussion Starters (3 deep questions for exploring this topic with your AI tutor)

Output clean, well-formatted Markdown only."""
        content = provider.generate(prompt, system_instruction=system_instruction)
        foundation_path.write_text(content.strip() + "\n", encoding="utf-8")
        results["foundation"] = True
    else:
        results["foundation"] = False

    # 2. LESSON.md
    lesson_path = subtopic_dir / "LESSON.md"
    if not lesson_path.exists() or force:
        prompt = f"""Write an exhaustive, complete technical LESSON on the topic of '{subtopic_title}'.
This belongs to the '{domain_title}' domain under '{category.replace('_', ' ').title()}'.

Structure the document with:
# In-Depth Technical Lesson: {subtopic_title}
## 1. Underlying Mechanics & Deep Theory
## 2. Architecture, Data Structures, or Physical Laws
## 3. Production Implementations / Real-World Code or Manifests (No placeholders, fully realized examples)
## 4. Failure Domains, Edge Cases & Performance Tradeoffs
## 5. Executive Summary & Key Takeaways

Output clean, well-formatted Markdown only."""
        content = provider.generate(prompt, system_instruction=system_instruction)
        lesson_path.write_text(content.strip() + "\n", encoding="utf-8")
        results["lesson"] = True
    else:
        results["lesson"] = False

    # 3. LABS.md
    labs_path = subtopic_dir / "LABS.md"
    if not labs_path.exists() or force:
        prompt = f"""Write a hands-on, operational LAB guide for practicing '{subtopic_title}'.
This belongs to the '{domain_title}' domain under '{category.replace('_', ' ').title()}'.

Structure the document with:
# Hands-On Operational Lab: {subtopic_title}
## Objective & Prerequisites
## Exercise 1: Exploration & System State Inspection (Explicit verification commands and expected outputs)
## Exercise 2: Building & Deploying / Modeling Scenario (Step-by-step interactive workflow)
## Exercise 3: Fault Injection, Failure Analysis & Debugging
## Challenge Lab: Independent Problem for Socratic Discussion with the AI Tutor

Output clean, well-formatted Markdown with exact shell commands or actionable steps."""
        content = provider.generate(prompt, system_instruction=system_instruction)
        labs_path.write_text(content.strip() + "\n", encoding="utf-8")
        results["labs"] = True
    else:
        results["labs"] = False

    return results
