"""
Curriculum Generation Engine (Progressive 3-Tier Model)
Generates Beginner -> Intermediate -> Advanced content units.
Enforces human, narrative book-like prose (O'Reilly / MIT Press textbook style)
and strictly bans lazy slide-deck bullet point lists.
"""

import time
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from .models import OllamaCluster, OllamaProvider, get_provider, LLMProvider, validate_generation_output
from .topic_manager import get_domain_persona, LEVELS

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

BOOK_STYLE_DIRECTIVE = """CRITICAL STYLE & TONE DIRECTIVE:
- This is a masterclass textbook chapter, NOT a slide-deck presentation or outline.
- STRICTLY AVOID endless bullet-point lists. Write in rich, articulated, flowing paragraphs of narrative prose.
- Connect concepts through deep exposition, historical context, and cause-and-effect mechanical reasoning.
- Write like an authoritative technical author (e.g. O'Reilly, MIT Press, No Starch Press): articulate, human, intellectually rigorous, and engaging.
- Use lists ONLY when providing sequential step-by-step CLI commands in labs or parameter reference tables. All conceptual and architectural explanations must be written in full narrative prose."""

def generate_topic_parallel(
    domain: str,
    category: str,
    subtopic_id: str,
    subtopic_dir: Path,
    force: bool = False,
    workers: Optional[List[Tuple[str, str, OllamaProvider]]] = None
) -> Dict[str, Any]:
    """
    Generates a sequential multi-lesson masterclass curriculum unit across all active
    Ollama cluster engines in parallel:
      - Worker 1: Foundations & System Invariants
      - Worker 2: Core Architecture & Memory Subsystems
      - Worker 3: Internal Mechanics & Reliability
      - Worker 4: Operational Verification Labs
    """
    subtopic_dir.mkdir(parents=True, exist_ok=True)
    subtopic_title = subtopic_id.replace("_", " ").title()
    domain_title = domain.replace("_", " ").title()
    category_title = category.replace("_", " ").title()
    persona = get_domain_persona(domain)
    system_instruction = persona + "\n\n" + BOOK_STYLE_DIRECTIVE

    if workers is None:
        cluster = OllamaCluster()
        workers = cluster.get_parallel_workers()

    modules = [
        {
            "filename": "lesson_01_foundations_and_invariants.md",
            "title": f"Lesson 1: Foundations & System Invariants",
            "prompt": f"""Write Lesson 1 (Foundations & Invariants) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Senior software engineers, systems programmers, and infrastructure architects.
Goal: Establish unshakeable theoretical grounding, core invariants, and architecture.

Structure:
# Lesson 1: Foundations & System Invariants

## Curriculum Roadmap
(Provide a clear outline of the curriculum modules)

## 1. First-Principles Mental Model & Problem Space
(Deep narrative exposition on why this technology exists, what physics or systems trade-offs it solves)

## 2. Fundamental System Guarantees & Non-Negotiable Invariants
(Rigorous mathematical/architectural guarantees)

## 3. High-Level Process & Component Architecture
(Include a clean Mermaid diagram representing the core data and control flow)

Remember: Write in rich, continuous book prose like an O'Reilly or MIT Press author. Avoid lazy bullet point lists.
Output publication-grade Markdown only."""
        },
        {
            "filename": "lesson_02_architecture_and_mechanics.md",
            "title": f"Lesson 2: Core Architecture & Memory Subsystems",
            "prompt": f"""Write Lesson 2 (Core Architecture & Mechanics) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Systems programmers and engineers needing deep mechanical understanding.
Goal: Dissect process models, memory allocation, byte-level data structures, and the critical execution path.

Structure:
# Lesson 2: Core Architecture & Memory Subsystems

## 1. Process, Threading & Concurrency Architecture
(Flowing narrative on how processes/threads are scheduled, isolated, and coordinated)

## 2. Memory Subsystems & Buffer Management
(Page layouts, cache hierarchies, replacement algorithms, and shared memory segments)

## 3. Data Structures & On-Disk Binary Layouts
(Detailed ASCII layouts and bitwise field explanations)

## 4. The Critical Read/Write Execution Lifecycle
(End-to-end trace of a request through the kernel and subsystem)

Remember: Write in rich, continuous book prose. Avoid superficial summaries.
Output publication-grade Markdown only."""
        },
        {
            "filename": "lesson_03_deep_dive_and_concurrency.md",
            "title": f"Lesson 3: Advanced Internal Mechanics & Reliability",
            "prompt": f"""Write Lesson 3 (Internal Mechanics & Reliability) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Principal engineers and database/infrastructure architects.
Goal: In-depth analysis of concurrency control, crash recovery, state machines, and high availability.

Structure:
# Lesson 3: Advanced Internal Mechanics & Reliability

## 1. Concurrency Control, Lock Scheduling & Conflict Graphs
(Multi-version concurrency, lock-free queues, latches, and deadlock detection)

## 2. Write-Ahead Logging & Crash Recovery State Machines
(Recovery protocols, checkpointing invariants, redo/undo logging mechanics)

## 3. Compaction, Eviction & Garbage Collection Engines
(Tuples freezing, background worker loops, bloat prevention)

## 4. Failure Domains & Byzantine Edge Cases
(Disk corruption, partial writes, network partitions, and mitigations)

Remember: Write in rich, continuous book prose with technical depth.
Output publication-grade Markdown only."""
        },
        {
            "filename": "labs.md",
            "title": f"Operational Verification Labs",
            "prompt": f"""Write the complete Operational Verification Lab guide for '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Hands-on practitioner and systems engineer.
Goal: Step-by-step diagnostic verification using real Linux/BSD CLI commands, inspection tools, and reproduction scripts.

Structure:
# Operational Verification Labs: {subtopic_title}

## Objective & Environment Setup
(Required CLI tools, packages, kernel settings, and environment variables)

## Exercise 1: Live State & Internal Memory Inspection
(Exact runnable CLI commands to inspect memory, buffers, processes, or metrics)

## Exercise 2: Benchmarking & Saturation Profiling
(Real benchmark commands, load generation, and latency profiling)

## Exercise 3: Fault Injection & Recovery Analysis
(Simulating sudden failure, packet loss, or corruption, and inspecting recovery logs)

## Diagnostic Cheat Sheet & Verification Checklist
(Table of essential CLI commands and operational flags)

Rules: Provide full, executable commands and configurations with zero placeholders.
Output publication-grade Markdown only."""
        }
    ]

    tasks_to_run = []
    results = {}

    for mod in modules:
        out_path = subtopic_dir / mod["filename"]
        if not out_path.exists() or force:
            tasks_to_run.append(mod)
        else:
            results[mod["filename"]] = False

    if not tasks_to_run:
        return results

    if workers and len(workers) > 0:
        worker_cycle = itertools.cycle(workers)
        job_pairs = [(mod, next(worker_cycle)) for mod in tasks_to_run]

        def run_module_job(job):
            mod_item, (w_host, w_model, w_provider) = job
            try:
                t0 = time.time()
                content = w_provider.generate(mod_item["prompt"], system_instruction=system_instruction)
                validated = validate_generation_output(content)
                target_file = subtopic_dir / mod_item["filename"]
                target_file.write_text(validated.strip() + "\n", encoding="utf-8")
                elapsed = time.time() - t0
                return mod_item["filename"], True, f"{w_host} ({w_model}) in {elapsed:.1f}s", None
            except Exception as e:
                return mod_item["filename"], False, f"{w_host} ({w_model})", str(e)

        with ThreadPoolExecutor(max_workers=min(len(workers), len(tasks_to_run))) as executor:
            future_to_mod = {executor.submit(run_module_job, job): job[0]["filename"] for job in job_pairs}
            for fut in as_completed(future_to_mod):
                fname, ok, worker_info, err = fut.result()
                results[fname] = ok
    else:
        # Fallback to single provider
        provider = get_provider(domain=domain)
        for mod in tasks_to_run:
            try:
                content = provider.generate(mod["prompt"], system_instruction=system_instruction)
                validated = validate_generation_output(content)
                (subtopic_dir / mod["filename"]).write_text(validated.strip() + "\n", encoding="utf-8")
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
    level: Optional[str] = None
) -> Dict[str, Any]:
    # Default to parallel multi-lesson cluster generation
    if not level:
        return generate_topic_parallel(domain, category, subtopic_id, subtopic_dir, force=force)

    # Legacy 3-tier generation if level is explicitly specified
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
