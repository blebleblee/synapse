"""
Curriculum Generation Engine (Progressive 3-Tier Model)
Generates Beginner -> Intermediate -> Advanced content units.
Enforces human, narrative book-like prose (O'Reilly / MIT Press textbook style)
and strictly bans lazy slide-deck bullet point lists.
"""

import time
import itertools
import re
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from .models import OllamaCluster, OllamaProvider, get_provider, LLMProvider, validate_generation_output
from .topic_manager import get_domain_persona, LEVELS

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

def purge_legacy_topic_files(topic_dir: Path):
    """
    Purges legacy uppercase markdown files (FOUNDATION.md, LESSON.md, LABS.md, SUMMARY.md),
    old leveled files (beginner.md, intermediate.md, advanced.md), old session directories,
    and legacy numbered subdirectories (01_*, 02_*).
    """
    if not topic_dir.exists():
        return

    legacy_files = [
        "FOUNDATION.md", "LESSON.md", "LABS.md", "SUMMARY.md",
        "foundation.md", "lesson.md", "summary.md",
        "beginner.md", "intermediate.md", "advanced.md",
        "flashcards.csv"
    ]
    for fname in legacy_files:
        p = topic_dir / fname
        if p.exists() and p.is_file():
            try:
                p.unlink()
            except Exception:
                pass

    sessions_dir = topic_dir / "sessions"
    if sessions_dir.exists() and sessions_dir.is_dir():
        shutil.rmtree(sessions_dir, ignore_errors=True)

    for sub in list(topic_dir.iterdir()):
        if sub.is_dir() and re.match(r"^\d{2}_", sub.name):
            shutil.rmtree(sub, ignore_errors=True)

BOOK_STYLE_DIRECTIVE = """CRITICAL STYLE & TONE DIRECTIVE:
- This is a masterclass textbook chapter, NOT a slide-deck presentation or outline.
- STRICTLY AVOID endless bullet-point lists. Write in rich, articulated, flowing paragraphs of narrative prose.
- Connect concepts through deep exposition, historical context, and cause-and-effect mechanical reasoning.
- Write like an authoritative technical author (e.g. O'Reilly, MIT Press, No Starch Press): articulate, human, intellectually rigorous, and engaging.
- Use lists ONLY when providing sequential step-by-step CLI commands in labs or parameter reference tables. All conceptual and architectural explanations must be written in full narrative prose."""

def build_topic_modules(domain: str, category: str, subtopic_id: str, subtopic_title: str) -> List[Dict[str, str]]:
    """
    Constructs domain-adaptive, subject-aware masterclass lesson prompts and hands-on lab templates.
    Dynamically aligns technical depth, real-world tools, and verification exercises with the discipline:
      - AI & ML: Python 3.11+, PyTorch/HuggingFace/Ollama pipelines, tokenizers, evaluations, benchmarks
      - Security: Logic analyzers, minicom, flashrom, openocd, binwalk, bus sniffing, glitching
      - Infrastructure: bpftool, kubectl, iproute2, tcpdump, perf, eBPF maps, kernel tracing
      - Databases: psql, pg_waldump, page inspection, buffer pools, MVCC, lock graphs
      - Software: Cargo, rustc, GDB, Valgrind/ASan, AST/IR compilation, thread contention
    """
    domain_title = domain.replace("_", " ").title()
    category_title = category.replace("_", " ").title()
    cat_lower = category.lower()

    # 1. AI, Machine Learning, LLMs, Data Science
    if any(k in cat_lower for k in ["ai", "machine_learning", "deep_learning", "data_analysis", "data_visualisation", "mlops", "rag", "vibe_coding", "prompt"]):
        return [
            {
                "filename": "lesson_01_foundations_and_invariants.md",
                "title": f"Lesson 1: Foundations & Mathematical Formulation",
                "prompt": f"""Write Lesson 1 (Foundations & Invariants) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Senior machine learning engineers, AI researchers, and systems architects.
Goal: Establish unshakeable theoretical grounding, problem space formulation, and mathematical invariants.

Structure:
# Lesson 1: Foundations & Mathematical Formulation

## Curriculum Roadmap
(Provide a clear outline of the curriculum modules)

## 1. First-Principles Intuition & The Problem Space
(Deep narrative exposition on why this AI/ML technique exists, what fundamental limitations or computational trade-offs it solves)

## 2. Mathematical Formalization & Core Invariants
(Rigorous mathematical formulation, loss/objective equations, optimization bounds, and non-negotiable guarantees)

## 3. High-Level Pipeline & Architecture Dataflow
(Include a clean Mermaid diagram representing the model pipeline, tensor transformations, or agentic control flow)

Remember: Write in rich, continuous book prose like an O'Reilly or MIT Press author. Avoid lazy bullet point lists.
Output publication-grade Markdown only."""
            },
            {
                "filename": "lesson_02_architecture_and_mechanics.md",
                "title": f"Lesson 2: Core Architecture & Algorithmic Mechanics",
                "prompt": f"""Write Lesson 2 (Core Architecture & Algorithmic Mechanics) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Machine learning engineers and AI practitioners needing deep mechanical understanding.
Goal: Dissect representations, algorithm mechanics, layer operations, and runtime data structures.

Structure:
# Lesson 2: Core Architecture & Algorithmic Mechanics

## 1. Internal Representations & Data Structures
(Vector embeddings, token structures, attention matrices, or parameter layouts with ASCII diagrams)

## 2. Forward Pass & Algorithmic Execution Lifecycle
(Step-by-step mathematical trace of inference/execution through the architecture)

## 3. Memory Footprint & Computational Complexity
(KV-cache scaling, parameter memory allocation, computational complexity O(...) bounds, and hardware accelerator mapping)

Remember: Write in rich, continuous book prose. Avoid superficial summaries.
Output publication-grade Markdown only."""
            },
            {
                "filename": "lesson_03_deep_dive_and_concurrency.md",
                "title": f"Lesson 3: Optimization, Scaling & Failure Modes",
                "prompt": f"""Write Lesson 3 (Optimization, Scaling & Failure Modes) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Lead AI engineers and production systems architects.
Goal: In-depth analysis of training/inference optimization, scaling laws, drift domains, and failure mitigation.

Structure:
# Lesson 3: Optimization, Scaling & Failure Modes

## 1. Training Dynamics & Convergence Invariants
(Gradient stability, loss landscape geometry, learning rate mechanics, and regularization)

## 2. Production Latency & Serving Optimization
(Quantization trade-offs, batching strategies, speculative decoding, and caching)

## 3. Failure Modes & Edge Case Domains
(Distribution drift, catastrophic forgetting, hallucination failure surfaces, and guardrail architectures)

Remember: Write in rich, continuous book prose with technical depth.
Output publication-grade Markdown only."""
            },
            {
                "filename": "labs.md",
                "title": f"Operational Verification Labs",
                "prompt": f"""Write the complete Operational Verification Lab guide for '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Hands-on AI engineer and practitioner.
Goal: Concrete hands-on lab using real, executable Python scripts, API harnesses, evaluation pipelines, and verification commands. Do NOT output generic Linux kernel or low-level sysctl/modprobe commands.

Structure:
# Operational Verification Labs: {subtopic_title}

## Objective & Environment Setup
(Required Python 3.11+ environment, packages e.g. PyTorch, HuggingFace, NumPy, Scikit-learn, Ollama, or Polars, and API configuration)

## Exercise 1: Hands-On Implementation & Pipeline Execution
(Complete, runnable Python script implementing the core prompt/model/algorithm for this topic with zero placeholders)

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking
(Real benchmarking code measuring accuracy, latency distributions, token costs, or convergence curves)

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation
(Reproducing failure modes, testing edge cases, and implementing guardrails or error handling)

## Verification Checklist & Quick Reference Cheat Sheet
(Table of essential Python methods, parameters, and verification flags for this topic)

Rules: Provide full, executable Python code and CLI commands with zero placeholders.
Output publication-grade Markdown only."""
            }
        ]

    # 2. Security & Hardware Hacking
    elif any(k in cat_lower for k in ["security", "hardware_hacking", "reverse_engineering", "cryptography", "exploit"]):
        return [
            {
                "filename": "lesson_01_foundations_and_invariants.md",
                "title": f"Lesson 1: Foundations, Attack Surfaces & Physical Invariants",
                "prompt": f"""Write Lesson 1 (Foundations & Physical Invariants) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Hardware security researchers, embedded engineers, and offensive security practitioners.
Goal: Establish physical signaling models, attack surfaces, pinout mechanics, and security boundaries.

Structure:
# Lesson 1: Foundations, Attack Surfaces & Physical Invariants

## Curriculum Roadmap
(Provide a clear outline of the curriculum modules)

## 1. Physical Signal Theory & Hardware Problem Space
(Deep exposition on signaling physics, voltage logic levels, pull-up/pull-down resistor networks, and why physical security fails)

## 2. Threat Modeling & Non-Negotiable Invariants
(Root-of-trust, memory isolation boundaries, and cryptographic invariants)

## 3. High-Level Bus Topology & Interface Architecture
(Include a clean Mermaid diagram representing bus communication between master, target chip, and analyzer)

Remember: Write in rich, continuous book prose. Avoid lazy bullet point lists.
Output publication-grade Markdown only."""
            },
            {
                "filename": "lesson_02_architecture_and_mechanics.md",
                "title": f"Lesson 2: Protocol Mechanics & Bus Framing",
                "prompt": f"""Write Lesson 2 (Protocol Mechanics & Bus Framing) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Embedded security engineers and hardware reverse engineers.
Goal: Dissect frame structures, clocking edges, register maps, and signal transactions.

Structure:
# Lesson 2: Protocol Mechanics & Bus Framing

## 1. Clock Synchronization & Signal Timing Diagrams
(Baud rate derivation, clock polarities, setup/hold times with detailed ASCII timing diagrams)

## 2. Frame Architecture & Bit-Level Encodings
(Start/stop bits, packet headers, register address bytes, and parity encodings)

## 3. Bus Transaction Lifecycle
(End-to-end trace of a read/write command across the physical wire)

Remember: Write in rich, continuous book prose. Avoid superficial summaries.
Output publication-grade Markdown only."""
            },
            {
                "filename": "lesson_03_deep_dive_and_concurrency.md",
                "title": f"Lesson 3: Exploitation Primitives, Glitching & Hardening",
                "prompt": f"""Write Lesson 3 (Exploitation Primitives & Defense) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Senior exploit developers and embedded hardware architects.
Goal: Deep dive into firmware dumping, fault injection (voltage/clock glitching), and hardware counter-measures.

Structure:
# Lesson 3: Exploitation Primitives, Glitching & Hardening

## 1. Firmware Extraction & Memory Carving Mechanics
(Bypassing readout protections, dumping SPI flash/EEPROM, and binary analysis)

## 2. Fault Injection & Glitch State Machines
(Precision timing, clock jitter, voltage droop simulation, and bypassing instruction verification)

## 3. Hardware Countermeasures & Defensive Invariants
(Active shielding, tamper detection meshes, encrypted bus interfaces, and secure boot verification)

Remember: Write in rich, continuous book prose with technical depth.
Output publication-grade Markdown only."""
            },
            {
                "filename": "labs.md",
                "title": f"Operational Verification Labs",
                "prompt": f"""Write the complete Operational Verification Lab guide for '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Hands-on hardware hacker and penetration tester.
Goal: Concrete laboratory exercises using real hardware tools, bus sniffers, logic analyzers, and extraction commands.

Structure:
# Operational Verification Labs: {subtopic_title}

## Objective & Lab Bench Setup
(Required hardware/simulation tools: USB-UART bridge, logic analyzer, minicom, sigrok-cli, openocd, flashrom, binwalk, gdb-multiarch)

## Exercise 1: Live Hardware Probing & Signal Capture
(Exact CLI commands and scripts to identify pinouts, detect baud rates, and capture traffic)

## Exercise 2: Bus Sniffing, Register Inspection & Memory Dumping
(Extracting register states, reading flash chips, or dumping raw binary firmware)

## Exercise 3: Fault Simulation & Exploit Verification
(Simulating fault timing, voltage drops, or injecting exploit vectors)

## Hardware Security Checklist & Diagnostic Cheat Sheet
(Table of essential CLI commands, pinout rules, and verification flags)

Rules: Provide full, executable commands and configurations with zero placeholders.
Output publication-grade Markdown only."""
            }
        ]

    # 3. Systems & Cloud Infrastructure (eBPF, Kubernetes, Linux Kernel, SRE)
    elif any(k in cat_lower for k in ["infrastructure", "ebpf", "kubernetes", "networking", "linux_kernel", "os_theory", "sre"]):
        return [
            {
                "filename": "lesson_01_foundations_and_invariants.md",
                "title": f"Lesson 1: Foundations & Kernel/System Invariants",
                "prompt": f"""Write Lesson 1 (Foundations & Invariants) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Systems programmers, kernel engineers, and cloud infrastructure architects.
Goal: Establish theoretical grounding, kernel boundaries, and non-negotiable system invariants.

Structure:
# Lesson 1: Foundations & Kernel/System Invariants

## Curriculum Roadmap
(Provide a clear outline of the curriculum modules)

## 1. First-Principles Problem Space & Execution Boundaries
(Deep exposition on user vs kernel space, syscall overheads, or distributed consensus boundaries)

## 2. Fundamental System Guarantees & Non-Negotiable Invariants
(Safety constraints, memory isolation, or consistency guarantees)

## 3. High-Level Process & Subsystem Architecture
(Include a clean Mermaid diagram representing the subsystem, execution flow, or control plane topology)

Remember: Write in rich, continuous book prose. Avoid lazy bullet point lists.
Output publication-grade Markdown only."""
            },
            {
                "filename": "lesson_02_architecture_and_mechanics.md",
                "title": f"Lesson 2: Core Architecture & Memory/Execution Models",
                "prompt": f"""Write Lesson 2 (Core Architecture & Mechanics) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Systems programmers needing deep mechanical understanding.
Goal: Dissect process models, memory allocation, byte-level data structures, and the critical execution path.

Structure:
# Lesson 2: Core Architecture & Memory/Execution Models

## 1. Process, Threading & Execution Lifecycles
(Scheduling mechanics, ring buffers, eBPF bytecode execution, or control loops)

## 2. Memory Subsystems & Buffer Management
(Page layouts, socket buffers, shared memory, or CRD reconciliation cache)

## 3. Data Structures & On-Disk/In-Kernel Binary Layouts
(Detailed ASCII layouts and bitwise field explanations)

## 4. The Critical Execution Lifecycle
(End-to-end trace of a request, packet, or state transition through the system)

Remember: Write in rich, continuous book prose. Avoid superficial summaries.
Output publication-grade Markdown only."""
            },
            {
                "filename": "lesson_03_deep_dive_and_concurrency.md",
                "title": f"Lesson 3: Advanced Internal Mechanics, Concurrency & Recovery",
                "prompt": f"""Write Lesson 3 (Internal Mechanics & Reliability) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Principal infrastructure architects and kernel specialists.
Goal: In-depth analysis of concurrency control, crash recovery, state machines, and high availability.

Structure:
# Lesson 3: Advanced Internal Mechanics, Concurrency & Recovery

## 1. Concurrency Control, Lockless Queues & Conflict Resolution
(Lockless ring buffers, atomic operations, latch-free coordination, and deadlock prevention)

## 2. State Reconciliation & Recovery State Machines
(Crash recovery protocols, checkpointing invariants, redo/undo logging, or etcd raft consensus)

## 3. Resource Accounting, Eviction & Cleanup Engines
(Buffer recycling, worker loops, garbage collection, and bloat prevention)

## 4. Production Failure Domains & Byzantine Edge Cases
(Network partitions, kernel drops, partial writes, and mitigations)

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
(Required CLI tools: bpftool, kubectl, iproute2, tcpdump, strace, perf, and environment configuration)

## Exercise 1: Live State & Internal Subsystem Inspection
(Exact runnable CLI commands to inspect kernel maps, memory, buffers, processes, or metrics)

## Exercise 2: Benchmarking & Saturation Profiling
(Real benchmark commands, load generation, packet throughput, or latency profiling)

## Exercise 3: Fault Injection & Recovery Analysis
(Simulating sudden failure, packet drop, or partition, and inspecting recovery logs)

## Diagnostic Cheat Sheet & Verification Checklist
(Table of essential CLI commands and operational flags)

Rules: Provide full, executable commands and configurations with zero placeholders.
Output publication-grade Markdown only."""
            }
        ]

    # 4. Database Internals & Storage Systems
    elif any(k in cat_lower for k in ["data", "database", "postgresql", "storage", "distributed_systems"]):
        return [
            {
                "filename": "lesson_01_foundations_and_invariants.md",
                "title": f"Lesson 1: Foundations & Storage Invariants",
                "prompt": f"""Write Lesson 1 (Foundations & Storage Invariants) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Senior software engineers and database/storage architects.
Goal: Establish theoretical grounding, storage hierarchy trade-offs, and ACID invariants.

Structure:
# Lesson 1: Foundations & Storage Invariants

## Curriculum Roadmap
(Provide a clear outline of the curriculum modules)

## 1. Storage Hierarchies & The Relational/Disk Problem Space
(Deep exposition on disk/RAM boundaries, latency numbers, and why databases exist)

## 2. Fundamental System Guarantees & Slotted-Page Invariants
(PageHeaderData, item pointers, tuple alignment, and ACID guarantees)

## 3. High-Level Process & Shared Memory Architecture
(Include a clean Mermaid diagram representing background workers, shared buffers, and disk files)

Remember: Write in rich, continuous book prose. Avoid lazy bullet point lists.
Output publication-grade Markdown only."""
            },
            {
                "filename": "lesson_02_architecture_and_mechanics.md",
                "title": f"Lesson 2: Core Storage Engine & Buffer Pools",
                "prompt": f"""Write Lesson 2 (Core Storage Engine & Buffer Pools) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Database reliability engineers and storage systems programmers.
Goal: Dissect buffer pool replacement algorithms, dirty page flush lifecycles, and indexing internals.

Structure:
# Lesson 2: Core Storage Engine & Buffer Pools

## 1. Buffer Pool Architecture & Cache Replacement Mechanics
(Clock sweep, ARC, LRU-2, and shared memory hash tables)

## 2. B-Tree & Indexing Mechanics
(Page splitting, high keys, right links, and search/insert lifecycle)

## 3. The Critical Read/Write Execution Lifecycle
(End-to-end trace of a query from executor through buffer pool to disk)

Remember: Write in rich, continuous book prose. Avoid superficial summaries.
Output publication-grade Markdown only."""
            },
            {
                "filename": "lesson_03_deep_dive_and_concurrency.md",
                "title": f"Lesson 3: Concurrency Control, WAL & Recovery Mechanics",
                "prompt": f"""Write Lesson 3 (Concurrency Control, WAL & Recovery) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Principal database architects.
Goal: In-depth analysis of MVCC snapshot isolation, lock scheduling, WAL redo/undo state machines, and crash recovery.

Structure:
# Lesson 3: Concurrency Control, WAL & Recovery Mechanics

## 1. Multi-Version Concurrency Control (MVCC) & Lock Graphs
(xmin/xmax commit log visibility, snapshot horizons, and deadlock detection)

## 2. Write-Ahead Logging & Crash Recovery State Machines
(WAL buffers, LSN monotonically increasing invariants, checkpointing, and ARIES recovery)

## 3. Compaction, Eviction & Vacuum Engines
(Tuple freezing, background worker loops, and bloat prevention)

Remember: Write in rich, continuous book prose with technical depth.
Output publication-grade Markdown only."""
            },
            {
                "filename": "labs.md",
                "title": f"Operational Verification Labs",
                "prompt": f"""Write the complete Operational Verification Lab guide for '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Hands-on database practitioner and DBA.
Goal: Concrete laboratory exercises using real database clients, page analyzers, and benchmark suites.

Structure:
# Operational Verification Labs: {subtopic_title}

## Objective & Database Environment Setup
(Required database engines, client CLI tools, and inspection utilities)

## Exercise 1: Storage Page & Internal Memory Inspection
(Exact SQL and CLI commands to inspect slotted pages, buffer pool states, or index trees)

## Exercise 2: Concurrency Contention & Lock Graph Analysis
(Simulating concurrent transactions, lock conflicts, and analyzing wait graphs)

## Exercise 3: Crash Simulation & WAL Recovery Replay
(Simulating sudden termination, inspecting WAL records, and validating consistency)

## Production Diagnostic Cheat Sheet & Verification Checklist
(Table of essential SQL inspection queries and CLI flags)

Rules: Provide full, executable SQL queries and CLI commands with zero placeholders.
Output publication-grade Markdown only."""
            }
        ]

    # 5. Software Engineering, Compilers, Rust Systems & Architecture
    elif any(k in cat_lower for k in ["software", "compilers", "rust_systems", "architecture", "programming", "systems_programming"]):
        return [
            {
                "filename": "lesson_01_foundations_and_invariants.md",
                "title": f"Lesson 1: Foundations & Computational Invariants",
                "prompt": f"""Write Lesson 1 (Foundations & Invariants) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Senior software engineers, compiler engineers, and systems programmers.
Goal: Establish formal mental models, type system invariants, and computational complexity bounds.

Structure:
# Lesson 1: Foundations & Computational Invariants

## Curriculum Roadmap
(Provide a clear outline of the curriculum modules)

## 1. Theoretical Mental Model & Problem Space
(Deep exposition on language paradigms, formal grammars, type soundness, and memory safety invariants)

## 2. Computational Bounds & Non-Negotiable Invariants
(Asymptotic complexity bounds, memory safety guarantees, and deterministic resource lifecycles)

## 3. High-Level Component & Pipeline Architecture
(Include a clean Mermaid diagram representing the pipeline, AST/IR stages, or software architecture)

Remember: Write in rich, continuous book prose. Avoid lazy bullet point lists.
Output publication-grade Markdown only."""
            },
            {
                "filename": "lesson_02_architecture_and_mechanics.md",
                "title": f"Lesson 2: Core Internals & Memory Layouts",
                "prompt": f"""Write Lesson 2 (Core Internals & Memory Layouts) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Systems programmers needing deep mechanical understanding.
Goal: Dissect memory layouts, struct padding, AST/IR pipelines, and runtime execution.

Structure:
# Lesson 2: Core Internals & Memory Layouts

## 1. Memory Subsystems, Alignment & Pointer Mechanics
(Stack vs heap, cache line alignment, struct packing, and pointer indirection with ASCII diagrams)

## 2. Intermediate Representation (IR) & Compilation Stages
(Transformation pipelines, optimization passes, and code generation mechanics)

## 3. The Critical Execution Lifecycle
(End-to-end trace of execution through runtime, thread pool, or dispatch tables)

Remember: Write in rich, continuous book prose. Avoid superficial summaries.
Output publication-grade Markdown only."""
            },
            {
                "filename": "lesson_03_deep_dive_and_concurrency.md",
                "title": f"Lesson 3: Concurrency, Cache Coherence & Failure Modes",
                "prompt": f"""Write Lesson 3 (Concurrency, Optimization & Failure Modes) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Principal software engineers and systems architects.
Goal: Deep dive into lock-free synchronization, hardware cache coherence, SIMD, and undefined behavior.

Structure:
# Lesson 3: Concurrency, Cache Coherence & Failure Modes

## 1. Lock-Free Synchronization & Atomics
(Memory ordering semantics, compare-and-swap loops, and cache coherence protocols)

## 2. Hardware Cache Saturation & Optimization
(Minimizing branch mispredictions, cache misses, and vectorized execution)

## 3. Undefined Behavior & Edge Case Failure Domains
(Data races, pointer aliasing violations, memory leaks, and formal verification)

Remember: Write in rich, continuous book prose with technical depth.
Output publication-grade Markdown only."""
            },
            {
                "filename": "labs.md",
                "title": f"Operational Verification Labs",
                "prompt": f"""Write the complete Operational Verification Lab guide for '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Hands-on software engineer and systems programmer.
Goal: Concrete laboratory exercises using language toolchains, sanitizers, and performance profilers.

Structure:
# Operational Verification Labs: {subtopic_title}

## Objective & Toolchain Setup
(Required compiler toolchains e.g. Cargo/Rust, GCC/Clang, LLVM, GDB/LLDB, Valgrind/ASan)

## Exercise 1: AST, IR & Disassembly Analysis
(Exact commands to inspect intermediate representations, assembly output, and memory layouts)

## Exercise 2: Cache Miss & Throughput Profiling
(Benchmarking execution speed, memory allocations, and hardware performance counters)

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics
(Simulating concurrent thread access, running thread sanitizers, and diagnosing race conditions)

## Developer Cheat Sheet & Toolchain Checklist
(Table of essential compiler flags, sanitizer options, and profiling commands)

Rules: Provide full, executable code and commands with zero placeholders.
Output publication-grade Markdown only."""
            }
        ]

    # 6. Universal Technical Fallback (Domain-Calibrated)
    else:
        return [
            {
                "filename": "lesson_01_foundations_and_invariants.md",
                "title": f"Lesson 1: Foundations & Invariants",
                "prompt": f"""Write Lesson 1 (Foundations & Invariants) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Advanced practitioners and domain specialists.
Goal: Establish unshakeable theoretical grounding, core principles, and foundational invariants.

Structure:
# Lesson 1: Foundations & Invariants

## Curriculum Roadmap
(Provide a clear outline of the curriculum modules)

## 1. First-Principles Mental Model & Problem Space
(Deep exposition on why this field exists, what fundamental physical or conceptual trade-offs it solves)

## 2. Core Invariants & Non-Negotiable Guarantees
(Rigorous principles, physical laws, or axiomatic guarantees)

## 3. High-Level System Architecture & Conceptual Flow
(Include a clean Mermaid diagram representing the core data, signal, or conceptual pipeline)

Remember: Write in rich, continuous book prose like an authoritative textbook author. Avoid lazy bullet point lists.
Output publication-grade Markdown only."""
            },
            {
                "filename": "lesson_02_architecture_and_mechanics.md",
                "title": f"Lesson 2: Core Architecture & Structural Mechanics",
                "prompt": f"""Write Lesson 2 (Core Architecture & Mechanics) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Practitioners needing deep mechanical and structural understanding.
Goal: Dissect components, functional mechanics, internal representations, and the critical execution path.

Structure:
# Lesson 2: Core Architecture & Structural Mechanics

## 1. Internal Structure & Subsystem Coordination
(Deep exposition on how subsystems are organized, isolated, and coordinated)

## 2. Fundamental Mechanics & State Transitions
(Step-by-step trace of how state, energy, or data flows through the system)

## 3. Critical Path Analysis
(End-to-end trace of a primary operation from start to finish)

Remember: Write in rich, continuous book prose. Avoid superficial summaries.
Output publication-grade Markdown only."""
            },
            {
                "filename": "lesson_03_deep_dive_and_concurrency.md",
                "title": f"Lesson 3: Advanced Mechanics, Optimization & Failure Modes",
                "prompt": f"""Write Lesson 3 (Advanced Mechanics & Failure Modes) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Lead specialists and architects.
Goal: In-depth analysis of optimization, boundary conditions, edge cases, and failure domains.

Structure:
# Lesson 3: Advanced Mechanics, Optimization & Failure Modes

## 1. High-Performance Optimization & Scaling Dynamics
(Techniques for maximizing efficiency, minimizing distortion, or scaling throughput)

## 2. Boundary Conditions & Complex Dynamics
(Interactions under extreme stress, edge cases, and non-linear behaviors)

## 3. Failure Modes & Mitigations
(Common failure patterns, diagnostics, and defensive principles)

Remember: Write in rich, continuous book prose with technical depth.
Output publication-grade Markdown only."""
            },
            {
                "filename": "labs.md",
                "title": f"Operational Verification Labs",
                "prompt": f"""Write the complete Operational Verification Lab guide for '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Hands-on practitioner and specialist.
Goal: Step-by-step practical laboratory exercises using tools, simulators, or code specific to '{category_title}'.

Structure:
# Operational Verification Labs: {subtopic_title}

## Objective & Lab Setup
(Required domain-specific tools, environments, packages, or simulators)

## Exercise 1: Foundational Practical Implementation
(Exact step-by-step runnable exercise demonstrating the core concept)

## Exercise 2: Parameter Variation & Empirical Analysis
(Testing different configurations, measuring outputs, and graphing responses)

## Exercise 3: Fault Injection & Stress Testing
(Inducing boundary failures, analyzing error states, and verifying recovery)

## Practical Cheat Sheet & Quick Reference
(Table of essential commands, parameters, formulas, and verification checks)

Rules: Provide full, executable exercises with zero placeholders.
Output publication-grade Markdown only."""
            }
        ]

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

    modules = build_topic_modules(domain, category, subtopic_id, subtopic_title)

    tasks_to_run = []
    results = {}

    if force:
        purge_legacy_topic_files(subtopic_dir)

    for mod in modules:
        out_path = subtopic_dir / mod["filename"]
        if not out_path.exists() or force:
            tasks_to_run.append(mod)
        else:
            results[mod["filename"]] = False

    if not tasks_to_run:
        return results

    if workers and len(workers) > 0:
        # Build Author -> Reviewer pairs across distinct cluster nodes
        job_pairs = []
        for i, mod in enumerate(tasks_to_run):
            author_worker = workers[i % len(workers)]
            # Distinct node as reviewer
            reviewer_worker = workers[(i + 1) % len(workers)]
            # If author is an 8B/4B model, prefer a 32B model as reviewer if available
            large_workers = [w for w in workers if "32b" in w[1] or "35b" in w[1]]
            if large_workers and ("8b" in author_worker[1] or "4b" in author_worker[1]):
                reviewer_worker = large_workers[i % len(large_workers)]

            job_pairs.append((mod, author_worker, reviewer_worker))

        def run_module_job(job):
            mod_item, (w_host, w_model, w_provider), (r_host, r_model, r_provider) = job
            try:
                t0 = time.time()
                # 1. Authoring draft
                content = w_provider.generate(mod_item["prompt"], system_instruction=system_instruction)
                validated = validate_generation_output(content)

                # 2. Adversarial Peer Review & Hallucination Audit
                audit_prompt = f"""You are an adversarial Technical Reviewer & Fact-Checker.
Audit this masterclass chapter for '{mod_item['title']}' on '{subtopic_title}'.
Check for:
1. Fabricated APIs, fake syscalls/registers, or hallucinated invariants.
2. Syntactically invalid C/Rust snippets, bash commands, or Mermaid diagrams (ensure edge labels with '&' or math symbols are enclosed in double quotes).
3. Any lazy placeholders (// TODO, ..., TBD) or bullet-point outlines instead of rich narrative prose.

If accurate, factual, and publication-grade, output 'VERIFIED'.
If there are any hallucinations, syntax errors, or placeholders, rewrite and correct the full document with graduate-level precision.

DRAFT TO AUDIT:
\"\"\"
{validated[:8000]}
\"\"\"

Output either 'VERIFIED' or the fully corrected publication-grade Markdown only."""

                try:
                    review_res = r_provider.generate(audit_prompt, system_instruction="You are a ruthless technical auditor and peer reviewer.").strip()
                    if "<think>" in review_res and "</think>" in review_res:
                        review_res = review_res.split("</think>")[-1].strip()

                    final_content = validated
                    review_label = "Verified"
                    if review_res and not review_res.startswith("VERIFIED") and len(review_res) > 500:
                        final_content = validate_generation_output(review_res)
                        review_label = f"Audited & Corrected by {r_host}"
                except Exception as audit_err:
                    final_content = validated
                    review_label = f"Audit skipped ({audit_err})"

                target_file = subtopic_dir / mod_item["filename"]
                target_file.write_text(final_content.strip() + "\n", encoding="utf-8")
                elapsed = time.time() - t0
                return mod_item["filename"], True, f"Author: {w_host} ({w_model}) | {review_label} in {elapsed:.1f}s", None
            except Exception as e:
                return mod_item["filename"], False, f"{w_host} ({w_model})", str(e)

        with ThreadPoolExecutor(max_workers=min(len(workers), len(tasks_to_run))) as executor:
            future_to_mod = {executor.submit(run_module_job, job): job[0]["filename"] for job in job_pairs}
            for fut in as_completed(future_to_mod):
                fname, ok, worker_info, err = fut.result()
                results[fname] = ok
                if ok:
                    print(f"      [✔] {fname} -> {worker_info}", flush=True)
                else:
                    print(f"      [✘] {fname} failed ({worker_info}): {err}", flush=True)
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
