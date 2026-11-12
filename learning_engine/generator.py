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
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from jinja2 import Environment, FileSystemLoader
from .models import (
    OllamaCluster,
    OllamaProvider,
    get_provider,
    LLMProvider,
    validate_generation_output,
    CLUSTER_HOST_SPECS,
    AnthropicProvider
)
from .topic_manager import get_domain_persona
from .security import validate_canonical_topic_path

# Global semaphore to limit concurrent LLM requests and avoid rate limits
_LLM_SEMAPHORE = threading.Semaphore(4)

# Jinja2 Setup
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

class PromptFactory:
    @staticmethod
    def build_lesson_prompt(lesson_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        template = env.get_template("lesson.j2")
        return template.render(
            lesson_title=lesson_data["title"],
            subtopic_title=context["subtopic_title"],
            domain_title=context["domain_title"],
            category_title=context["category_title"],
            audience=lesson_data["audience"],
            goal=lesson_data["goal"],
            content_structure=lesson_data["structure"],
            latex_constraint=context["latex_constraint"]
        )

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

def purge_legacy_topic_files(topic_dir: Path):
    """
    Aggressively purges everything in the topic directory to allow clean regeneration 
    with the new 3-stage pipeline.
    """
    if not topic_dir.exists():
        return

    # Delete all markdown files and subdirectories
    for item in topic_dir.iterdir():
        if item.is_file() and item.suffix == ".md":
            try:
                item.unlink()
            except Exception:
                pass
        elif item.is_dir():
            shutil.rmtree(item, ignore_errors=True)

BOOK_STYLE_DIRECTIVE = """CRITICAL STYLE & TONE DIRECTIVE:
- This is a masterclass textbook chapter, NOT a slide-deck presentation or outline.
- STRICTLY AVOID endless bullet-point lists. Write in rich, articulated, flowing paragraphs of narrative prose.
- Connect concepts through deep exposition, historical context, and cause-and-effect mechanical reasoning.
- Write like an authoritative technical author (e.g. O'Reilly, MIT Press, No Starch Press): articulate, human, intellectually rigorous, and engaging.
- Use lists ONLY when providing sequential step-by-step CLI commands in labs or parameter reference tables. All conceptual and architectural explanations must be written in full narrative prose.
- RAW OUTPUT ONLY: Do NOT include conversational preambles (e.g., 'Here is your lesson', 'Sure', etc.), HTML tags, or code fences (e.g. ```markdown ... ```) around the entire output. Output the raw Markdown text directly."""

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
    domain_lower = domain.lower()
    cat_lower = category.lower()

    # 1. AI, Machine Learning, LLMs, Data Science (Computing domain)
    if domain_lower == "computing" and any(k in cat_lower for k in ["ai", "machine_learning", "deep_learning", "data_analysis", "data_visualisation", "mlops", "rag", "vibe_coding", "prompt"]):
        context = {
            "subtopic_title": subtopic_title,
            "domain_title": domain_title,
            "category_title": category_title,
            "latex_constraint": "3. FORMATTING: STRICTLY NO LaTeX ($...$ or $$...$$). Use plain text or code blocks for math."
        }
        return [
            {
                "filename": "lesson_01_foundations_and_invariants.md",
                "title": f"Lesson 1: Foundations & Mathematical Formulation",
                "prompt": PromptFactory.build_lesson_prompt({
                    "title": "Lesson 1: Foundations & Mathematical Formulation",
                    "audience": "Senior machine learning engineers, AI researchers, and systems architects.",
                    "goal": "Establish unshakeable theoretical grounding, problem space formulation, and mathematical invariants.",
                    "structure": """
## Curriculum Roadmap
(Provide a clear outline of the curriculum modules)

## 1. First-Principles Intuition & The Problem Space
(Deep narrative exposition on why this AI/ML technique exists, what fundamental limitations or computational trade-offs it solves)

## 2. Mathematical Formalization & Core Invariants
(Rigorous mathematical formulation, loss/objective equations, optimization bounds, and non-negotiable guarantees)

## 3. High-Level Pipeline & Architecture Dataflow
(Include a clean Mermaid diagram representing the model pipeline, tensor transformations, or agentic control flow)
"""
                }, context)
            },
            {
                "filename": "lesson_02_architecture_and_mechanics.md",
                "title": f"Lesson 2: Core Architecture & Algorithmic Mechanics",
                "prompt": PromptFactory.build_lesson_prompt({
                    "title": "Lesson 2: Core Architecture & Algorithmic Mechanics",
                    "audience": "Machine learning engineers and AI practitioners needing deep mechanical understanding.",
                    "goal": "Dissect representations, algorithm mechanics, layer operations, and runtime data structures.",
                    "structure": """
## 1. Internal Representations & Data Structures
(Vector embeddings, token structures, attention matrices, or parameter layouts with ASCII diagrams)

## 2. Forward Pass & Algorithmic Execution Lifecycle
(Step-by-step mathematical trace of inference/execution through the architecture)

## 3. Memory Footprint & Computational Complexity
(KV-cache scaling, parameter memory allocation, computational complexity O(...) bounds, and hardware accelerator mapping)
"""
                }, context)
            },
            {
                "filename": "lesson_03_deep_dive_and_concurrency.md",
                "title": f"Lesson 3: Optimization, Scaling & Failure Modes",
                "prompt": PromptFactory.build_lesson_prompt({
                    "title": "Lesson 3: Optimization, Scaling & Failure Modes",
                    "audience": "Lead AI engineers and production systems architects.",
                    "goal": "In-depth analysis of training/inference optimization, scaling laws, drift domains, and failure mitigation.",
                    "structure": """
## 1. Training Dynamics & Convergence Invariants
(Gradient stability, loss landscape geometry, learning rate mechanics, and regularization)

## 2. Production Latency & Serving Optimization
(Quantization trade-offs, batching strategies, speculative decoding, and caching)

## 3. Failure Modes & Edge Case Domains
(Distribution drift, catastrophic forgetting, hallucination failure surfaces, and guardrail architectures)
"""
                }, context)
            },
            {
                "filename": "labs.md",
                "title": f"Operational Verification Labs",
                "prompt": PromptFactory.build_lesson_prompt({
                    "title": "Operational Verification Labs",
                    "audience": "Hands-on AI engineer and practitioner.",
                    "goal": "Concrete hands-on lab using real, executable Python scripts, API harnesses, evaluation pipelines, and verification commands.",
                    "structure": """
## Objective & Environment Setup
(Required Python 3.11+ environment, packages e.g. PyTorch, HuggingFace, NumPy, Scikit-learn, Ollama, or Polars, and API configuration)

## Exercise 1: Hands-On Implementation & Pipeline Execution
(Complete, runnable Python script implementing the core prompt/model/algorithm for this topic with zero placeholders)

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking
(Real benchmarking code measuring accuracy, latency distributions, token costs, or convergence curves)

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation
(Reproducing failure modes, testing edge cases, and implementing guardrails or error handling)
"""
                }, context)
            }
        ]

    # 2. Security & Hardware Hacking (Computing domain)
    elif domain_lower == "computing" and any(k in cat_lower for k in ["security", "hardware_hacking", "reverse_engineering", "cryptography", "exploit"]):
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

    # 2b. DevSecOps, CI/CD, Supply Chain Security & Security Automation (Computing domain)
    elif domain_lower == "computing" and any(k in cat_lower for k in ["devsecops", "ci_cd", "supply_chain", "security_automation", "policy_as_code"]):
        return [
            {
                "filename": "lesson_01_foundations_and_invariants.md",
                "title": f"Lesson 1: DevSecOps Foundations & Secure Supply Chain Invariants",
                "prompt": f"""Write Lesson 1 (DevSecOps Foundations & Supply Chain Invariants) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Senior DevSecOps engineers, security architects, and platform security specialists.
Goal: Establish threat modeling, shift-left security boundaries, and SLSA / zero-trust pipeline invariants.

Structure:
# Lesson 1: DevSecOps Foundations & Secure Supply Chain Invariants

## Curriculum Roadmap
(Provide a clear outline of the curriculum modules)

## 1. Supply Chain Threat Landscape & Pipeline Attack Vectors
(Deep exposition on dependency confusion, typosquatting, compromised CI runners, and pipeline tampering)

## 2. Cryptographic Attestation & Non-Negotiable Invariants
(Provenance verification, SLSA framework levels, SBOM integrity, and policy admission barriers)

## 3. High-Level DevSecOps Pipeline Architecture
(Include a clean Mermaid diagram representing the secure CI/CD lifecycle: lint -> SAST -> secret scan -> build -> SBOM -> image signing -> admission control)

Remember: Write in rich, continuous book prose. Avoid lazy bullet point lists.
Output publication-grade Markdown only."""
            },
            {
                "filename": "lesson_02_architecture_and_mechanics.md",
                "title": f"Lesson 2: Static Analysis, Secret Detection & Container Security",
                "prompt": f"""Write Lesson 2 (Static Analysis, Secrets & Containers) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Security engineers and CI/CD platform developers.
Goal: Dissect AST-based SAST rules, Shannon entropy secret detection, container image layer scanning, and rootless isolation.

Structure:
# Lesson 2: Static Analysis, Secret Detection & Container Security

## 1. Abstract Syntax Tree (AST) Rules & SAST Engine Mechanics
(How Semgrep parses code, pattern matching syntax, taint tracking across call graphs)

## 2. High-Entropy Secret Detection & Git History Analysis
(Shannon entropy calculations, regex token matchers, gitleaks rules, and pre-commit hook interception)

## 3. OCI Container Layer Inspection & Rootless Architecture
(Image layer hashing, base image CVE tracking, minimal distroless containers, and seccomp/apparmor profiles)

Remember: Write in rich, continuous book prose with deep technical mechanics.
Output publication-grade Markdown only."""
            },
            {
                "filename": "lesson_03_deep_dive_and_concurrency.md",
                "title": f"Lesson 3: Supply Chain Attestation, SBOMs & Policy as Code",
                "prompt": f"""Write Lesson 3 (Attestation, SBOMs & Policy as Code) for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Principal security architects and platform engineering leads.
Goal: In-depth analysis of in-toto attestations, Sigstore/Cosign keyless signing, SPDX/CycloneDX SBOMs, and OPA/Gatekeeper admission control.

Structure:
# Lesson 3: Supply Chain Attestation, SBOMs & Policy as Code

## 1. Sigstore, Fulcio & Keyless OIDC Image Signing Mechanics
(OIDC identity tokens, ephemeral X.509 certs, Rekor transparency log, and verification workflows)

## 2. SBOM Generation & Vulnerability Correlation Engines
(SPDX and CycloneDX standard formats, Syft package discovery, Grype vulnerability matching algorithms)

## 3. Admission Control & Policy-as-Code Evaluation
(OPA Rego and Kyverno validation webhooks, verifying signatures at Kubernetes cluster admission)

Remember: Write in rich, continuous book prose. Output publication-grade Markdown only."""
            },
            {
                "filename": "labs.md",
                "title": f"Operational Verification Labs",
                "prompt": f"""Write the complete Operational Verification Lab guide for '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Hands-on DevSecOps engineer and security practitioner.
Goal: Step-by-step diagnostic verification using real DevSecOps tools (trivy, semgrep, gitleaks, cosign, syft, grype, checkov, conftest).

STRICT MANDATE: DO NOT use Linux kernel commands (NO bpftool, NO tc qdisc, NO mkfs, NO mount). Every single exercise MUST execute real application security, container scanning, secret detection, or SBOM tools.

Structure:
# Operational Verification Labs: {subtopic_title}

## Objective & Lab Bench Setup
(Required CLI tools: trivy, semgrep, gitleaks, cosign, syft, grype, checkov, conftest, and test repository setup)

## Exercise 1: Static Code Analysis & Secret Scanning
(Exact runnable CLI commands with semgrep custom rules and gitleaks git history audits, with realistic vulnerable snippets)

## Exercise 2: Container Vulnerability Auditing & SBOM Generation
(Scanning container images with Trivy/Grype, generating CycloneDX SBOMs with Syft, filtering false positives)

## Exercise 3: Cryptographic Image Signing & Admission Policy Enforcement
(Generating Cosign key pairs or keyless signing, creating OPA/conftest Rego policies to reject unsigned or high-CVE artifacts)

## DevSecOps Pipeline Diagnostic Cheat Sheet & Verification Checklist
(Table of essential CLI commands, exit codes, and operational flags)

Rules: Provide full, runnable commands, configurations, and YAML/Rego policies with zero placeholders.
Output publication-grade Markdown only."""
            }
        ]

    # 3. Systems & Cloud Infrastructure (eBPF, Kubernetes, Linux Kernel, SRE) (Computing domain)
    elif domain_lower == "computing" and any(k in cat_lower for k in ["infrastructure", "ebpf", "kubernetes", "networking", "linux_kernel", "os_theory", "sre"]):
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

Target Audience: Hands-on systems engineer and infrastructure practitioner.
Goal: Step-by-step diagnostic verification using real tools, inspection utilities, and reproduction scripts specific to '{subtopic_title}'.

Structure:
# Operational Verification Labs: {subtopic_title}

## Objective & Environment Setup
(Required diagnostic utilities authentic to '{subtopic_title}' e.g. for Kubernetes: kubectl, etcdctl, helm; for Networking: ip, ss, wireshark, dig; for eBPF: bpftool, bpftrace; for Linux: strace, perf; for SRE: prometheus, alertmanager. Do NOT output generic copy-pasted kernel tool lists)

## Exercise 1: Live State & Internal Subsystem Inspection
(Exact runnable CLI commands to inspect state, memory, buffers, processes, or metrics)

## Exercise 2: Benchmarking & Saturation Profiling
(Real benchmark commands, load generation, throughput, or latency profiling)

## Exercise 3: Fault Injection & Recovery Analysis
(Simulating sudden failure, packet drop, or partition, and inspecting recovery logs)

## Diagnostic Cheat Sheet & Verification Checklist
(Table of essential CLI commands and operational flags)

Rules: Provide full, executable commands and configurations with zero placeholders.
Output publication-grade Markdown only."""
            }
        ]

    # 4. Database Internals & Storage Systems (Computing domain)
    elif domain_lower == "computing" and any(k in cat_lower for k in ["data", "database", "postgresql", "storage", "distributed_systems"]):
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

    # 5. Software Engineering, Compilers, Rust Systems & Architecture (Computing domain)
    elif domain_lower == "computing" and any(k in cat_lower for k in ["software", "compilers", "rust_systems", "architecture", "programming", "systems_programming"]):
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

Target Audience: Hands-on practitioner and specialist in '{category_title}'.
Goal: Step-by-step practical laboratory exercises using tools, simulators, or code specific to '{category_title}'.

STRICT NON-COMPUTING MANDATE:
- This is a non-computing subject ({domain_title} / {category_title}).
- Under NO circumstances should you use generic Linux operating system commands (NO bpftool, NO kubectl, NO dmesg, NO strace, NO sysctl, NO apt-get, NO netstat, NO iptables).
- All tools, environments, exercises, and setups MUST be 100% authentic and domain-native to '{domain_title}' (e.g. for Arts/Music: DAW, MIDI controllers, synthesizers, score notation software; for Motorsports: telemetry data, chassis simulators, CAD; for Natural Sciences: laboratory glassware, spectroscopy, Python scientific computing with NumPy/SciPy; for Economics: econometrics models, R/Python, spreadsheets).

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

def scope_topic_curriculum(
    domain: str,
    category: str,
    subtopic_id: str,
    subtopic_title: str,
    scoping_provider: Optional[LLMProvider] = None
) -> List[Dict[str, str]]:
    """
    Option B Pre-Flight AI Scoping:
    Dynamically analyzes the true engineering surface area of the subject to size the curriculum:
      - Focused Primitives / Specific Tools: 2 Lessons + Labs
      - Standard Systems / Engines: 3-4 Lessons + Labs
      - Flagship Architectures / Large Distributed Systems: 5-6 Lessons + Labs
    Prevents artificial filler for narrow topics and prevents truncation of complex flagship topics.
    """
    domain_title = domain.replace("_", " ").title()
    category_title = category.replace("_", " ").title()

    fallback_modules = build_topic_modules(domain, category, subtopic_id, subtopic_title)
    if not scoping_provider:
        return fallback_modules

    scoping_prompt = f"""You are a Principal Technical Curriculum Architect.
Analyze the subject: '{subtopic_title}' (Domain: '{domain_title}', Discipline/Course: '{category_title}').

Determine the exact number of theoretical masterclass lessons required to provide exhaustive technical coverage WITHOUT superficial padding or unnecessary filler:
- Tier 1 (Focused Primitives / Narrow Tools): 2 Lessons (e.g. A specific tool, single protocol, or focused technique).
- Tier 2 (Standard Engines / Frameworks / Core Protocols): 3-4 Lessons (e.g. A self-contained engine, design pattern, or subsystem).
- Tier 3 (Flagship Architectures / Massive Distributed Systems): 5-6 Lessons (e.g. PostgreSQL, Kubernetes, Linux VFS, eBPF Kernel).

Output JSON only in this exact format:
{{
  "scope_tier": "focused|standard|flagship",
  "lesson_count": <int between 2 and 6>,
  "rationale": "<1 sentence justifying the chosen depth>",
  "lessons": [
    {{
      "filename": "lesson_01_<clean_slug>.md",
      "title": "Lesson 1: <Descriptive Title without 'and'>",
      "focus": "<Core theoretical focus, mechanisms, and invariants>"
    }}
  ]
}}"""

    try:
        raw_res = scoping_provider.generate(scoping_prompt, system_instruction="Output valid JSON only.")
        clean_json = raw_res.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[-1].split("```")[0].strip()
        elif clean_json.startswith("```") and clean_json.endswith("```"):
            clean_json = clean_json.split("```")[1].strip()

        parsed = json.loads(clean_json)
        tier = parsed.get("scope_tier", "standard").upper()
        rationale = parsed.get("rationale", "")
        parsed_lessons = parsed.get("lessons", [])

        if len(parsed_lessons) >= 2:
            print(f"      [★] Pre-Flight Scoping: {tier} ({len(parsed_lessons)} Lessons + Labs) -> {rationale}", flush=True)
            dynamic_modules = []
            for i, l in enumerate(parsed_lessons):
                num = i + 1
                fname = l.get("filename") or f"lesson_{num:02d}.md"
                clean_name = fname.replace(".md", "")
                if not re.match(r"^lesson_\d{2}_", clean_name):
                    clean_slug = re.sub(r"^(?:lesson_)?\d*_*", "", clean_name).strip("_")
                    fname = f"lesson_{num:02d}_{clean_slug}.md" if clean_slug else f"lesson_{num:02d}.md"

                title = l.get("title") or f"Lesson {num}"
                focus = l.get("focus") or ""

                lesson_prompt = f"""Write {title} for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: Senior software engineers, systems programmers, and domain architects.
Lesson Focus: {focus}

Structure:
# {title}

## 1. First-Principles Intuition & Invariants
(Deep narrative exposition establishing theoretical grounding, problem space, and mathematical/system invariants)

## 2. Core Architecture & Mechanics
(Dissect internal data structures, algorithms, or execution models with ASCII or clean Mermaid diagrams)

## 3. High-Performance Optimization & Failure Modes
(Concurrency, resource scaling, boundary edge cases, and failure mitigations)

Remember: Write in rich, continuous book prose like an O'Reilly or MIT Press author. Avoid lazy bullet point lists.
Output publication-grade Markdown only."""

                dynamic_modules.append({
                    "filename": fname,
                    "title": title,
                    "prompt": lesson_prompt
                })

            # Append the discipline-adaptive lab module
            lab_mod = fallback_modules[-1]
            dynamic_modules.append(lab_mod)
            return dynamic_modules
    except Exception as e:
        print(f"      [!] Pre-flight scoping note ({e}), using standard adaptive template.", flush=True)

    return fallback_modules

def generate_topic_parallel(
    domain: str,
    category: str,
    subtopic_id: str,
    subtopic_dir: Path,
    force: bool = False,
    workers: Optional[List[Tuple[str, str, OllamaProvider]]] = None
) -> Dict[str, Any]:
    """
    Generates a dynamically-scoped multi-lesson masterclass curriculum unit across all active
    Ollama cluster engines in parallel with cross-node adversarial fact-checking.
    """
    subtopic_dir = validate_canonical_topic_path(subtopic_dir)
    subtopic_dir.mkdir(parents=True, exist_ok=True)
    subtopic_title = subtopic_id.replace("_", " ").title()
    domain_title = domain.replace("_", " ").title()
    category_title = category.replace("_", " ").title()
    persona = get_domain_persona(domain)
    system_instruction = persona + "\n\n" + BOOK_STYLE_DIRECTIVE

    if workers is None:
        cluster = OllamaCluster()
        workers = cluster.get_parallel_workers()

    scoping_prov = workers[0][2] if workers else None
    modules = scope_topic_curriculum(domain, category, subtopic_id, subtopic_title, scoping_provider=scoping_prov)

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
        # Build parallel drafting jobs (1 worker per module)
        jobs = []
        for i, mod in enumerate(tasks_to_run):
            w = workers[i % len(workers)]
            jobs.append((mod, w))

        print(f"      [▶] Dispatched {len(jobs)} parallel drafting jobs simultaneously across cluster:", flush=True)
        for mod_item, (w_host, w_model, _) in jobs:
            host_label = CLUSTER_HOST_SPECS.get(w_host, {}).get("name", w_host).upper()
            print(f"          ├── [{host_label:9s}] -> {mod_item['filename']} ({w_model})", flush=True)

        drafts = {}

        def run_draft_job(job):
            mod_item, (w_host, w_model, w_provider) = job
            host_label = CLUSTER_HOST_SPECS.get(w_host, {}).get("name", w_host).upper()
            t0 = time.time()
            try:
                with _LLM_SEMAPHORE:
                    content = w_provider.generate(mod_item["prompt"], system_instruction=system_instruction)
                validated = validate_generation_output(content)
                elapsed = time.time() - t0
                print(f"          [✔] [{host_label:9s}] Drafted {mod_item['filename']} in {elapsed:.1f}s", flush=True)
                return mod_item["filename"], True, validated, mod_item, host_label, w_host, elapsed, None
            except Exception as e:
                print(f"          [✘] [{host_label:9s}] Failed {mod_item['filename']}: {e}", flush=True)
                return mod_item["filename"], False, None, mod_item, host_label, w_host, time.time() - t0, str(e)

        # Phase 1: Concurrently draft all modules without cross-node lock contention
        is_cloud = any("anthropic" in w[0].lower() or "gemini" in w[0].lower() for w in workers)
        pool_size = min(3, len(tasks_to_run)) if is_cloud else min(len(workers), len(tasks_to_run))
        with ThreadPoolExecutor(max_workers=pool_size) as executor:
            future_to_mod = {executor.submit(run_draft_job, job): job[0]["filename"] for job in jobs}
            for fut in as_completed(future_to_mod):
                fname, ok, content, mod_item, host_label, w_host, elapsed, err = fut.result()
                if ok and content:
                    drafts[fname] = (content, mod_item, host_label, w_host, elapsed)
                else:
                    results[fname] = False

        # Phase 2: Concurrent Quality Audit & Fact-Checking + Prose Refinement
        def get_auditor_for_host(author_host: str):
            # Prioritize 30B/32B local nodes, or Claude if available
            large_reviewers = [w for w in workers if ("32b" in w[1] or "30b" in w[1]) and w[0] != author_host]
            if large_reviewers:
                return large_reviewers[0]
            # Fallback to any other node
            distinct = [w for w in workers if w[0] != author_host]
            return distinct[0] if distinct else workers[0]

        def run_audit_and_refine_job(item):
            fname, (content, mod_item, host_label, author_host, elapsed) = item
            r_host, r_model, r_provider = get_auditor_for_host(author_host)
            r_name = CLUSTER_HOST_SPECS.get(r_host, {}).get("name", r_host).upper()
            
            final_content = content
            audit_note = "Verified"

            # 3-Stage: Audit (Fact-Check) + Refine (Prose Polish)
            try:
                # Domain-specific constraints
                latex_constraint = ""
                if any(d in domain for d in ["computing", "engineering", "business", "crafts", "humanities"]):
                    latex_constraint = "3. FORMATTING: STRICTLY NO LaTeX ($...$ or $$...$$). Use plain text or code blocks for math. "
                else:
                    latex_constraint = "3. FORMATTING: Use LaTeX ($...$) for mathematical formulas where appropriate."

                refine_prompt = f"""You are a master technical author and rigorous adversarial auditor.
Audit and rewrite this masterclass chapter for '{mod_item['title']}' on '{subtopic_title}'.

AUDIT & REFINE REQUIREMENTS:
1. FACT-CHECK: Fix any fabricated APIs, hallucinated invariants, or technical inaccuracies.
2. PROSE STYLE: Rewrite all prose to be authoritative, engaging, and articulate (e.g., O'Reilly/MIT Press style). Remove all 'AI-isms' (e.g., 'In conclusion', 'It is important to note', 'I hope this helps'). Ensure continuous flow, depth, and structural coherence.
{latex_constraint}
4. DIAGRAMS & SYNTAX: Mermaid diagrams MUST use strict syntax.
   - All labels MUST be enclosed in double quotes (e.g., A -->| "Label Text" | B).
   - Use simple, linear flowcharts. Do NOT use complex subgraphs or nested nodes.
   - Examples of correct Mermaid syntax:
     - `graph TD; A -->| "Start" | B; B -->| "End" | C;`
     - `sequenceDiagram; participant A; participant B; A->>B: "Request"; B-->>A: "Response";`
5. PLACEHOLDERS: Eliminate all lazy placeholders (// TODO, ..., TBD) and bullet-point lists. Convert to rich narrative paragraphs.

DRAFT TO AUDIT & REFINE:
\"\"\"
{content[:7000]}
\"\"\"

Output the fully corrected, publication-grade, raw Markdown only."""

                refinement_res = ""
                with _LLM_SEMAPHORE:
                    refinement_res = r_provider.generate(refine_prompt, system_instruction="You are a master technical author and ruthless peer reviewer.")
                final_content = validate_generation_output(refinement_res)
                audit_note = f"Audited & Refined by [{r_name}]"
            except Exception as e:
                audit_note = f"Audit/Refine failed: {e}"
                # Keep original draft if refinement fails

            target_file = subtopic_dir / fname
            target_file.write_text(final_content.strip() + "\n", encoding="utf-8")
            print(f"      [✔] {fname} published ({host_label} -> {audit_note})", flush=True)
            return fname, True

        if not drafts:
            return results

        with ThreadPoolExecutor(max_workers=min(4, len(drafts))) as audit_executor:
            for fname, ok in audit_executor.map(run_audit_and_refine_job, drafts.items()):
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
    """
    Standardized entrypoint for curriculum unit generation.
    Always enforces canonical 3-level taxonomy and multi-lesson masterclass generation.
    """
    subtopic_dir = validate_canonical_topic_path(subtopic_dir)
    workers = None
    if provider:
        workers = [("custom", "override", provider)]
    return generate_topic_parallel(
        domain=domain,
        category=category,
        subtopic_id=subtopic_id,
        subtopic_dir=subtopic_dir,
        force=force,
        workers=workers
    )

