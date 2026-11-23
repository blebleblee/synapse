"""
Domain Curriculum & Toolchain Strategy Architecture
Provides domain-aware curriculum blueprints, structured toolchain definitions,
and clean strategy dispatching for masterclass curriculum and lab generation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple


class LabEnvironmentType(Enum):
    """Defines the authentic execution environment for domain exercises."""
    CODE = "code"                    # Python, Rust, C++ runnable scripts & harnesses
    CLI_TOOLS = "cli_tools"          # Native CLI utilities, diagnostics & profilers
    HARDWARE = "hardware"            # Logic analyzers, bus sniffers, breadboards
    SOFTWARE_GUI = "software_gui"    # DAWs, CAD software, visual notation suites
    FIELDWORK = "fieldwork"          # Wet lab glassware, spectroscopy, clinical protocols
    ANALYTICAL = "analytical"        # Proofs, formal derivations, econometrics models


@dataclass
class Toolchain:
    """Represents domain-native tooling, packages, and verification procedures."""
    environment_type: LabEnvironmentType
    primary_language: Optional[str] = None
    frameworks: List[str] = field(default_factory=list)
    diagnostic_tools: List[str] = field(default_factory=list)
    verification_commands: List[str] = field(default_factory=list)
    setup_instructions: str = ""


@dataclass
class LessonTemplate:
    """Defines the structure and pedagogical goals of a curriculum module."""
    filename: str
    title: str
    audience: str
    goal: str
    sections: List[str]


@dataclass
class CurriculumBlueprint:
    """Complete masterclass specification composed of lesson templates and toolchain."""
    lessons: List[LessonTemplate]
    toolchain: Toolchain
    style_directives: str
    latex_policy: str = "optional"   # "forbidden" | "required" | "optional"


class DomainStrategy(ABC):
    """Abstract base strategy for a curriculum domain or discipline."""

    def get_base_style_directive(self) -> str:
        return (
            "CRITICAL STYLE MANDATE: PRACTICALITY FIRST (80% Hands-On / 20% Theory):\n"
            "- Write in continuous, authoritative narrative textbook prose (MIT Press / O'Reilly style).\n"
            "- 80% Actionable Execution: Focus on real-world techniques, physical hand/tool mechanics, exact parameters, runnable code/manifests, and concrete practice routines.\n"
            "- 20% First-Principles Intuition: Ground the practice in core theory/physics, but NEVER let abstract math, academic derivations, or disconnected scripts overshadow hands-on mastery.\n"
            "- AVOID superficial summaries or lazy bullet-point slide decks. Use rich, structured, practitioner-first paragraphs.\n"
            "- All code, configurations, equations, and exercises must be complete with ZERO placeholders."
        )

    @abstractmethod
    def get_toolchain(self) -> Toolchain:
        """Returns the domain-native toolchain for lab verification."""
        pass

    @abstractmethod
    def get_blueprint(self, subtopic_title: str, category_title: str) -> CurriculumBlueprint:
        """Constructs the canonical 4-module masterclass blueprint."""
        pass


# ============================================================================
# COMPUTING DOMAIN STRATEGIES
# ============================================================================

class AIMLStrategy(DomainStrategy):
    """Strategy for AI, Machine Learning, LLMs, and Data Science."""

    def get_toolchain(self) -> Toolchain:
        return Toolchain(
            environment_type=LabEnvironmentType.CODE,
            primary_language="Python 3.11+",
            frameworks=["PyTorch", "HuggingFace Transformers", "NumPy", "Scikit-Learn", "Polars", "Ollama"],
            diagnostic_tools=["cProfile", "torch.cuda.memory_summary", "Weights & Biases", "TensorBoard"],
            verification_commands=["python -m pytest", "python eval_pipeline.py --benchmark"],
            setup_instructions="Create a clean Python 3.11+ virtual environment and install ML dependencies: pip install torch transformers datasets accelerate numpy polars"
        )

    def get_blueprint(self, subtopic_title: str, category_title: str) -> CurriculumBlueprint:
        return CurriculumBlueprint(
            lessons=[
                LessonTemplate(
                    filename="lesson_01_foundations_and_invariants.md",
                    title="Lesson 1: Foundations & Mathematical Formulation",
                    audience="Senior machine learning engineers, AI researchers, and systems architects",
                    goal="Establish theoretical grounding, problem space formulation, and mathematical invariants",
                    sections=[
                        "## Curriculum Roadmap",
                        "## 1. First-Principles Intuition & The Problem Space",
                        "## 2. Mathematical Formalization & Core Invariants",
                        "## 3. High-Level Pipeline & Architecture Dataflow (include clean Mermaid diagram)"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_02_architecture_and_mechanics.md",
                    title="Lesson 2: Core Architecture & Algorithmic Mechanics",
                    audience="ML engineers and data systems programmers needing mechanical understanding",
                    goal="Dissect internal algorithms, tensor operations, parameter scaling, and execution paths",
                    sections=[
                        "## 1. Tensor Transformations & Dimensional Flows",
                        "## 2. Loss Surfaces, Gradients & Optimization Dynamics",
                        "## 3. Attention Maps, Kernel Mechanics & Latent Geometry"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_03_deep_dive_and_concurrency.md",
                    title="Lesson 3: Advanced Optimization, Serving & Failure Modes",
                    audience="Staff ML engineers, MLOps architects, and research leads",
                    goal="In-depth analysis of quantization, throughput bottlenecks, hallucination modes, and scaling",
                    sections=[
                        "## 1. Memory Bandwidth, KV-Cache Optimization & Quantization Bounds",
                        "## 2. Distributed Sharding, Pipeline Parallelism & Communication Overhead",
                        "## 3. Production Failure Domains, Drift & Hallucination Mitigation"
                    ]
                ),
                LessonTemplate(
                    filename="labs.md",
                    title="Operational Verification Labs",
                    audience="Hands-on AI engineer and practitioner",
                    goal="Concrete hands-on lab using real, runnable Python scripts, evaluation harnesses, and benchmarks",
                    sections=[
                        "## Objective & Environment Setup",
                        "## Exercise 1: Hands-On Implementation & Pipeline Execution",
                        "## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking",
                        "## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation",
                        "## ML Diagnostic Cheat Sheet & Verification Checklist"
                    ]
                )
            ],
            toolchain=self.get_toolchain(),
            style_directives=self.get_base_style_directive(),
            latex_policy="forbidden"
        )


class SecurityHardwareStrategy(DomainStrategy):
    """Strategy for hardware hacking, reverse engineering, and embedded security."""

    def get_toolchain(self) -> Toolchain:
        return Toolchain(
            environment_type=LabEnvironmentType.HARDWARE,
            frameworks=["sigrok-cli", "openocd", "flashrom", "binwalk", "radare2"],
            diagnostic_tools=["Logic analyzer", "USB-UART bridge", "gdb-multiarch", "minicom"],
            verification_commands=["sigrok-cli --scan", "flashrom -p ft2232_spi:type=232H --read dump.bin"],
            setup_instructions="Hardware bench: USB logic analyzer, UART/JTAG adapter, and diagnostic suite: apt-get install sigrok-cli openocd flashrom binwalk"
        )

    def get_blueprint(self, subtopic_title: str, category_title: str) -> CurriculumBlueprint:
        return CurriculumBlueprint(
            lessons=[
                LessonTemplate(
                    filename="lesson_01_foundations_and_invariants.md",
                    title="Lesson 1: Foundations, Attack Surfaces & Physical Invariants",
                    audience="Hardware security researchers, embedded engineers, and offensive security practitioners",
                    goal="Establish physical signaling models, attack surfaces, pinout mechanics, and security boundaries",
                    sections=[
                        "## Curriculum Roadmap",
                        "## 1. Physical Signal Theory & Hardware Problem Space",
                        "## 2. Threat Modeling & Non-Negotiable Invariants",
                        "## 3. High-Level Bus Topology & Interface Architecture (include clean Mermaid diagram)"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_02_architecture_and_mechanics.md",
                    title="Lesson 2: Protocol Mechanics & Bus Framing",
                    audience="Embedded security engineers and hardware reverse engineers",
                    goal="Dissect frame structures, clocking edges, register maps, and signal transactions",
                    sections=[
                        "## 1. Clock Synchronization & Signal Timing Diagrams",
                        "## 2. Frame Architecture & Bit-Level Encodings",
                        "## 3. Bus Transaction Lifecycle"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_03_deep_dive_and_concurrency.md",
                    title="Lesson 3: Exploitation Primitives, Glitching & Hardening",
                    audience="Senior exploit developers and embedded hardware architects",
                    goal="Deep dive into firmware dumping, fault injection, and hardware countermeasures",
                    sections=[
                        "## 1. Firmware Extraction & Memory Carving Mechanics",
                        "## 2. Fault Injection & Glitch State Machines",
                        "## 3. Hardware Countermeasures & Defensive Invariants"
                    ]
                ),
                LessonTemplate(
                    filename="labs.md",
                    title="Operational Verification Labs",
                    audience="Hands-on hardware hacker and penetration tester",
                    goal="Concrete laboratory exercises using real hardware tools, bus sniffers, and logic analyzers",
                    sections=[
                        "## Objective & Lab Bench Setup",
                        "## Exercise 1: Live Hardware Probing & Signal Capture",
                        "## Exercise 2: Bus Sniffing, Register Inspection & Memory Dumping",
                        "## Exercise 3: Fault Simulation & Exploit Verification",
                        "## Hardware Security Checklist & Diagnostic Cheat Sheet"
                    ]
                )
            ],
            toolchain=self.get_toolchain(),
            style_directives=self.get_base_style_directive(),
            latex_policy="optional"
        )


class InfrastructureStrategy(DomainStrategy):
    """Strategy for Kubernetes, eBPF, Linux kernel, networking, and SRE."""

    def get_toolchain(self) -> Toolchain:
        return Toolchain(
            environment_type=LabEnvironmentType.CLI_TOOLS,
            frameworks=["kubectl", "iproute2", "etcdctl", "crictl", "helm"],
            diagnostic_tools=["ss", "ethtool", "tcpdump", "perf", "strace", "bpftool"],
            verification_commands=["ip -s link", "ss -tipm", "kubectl get pods -A", "perf stat"],
            setup_instructions="Install cloud infrastructure diagnostics: kubectl, iproute2, ethtool, tcpdump, and perf"
        )

    def get_blueprint(self, subtopic_title: str, category_title: str) -> CurriculumBlueprint:
        return CurriculumBlueprint(
            lessons=[
                LessonTemplate(
                    filename="lesson_01_foundations_and_invariants.md",
                    title="Lesson 1: Foundations & Kernel/System Invariants",
                    audience="Systems programmers, kernel engineers, and cloud infrastructure architects",
                    goal="Establish theoretical grounding, kernel boundaries, and non-negotiable system invariants",
                    sections=[
                        "## Curriculum Roadmap",
                        "## 1. First-Principles Problem Space & Execution Boundaries",
                        "## 2. Fundamental System Guarantees & Non-Negotiable Invariants",
                        "## 3. High-Level Process & Subsystem Architecture (include clean Mermaid diagram)"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_02_architecture_and_mechanics.md",
                    title="Lesson 2: Core Architecture & Memory/Execution Models",
                    audience="Systems programmers needing deep mechanical understanding",
                    goal="Dissect process models, memory allocation, byte-level data structures, and the critical execution path",
                    sections=[
                        "## 1. Process, Threading & Execution Lifecycles",
                        "## 2. Memory Subsystems & Buffer Management",
                        "## 3. Data Structures & On-Disk/In-Kernel Binary Layouts",
                        "## 4. The Critical Execution Lifecycle"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_03_deep_dive_and_concurrency.md",
                    title="Lesson 3: Advanced Internal Mechanics, Concurrency & Recovery",
                    audience="Principal infrastructure architects and kernel specialists",
                    goal="In-depth analysis of concurrency control, crash recovery, state machines, and high availability",
                    sections=[
                        "## 1. Concurrency Control, Lockless Queues & Conflict Resolution",
                        "## 2. State Reconciliation & Recovery State Machines",
                        "## 3. Resource Accounting, Eviction & Cleanup Engines",
                        "## 4. Production Failure Domains & Byzantine Edge Cases"
                    ]
                ),
                LessonTemplate(
                    filename="labs.md",
                    title="Operational Verification Labs",
                    audience="Hands-on systems engineer and infrastructure practitioner",
                    goal=f"Step-by-step diagnostic verification using real tools specific to '{subtopic_title}'",
                    sections=[
                        "## Objective & Environment Setup",
                        "## Exercise 1: Live State & Internal Subsystem Inspection",
                        "## Exercise 2: Benchmarking & Saturation Profiling",
                        "## Exercise 3: Fault Injection & Recovery Analysis",
                        "## Diagnostic Cheat Sheet & Verification Checklist"
                    ]
                )
            ],
            toolchain=self.get_toolchain(),
            style_directives=self.get_base_style_directive(),
            latex_policy="optional"
        )


class DatabaseStrategy(DomainStrategy):
    """Strategy for Database Internals, Storage Engines, and Distributed State."""

    def get_toolchain(self) -> Toolchain:
        return Toolchain(
            environment_type=LabEnvironmentType.CLI_TOOLS,
            frameworks=["PostgreSQL", "SQLite", "DuckDB", "etcd"],
            diagnostic_tools=["psql", "pgbench", "pg_waldump", "pageinspect", "explain (analyze, buffers)"],
            verification_commands=["pgbench -c 10 -t 1000", "psql -c 'SELECT * FROM pg_stat_activity;'"],
            setup_instructions="PostgreSQL / database client environment: psql, pgbench, and local test instance"
        )

    def get_blueprint(self, subtopic_title: str, category_title: str) -> CurriculumBlueprint:
        return CurriculumBlueprint(
            lessons=[
                LessonTemplate(
                    filename="lesson_01_foundations_and_invariants.md",
                    title="Lesson 1: Foundations & Storage Invariants",
                    audience="Senior software engineers and database/storage architects",
                    goal="Establish theoretical grounding, storage hierarchy trade-offs, and ACID invariants",
                    sections=[
                        "## Curriculum Roadmap",
                        "## 1. The Storage Problem Space & Theoretical Bounds",
                        "## 2. ACID Guarantees & Transactional Invariants",
                        "## 3. High-Level Engine Architecture & Transaction Flow (include clean Mermaid diagram)"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_02_architecture_and_mechanics.md",
                    title="Lesson 2: Storage Architecture & On-Disk Layouts",
                    audience="Database engineers needing byte-level mechanical understanding",
                    goal="Dissect page formats, buffer manager eviction algorithms, and index traversal paths",
                    sections=[
                        "## 1. Slotted Page Layouts, Tuples & Free-Space Maps",
                        "## 2. Buffer Pool Management & LRU-K / 2Q Eviction Algorithms",
                        "## 3. Index Mechanics (B+Tree, LSM Tree, or GiST/GIN internals)"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_03_deep_dive_and_concurrency.md",
                    title="Lesson 3: Concurrency Control, WAL & Crash Recovery",
                    audience="Principal database architects and systems engineers",
                    goal="Deep dive into MVCC snapshot isolation, lock trees, WAL write-ahead logging, and ARIES recovery",
                    sections=[
                        "## 1. MVCC, Multi-Version Mechanics & Vacuum Optimization",
                        "## 2. Lock Managers, Two-Phase Locking (2PL) & Deadlock Detection",
                        "## 3. Write-Ahead Logging (WAL), Checkpointing & Crash Recovery"
                    ]
                ),
                LessonTemplate(
                    filename="labs.md",
                    title="Operational Verification Labs",
                    audience="Hands-on database practitioner and DBA",
                    goal="Concrete laboratory exercises using database clients, page analyzers, and benchmark suites",
                    sections=[
                        "## Objective & Database Environment Setup",
                        "## Exercise 1: Storage Page & Internal Memory Inspection",
                        "## Exercise 2: Concurrency Contention & Lock Graph Analysis",
                        "## Exercise 3: Crash Simulation & WAL Recovery Replay",
                        "## Production Diagnostic Cheat Sheet & Verification Checklist"
                    ]
                )
            ],
            toolchain=self.get_toolchain(),
            style_directives=self.get_base_style_directive(),
            latex_policy="optional"
        )


class SoftwareEngineeringStrategy(DomainStrategy):
    """Strategy for Systems Programming, Compilers, Rust, and Low-Level Runtimes."""

    def get_toolchain(self) -> Toolchain:
        return Toolchain(
            environment_type=LabEnvironmentType.CODE,
            primary_language="Rust / C++ / Go",
            frameworks=["Cargo", "LLVM", "GCC/Clang"],
            diagnostic_tools=["GDB", "LLDB", "Valgrind", "AddressSanitizer", "ThreadSanitizer", "cargo-flamegraph"],
            verification_commands=["cargo test", "cargo check", "cargo bench"],
            setup_instructions="Systems toolchain: install rustup (Cargo, rustc), clang, lldb, and valgrind"
        )

    def get_blueprint(self, subtopic_title: str, category_title: str) -> CurriculumBlueprint:
        return CurriculumBlueprint(
            lessons=[
                LessonTemplate(
                    filename="lesson_01_foundations_and_invariants.md",
                    title="Lesson 1: Foundations & Computational Invariants",
                    audience="Senior software engineers, compiler engineers, and systems programmers",
                    goal="Establish formal mental models, type system invariants, and computational complexity bounds",
                    sections=[
                        "## Curriculum Roadmap",
                        "## 1. Formal Problem Space & Theoretical Formulation",
                        "## 2. Non-Negotiable Invariants & Safety Guarantees",
                        "## 3. High-Level Subsystem Architecture & Execution Flow (include clean Mermaid diagram)"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_02_architecture_and_mechanics.md",
                    title="Lesson 2: Core Architecture & Memory Representation",
                    audience="Systems engineers needing deep mechanical understanding",
                    goal="Dissect data representation, pointer indirection, cache alignment, and instruction generation",
                    sections=[
                        "## 1. Data Representation, Struct Packing & Memory Alignment",
                        "## 2. The Execution Critical Path & State Machine Transformations",
                        "## 3. Instruction Dispatch, Inlining & Compiler Optimization Boundaries"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_03_deep_dive_and_concurrency.md",
                    title="Lesson 3: Advanced Optimization, Concurrency & Failure Modes",
                    audience="Principal software engineers and systems architects",
                    goal="In-depth analysis of multi-threaded contention, lockless algorithms, memory reordering, and sanitizer diagnostics",
                    sections=[
                        "## 1. Memory Models, Atomics & Lockless Primitives",
                        "## 2. Cache Line Bouncing, False Sharing & CPU Saturation",
                        "## 3. Undefined Behavior, Race Conditions & Failure Mitigations"
                    ]
                ),
                LessonTemplate(
                    filename="labs.md",
                    title="Operational Verification Labs",
                    audience="Hands-on software engineer and systems programmer",
                    goal="Concrete laboratory exercises using language toolchains, sanitizers, and performance profilers",
                    sections=[
                        "## Objective & Toolchain Setup",
                        "## Exercise 1: AST, IR & Disassembly Analysis",
                        "## Exercise 2: Cache Miss & Throughput Profiling",
                        "## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics",
                        "## Developer Cheat Sheet & Toolchain Checklist"
                    ]
                )
            ],
            toolchain=self.get_toolchain(),
            style_directives=self.get_base_style_directive(),
            latex_policy="optional"
        )


# ============================================================================
# NON-COMPUTING DOMAIN STRATEGIES
# ============================================================================

class ArtsMusicStrategy(DomainStrategy):
    """Strategy for Music Theory, Composition, Audio Production, and Synthesizers."""

    def get_toolchain(self) -> Toolchain:
        return Toolchain(
            environment_type=LabEnvironmentType.SOFTWARE_GUI,
            frameworks=["Digital Audio Workstation (DAW - Ableton / Logic / Reaper)", "MuseScore / Dorico", "Modular Synth Simulators (VCV Rack)"],
            diagnostic_tools=["Spectrum Analyzer (Voxengo SPAN)", "Oscilloscope", "MIDI Monitor", "Loudness Meter (LUFS)"],
            verification_commands=[],
            setup_instructions="Music production environment: Digital Audio Workstation (DAW), virtual instruments, MIDI monitor, and spectrum analyzer"
        )

    def get_blueprint(self, subtopic_title: str, category_title: str) -> CurriculumBlueprint:
        return CurriculumBlueprint(
            lessons=[
                LessonTemplate(
                    filename="lesson_01_foundations_and_theory.md",
                    title="Lesson 1: Foundations, Harmonic Principles & Invariants",
                    audience="Composers, music producers, audio engineers, and instrumentalists",
                    goal="Establish theoretical acoustic principles, harmonic syntax, voice-leading rules, and aesthetic invariants",
                    sections=[
                        "## Curriculum Roadmap",
                        "## 1. Acoustic Physics & Historical Harmonic Problem Space",
                        "## 2. Fundamental Syntax: Scales, Intervals, Voice Leading & Core Invariants",
                        "## 3. Formal Structural Flow & Harmonic Architecture (include clean Mermaid diagram)"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_02_composition_techniques.md",
                    title="Lesson 2: Compositional Mechanics, Arrangement & Orchestration",
                    audience="Composers, arrangers, and sound designers",
                    goal="Dissect voice distribution, timbre blending, motivic development, and modulation mechanics",
                    sections=[
                        "## 1. Motivic Development, Inversion & Rhythmic Transformation",
                        "## 2. Counterpoint Mechanics & Polyphonic Voice Distribution",
                        "## 3. Orchestral Color, Timbre Selection & Register Allocation"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_03_production_and_acoustics.md",
                    title="Lesson 3: Advanced Audio DSP, Dynamic Range & Mixing Dynamics",
                    audience="Producers, audio engineers, and mastering specialists",
                    goal="In-depth analysis of signal flow, harmonic saturation, dynamic phase alignment, and stereo imaging",
                    sections=[
                        "## 1. Signal Flow Architecture & Audio Routing Topologies",
                        "## 2. Frequency Carving, Dynamic Phase Interactions & Transient Shaping",
                        "## 3. Spatial Acoustics, Reverb Decay Invariants & Stereo Coherence"
                    ]
                ),
                LessonTemplate(
                    filename="labs.md",
                    title="Operational Verification Labs",
                    audience="Hands-on music composer, producer, and audio practitioner",
                    goal="Practical hands-on exercises composing, scoring, synthesizing, and critically analyzing audio projects",
                    sections=[
                        "## Objective & DAW / Studio Setup",
                        "## Exercise 1: Practical Composition & Voice-Leading Realization",
                        "## Exercise 2: Timbre Synthesis, Waveform Shaping & Modulation Routing",
                        "## Exercise 3: Dynamic Mixing, Spectrum Analysis & Audio Stress Testing",
                        "## Studio Diagnostic Cheat Sheet & Verification Checklist"
                    ]
                )
            ],
            toolchain=self.get_toolchain(),
            style_directives=self.get_base_style_directive(),
            latex_policy="optional"
        )


class ArtsVisualStrategy(DomainStrategy):
    """Strategy for Visual Arts, Visual Media, Design, and 3D Graphics.

    Arts used to have only the music strategy, so drawing, design and 3D courses
    were written for "composers and audio engineers" and got DAW labs."""

    def get_toolchain(self) -> Toolchain:
        return Toolchain(
            environment_type=LabEnvironmentType.SOFTWARE_GUI,
            frameworks=["Traditional media (pencil, charcoal, paint, clay)", "Raster / vector editors (Krita, GIMP, Inkscape, Photoshop, Illustrator)", "3D suites (Blender, Maya)", "Design tools (Figma, Penpot)", "Camera and editing software (DaVinci Resolve)"],
            diagnostic_tools=["Value / greyscale check", "Histogram and waveform scopes", "Colour picker and contrast checker", "Mirror / flip-canvas check", "Critique rubric"],
            verification_commands=[],
            setup_instructions="Visual studio: sketchbook or canvas and drawing/painting materials, or the relevant digital tool (image editor, 3D suite, design tool, camera), with reference images and a critique rubric"
        )

    def get_blueprint(self, subtopic_title: str, category_title: str) -> CurriculumBlueprint:
        return CurriculumBlueprint(
            lessons=[
                LessonTemplate(
                    filename="lesson_01_foundations_and_principles.md",
                    title="Lesson 1: Foundations, Visual Principles & Core Vocabulary",
                    audience=f"Artists, designers and visual practitioners learning {subtopic_title}, from motivated beginners upward",
                    goal="Establish the core visual principles, vocabulary and perceptual foundations the craft is built on",
                    sections=[
                        "## Curriculum Roadmap",
                        "## 1. Why It Works: Perception, History & the Problem the Craft Solves",
                        "## 2. Core Principles, Vocabulary & Rules of Thumb",
                        "## 3. How a Piece Comes Together: Workflow Overview (include clean Mermaid diagram)"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_02_techniques_and_process.md",
                    title="Lesson 2: Techniques, Tools & Working Process",
                    audience=f"Practitioners building hands-on skill in {subtopic_title}",
                    goal="Teach the concrete techniques, tool settings and step-by-step process, with common mistakes and how to correct them",
                    sections=[
                        "## 1. Essential Techniques, Step by Step",
                        "## 2. Tools, Materials & Settings That Matter",
                        "## 3. Common Mistakes, Why They Happen & How to Fix Them"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_03_composition_and_critique.md",
                    title="Lesson 3: Composition, Style & Critique",
                    audience=f"Practitioners refining their {subtopic_title} work toward a personal, finished standard",
                    goal="Develop composition, intent and style, and a repeatable way to critique and improve finished work",
                    sections=[
                        "## 1. Composition, Hierarchy & Visual Storytelling",
                        "## 2. Style, Intent & Studying Master Works",
                        "## 3. Critique Method, Iteration & Presenting Work"
                    ]
                ),
                LessonTemplate(
                    filename="labs.md",
                    title="Studio Practice Labs",
                    audience=f"Hands-on {category_title} learner working in a studio or with the relevant digital tool",
                    goal=f"Practical exercises that build {subtopic_title} skill through making, observing and critiquing real work",
                    sections=[
                        "## Objective & Studio Setup",
                        "## Exercise 1: Observation & Fundamentals Drill",
                        "## Exercise 2: Technique Study, Step by Step",
                        "## Exercise 3: Finished Piece & Self-Critique",
                        "## Critique Checklist & Common Fixes"
                    ]
                )
            ],
            toolchain=self.get_toolchain(),
            style_directives=self.get_base_style_directive(),
            latex_policy="optional"
        )


class NaturalSciencesStrategy(DomainStrategy):
    """Strategy for Physics, Chemistry, Biology, Astronomy, and Earth Sciences."""

    def get_toolchain(self) -> Toolchain:
        return Toolchain(
            environment_type=LabEnvironmentType.FIELDWORK,
            primary_language="Python / Scientific Tools",
            frameworks=["NumPy", "SciPy", "Matplotlib", "Avogadro / PyMOL", "Astropy"],
            diagnostic_tools=["Spectrophotometry", "Microscopy", "Oscilloscopes", "Calorimeters", "Sensor telemetry"],
            verification_commands=["python -c 'import scipy; print(scipy.__version__)'"],
            setup_instructions="Scientific laboratory bench: measurement instruments, analytical sensors, and Python scientific environment (NumPy, SciPy, Matplotlib)"
        )

    def get_blueprint(self, subtopic_title: str, category_title: str) -> CurriculumBlueprint:
        return CurriculumBlueprint(
            lessons=[
                LessonTemplate(
                    filename="lesson_01_foundations_and_invariants.md",
                    title="Lesson 1: First-Principles Physical Laws & Conservation Invariants",
                    audience="Scientists, physicists, researchers, and advanced students",
                    goal="Establish unshakeable theoretical grounding, conservation laws, and axiomatic physical invariants",
                    sections=[
                        "## Curriculum Roadmap",
                        "## 1. First-Principles Problem Space & Historical Phenomenon",
                        "## 2. Conservation Invariants & Mathematical Laws",
                        "## 3. High-Level Phenomenological Model (include clean Mermaid diagram)"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_02_mechanisms_and_dynamics.md",
                    title="Lesson 2: Physical Mechanisms & Dynamical Equations",
                    audience="Empirical researchers and experimental scientists",
                    goal="Dissect mathematical derivations, reaction kinetics, field interactions, and state transitions",
                    sections=[
                        "## 1. Governing Differential Equations & Analytical Derivations",
                        "## 2. Microscopic vs. Macroscopic Phase Transitions",
                        "## 3. Energy Transfer, Entropy & Rate Limitations"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_03_experimental_methods.md",
                    title="Lesson 3: Measurement Limits, Perturbation & Boundary Failures",
                    audience="Senior researchers and experimental laboratory leaders",
                    goal="In-depth analysis of systematic error propagation, non-linear perturbations, and extreme conditions",
                    sections=[
                        "## 1. Instrument Sensitivity, Noise Floors & Uncertainty Propagation",
                        "## 2. Non-Linear Perturbations & Chaotic Regimes",
                        "## 3. Extreme Boundary Conditions & Phase Breakdown"
                    ]
                ),
                LessonTemplate(
                    filename="labs.md",
                    title="Operational Verification Labs",
                    audience="Hands-on experimental scientist and laboratory researcher",
                    goal="Concrete empirical exercises measuring physical constants, modeling phenomena, and analyzing error states",
                    sections=[
                        "## Objective & Laboratory Bench Setup",
                        "## Exercise 1: Empirical Observation & Measurement Protocol",
                        "## Exercise 2: Parameter Variation, Calibration & Response Curve Plotting",
                        "## Exercise 3: Boundary Condition Stress Testing & Uncertainty Analysis",
                        "## Laboratory Cheat Sheet & Metric Verification Guide"
                    ]
                )
            ],
            toolchain=self.get_toolchain(),
            style_directives=self.get_base_style_directive(),
            latex_policy="required"
        )


class FormalSciencesStrategy(DomainStrategy):
    """Strategy for Pure Mathematics, Applied Math, Logic, and Discrete Mathematics."""

    def get_toolchain(self) -> Toolchain:
        return Toolchain(
            environment_type=LabEnvironmentType.ANALYTICAL,
            primary_language="Python / CAS / Proof Assistants",
            frameworks=["SymPy", "NumPy", "Lean / Coq", "SageMath"],
            diagnostic_tools=["Symbolic algebra engines", "Automated theorem provers"],
            verification_commands=["python -c 'import sympy; print(sympy.__version__)'"],
            setup_instructions="Formal computing environment: Python 3.11+ with SymPy, NumPy, and SageMath or interactive proof assistant"
        )

    def get_blueprint(self, subtopic_title: str, category_title: str) -> CurriculumBlueprint:
        return CurriculumBlueprint(
            lessons=[
                LessonTemplate(
                    filename="lesson_01_axioms_and_invariants.md",
                    title="Lesson 1: Axiomatic Foundations & Formal Invariants",
                    audience="Mathematicians, logicians, and theoretical computer scientists",
                    goal="Establish axiomatic foundations, definitions, and invariant properties",
                    sections=[
                        "## Curriculum Roadmap",
                        "## 1. Historical Problem Space & Axiomatic Motivation",
                        "## 2. Fundamental Definitions & Non-Negotiable Axiomatic Invariants",
                        "## 3. Structural Mapping & Categorical Diagram (include clean Mermaid diagram)"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_02_theorems_and_proofs.md",
                    title="Lesson 2: Core Theorems & Rigorous Proof Mechanics",
                    audience="Pure and applied mathematicians needing mechanical proof comprehension",
                    goal="Provide rigorous, complete proofs of central theorems and lemma decompositions",
                    sections=[
                        "## 1. Foundational Lemma Formulations",
                        "## 2. The Main Theorem: Rigorous Proof & Step-by-Step Derivation",
                        "## 3. Canonical Counterexamples & Boundary Constraints"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_03_advanced_structures.md",
                    title="Lesson 3: Advanced Morphisms, Dualities & Applications",
                    audience="Research mathematicians and theoretical specialists",
                    goal="Explore structural dualities, algebraic isomorphisms, and asymptotic behavior",
                    sections=[
                        "## 1. Morphisms, Functors & Structural Dualities",
                        "## 2. Asymptotic Bounds & Limiting Behaviors",
                        "## 3. Applied Realizations & Theoretical Impact"
                    ]
                ),
                LessonTemplate(
                    filename="labs.md",
                    title="Operational Verification Labs",
                    audience="Analytical mathematician and computational practitioner",
                    goal="Verify mathematical properties through computational symbolic execution and formal proof verification",
                    sections=[
                        "## Objective & Mathematical Computing Setup",
                        "## Exercise 1: Computational Verification of Core Theorems",
                        "## Exercise 2: Boundary Value Stress Testing & Singularities",
                        "## Exercise 3: Algorithmic Implementation of Formal Structures",
                        "## Formal Axioms Cheat Sheet & Verification Reference"
                    ]
                )
            ],
            toolchain=self.get_toolchain(),
            style_directives=self.get_base_style_directive(),
            latex_policy="required"
        )


class MotorsportsStrategy(DomainStrategy):
    """Strategy for Motorsports, Vehicle Dynamics, Race Engineering, and Telemetry."""

    def get_toolchain(self) -> Toolchain:
        return Toolchain(
            environment_type=LabEnvironmentType.SOFTWARE_GUI,
            primary_language="Python / MATLAB",
            frameworks=["MoTeC i2 Pro", "Chassis Sim", "CAN bus analyzers", "RaceCapture"],
            diagnostic_tools=["Telemetry loggers", "Tire temperature pyrometers", "Suspension damper potentiometers", "GPS accelerometer traces"],
            verification_commands=[],
            setup_instructions="Motorsports telemetry environment: MoTeC i2 Pro, telemetry CSV data logs, and suspension kinematics simulation software"
        )

    def get_blueprint(self, subtopic_title: str, category_title: str) -> CurriculumBlueprint:
        return CurriculumBlueprint(
            lessons=[
                LessonTemplate(
                    filename="lesson_01_foundations_and_invariants.md",
                    title="Lesson 1: Vehicle Dynamics Physics & Traction Invariants",
                    audience="Race engineers, vehicle dynamicists, and performance drivers",
                    goal="Establish tire contact patch physics, load transfer equations, and mechanical grip invariants",
                    sections=[
                        "## Curriculum Roadmap",
                        "## 1. Dynamic Contact Patch & Grip Problem Space",
                        "## 2. Load Transfer, Slip Angles & Invariant In-Corner Dynamics",
                        "## 3. Chassis Kinematic Topology & Roll Center Architecture (include clean Mermaid diagram)"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_02_mechanics_and_telemetry.md",
                    title="Lesson 2: Suspension Kinematics, Aerodynamics & Telemetry Analysis",
                    audience="Trackside data engineers and race mechanics",
                    goal="Dissect damper velocity histograms, aero balance maps, and throttle/braking telemetry traces",
                    sections=[
                        "## 1. Damper Kinematics & Velocity Histogram Analysis",
                        "## 2. Aerodynamic Center of Pressure & Ride Height Sensitivity",
                        "## 3. G-G Friction Circle & Corner Entry/Exit Telemetry Dissection"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_03_tuning_and_failure_modes.md",
                    title="Lesson 3: Setup Optimization, Thermal Degradation & Dynamic Instability",
                    audience="Chief race engineers and technical directors",
                    goal="Analyze snap-oversteer transients, tire thermal degradation models, and wet-weather adaptations",
                    sections=[
                        "## 1. Transient Oversteer/Understeer Instability & Differential Locking",
                        "## 2. Tire Thermal Hysteresis & Blistering/Graining Failure Modes",
                        "## 3. Endurance Fuel Strategy & Brake Energy Dissipation"
                    ]
                ),
                LessonTemplate(
                    filename="labs.md",
                    title="Operational Verification Labs",
                    audience="Hands-on trackside race engineer and data analyst",
                    goal="Step-by-step practical laboratory analyzing real telemetry traces, damper adjustments, and setup sheets",
                    sections=[
                        "## Objective & Telemetry Environment Setup",
                        "## Exercise 1: Telemetry Data Import & Driver Trace Correlation",
                        "## Exercise 2: Damper Velocity Histogram Tuning & Anti-Roll Bar Optimization",
                        "## Exercise 3: Tire Temperature Analysis & Wear Modeling",
                        "## Race Engineering Diagnostic Cheat Sheet & Setup Matrix"
                    ]
                )
            ],
            toolchain=self.get_toolchain(),
            style_directives=self.get_base_style_directive(),
            latex_policy="optional"
        )


class GenericDomainStrategy(DomainStrategy):
    """Clean fallback strategy for Business, Humanities, Economics, Crafts, and Languages."""

    def __init__(self, domain: str):
        self.domain = domain

    def get_toolchain(self) -> Toolchain:
        return Toolchain(
            environment_type=LabEnvironmentType.ANALYTICAL,
            frameworks=["Domain Analytical Models", "Case Study Frameworks", "Quantitative Spreadsheets"],
            diagnostic_tools=["Empirical audit rubrics", "Statistical models"],
            verification_commands=[],
            setup_instructions=f"Analytical research environment and simulation tools native to {self.domain.replace('_', ' ').title()}"
        )

    def get_blueprint(self, subtopic_title: str, category_title: str) -> CurriculumBlueprint:
        domain_title = self.domain.replace("_", " ").title()
        return CurriculumBlueprint(
            lessons=[
                LessonTemplate(
                    filename="lesson_01_foundations_and_invariants.md",
                    title="Lesson 1: Foundations, First Principles & Core Invariants",
                    audience=f"Advanced practitioners, analysts, and specialists in {category_title}",
                    goal="Establish theoretical grounding, core principles, and foundational invariants",
                    sections=[
                        "## Curriculum Roadmap",
                        "## 1. First-Principles Problem Space & Structural Realities",
                        "## 2. Core Invariants, Systemic Constraints & Axiomatic Principles",
                        f"## 3. High-Level Conceptual Framework & Structural Flow (include clean Mermaid diagram)"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_02_mechanics_and_dynamics.md",
                    title="Lesson 2: Core Architecture & Operational Mechanics",
                    audience=f"Practitioners needing deep functional and structural understanding of {category_title}",
                    goal="Dissect functional components, systemic interactions, and critical execution paths",
                    sections=[
                        "## 1. Internal Structural Organization & Component Interplay",
                        "## 2. Dynamic Processes, Flow of Value/Information & State Transitions",
                        "## 3. Critical Path Analysis: From Input to Verified Outcome"
                    ]
                ),
                LessonTemplate(
                    filename="lesson_03_advanced_strategy.md",
                    title="Lesson 3: Advanced Optimization, Boundary Conditions & Failure Modes",
                    audience=f"Lead strategists, senior architects, and subject-matter directors",
                    goal="In-depth analysis of optimization, boundary dynamics, edge cases, and systemic breakdown",
                    sections=[
                        "## 1. High-Performance Optimization & Scaling Dynamics",
                        "## 2. Boundary Conditions, Complex Stress & Non-Linear Feedback Loops",
                        "## 3. Systemic Failure Modes, Diagnostic Indicators & Defensive Invariants"
                    ]
                ),
                LessonTemplate(
                    filename="labs.md",
                    title="Operational Verification Labs",
                    audience=f"Hands-on practitioner and operational specialist in {category_title}",
                    goal=f"Step-by-step practical laboratory exercises utilizing tools, models, or simulation methods native to {domain_title}",
                    sections=[
                        "## Objective & Operational Lab Setup",
                        "## Exercise 1: Foundational Practical Implementation",
                        "## Exercise 2: Parameter Variation & Empirical Analysis",
                        "## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol",
                        "## Operational Reference Guide & Diagnostic Checklist"
                    ]
                )
            ],
            toolchain=self.get_toolchain(),
            style_directives=self.get_base_style_directive(),
            latex_policy="optional"
        )


# ============================================================================
# STRATEGY REGISTRY & DISPATCHER
# ============================================================================

# Arts categories that are not music (see topics/arts/). creative_software stays
# with music: most of its courses are DAWs (Ableton, Cubase, Logic Pro).
VISUAL_ARTS_CATEGORIES = {"visual_arts", "visual_media", "design", "3d_graphics"}
# Visual courses that sit inside a music category (creative_software also holds
# Ableton, Cubase and Logic). Without this they got the music blueprint.
VISUAL_ARTS_COURSES = {"adobe_creative_cloud"}


class StrategyRegistry:
    """Central registry mapping domain/discipline pairs to dedicated strategies."""

    def __init__(self):
        self._computing_strategies: Dict[str, DomainStrategy] = {
            "ai": AIMLStrategy(),
            "machine_learning": AIMLStrategy(),
            "deep_learning": AIMLStrategy(),
            "mlops": AIMLStrategy(),
            "rag": AIMLStrategy(),
            "security": SecurityHardwareStrategy(),
            "hardware_hacking": SecurityHardwareStrategy(),
            "infrastructure": InfrastructureStrategy(),
            "kubernetes": InfrastructureStrategy(),
            "ebpf": InfrastructureStrategy(),
            "networking": InfrastructureStrategy(),
            "linux_kernel": InfrastructureStrategy(),
            "sre": InfrastructureStrategy(),
            "data": DatabaseStrategy(),
            "database": DatabaseStrategy(),
            "postgresql": DatabaseStrategy(),
            "systems": SoftwareEngineeringStrategy(),
            "compilers": SoftwareEngineeringStrategy(),
            "rust_systems": SoftwareEngineeringStrategy(),
        }

        self._domain_strategies: Dict[str, DomainStrategy] = {
            "arts": ArtsMusicStrategy(),
            "natural_sciences": NaturalSciencesStrategy(),
            "formal_sciences": FormalSciencesStrategy(),
            "motorsports": MotorsportsStrategy(),
        }

    def get_strategy(self, domain: str, category: str, subtopic_id: str = "") -> DomainStrategy:
        domain_lower = domain.lower()
        cat_lower = category.lower()

        # Arts: music categories keep the music strategy; visual ones do not.
        if domain_lower == "arts" and (cat_lower in VISUAL_ARTS_CATEGORIES or subtopic_id.lower() in VISUAL_ARTS_COURSES):
            return ArtsVisualStrategy()

        # 1. Specialized computing strategies
        if domain_lower == "computing":
            for key, strategy in self._computing_strategies.items():
                if key in cat_lower:
                    return strategy
            return SoftwareEngineeringStrategy()

        # 2. Specialized non-computing domain strategies
        if domain_lower in self._domain_strategies:
            return self._domain_strategies[domain_lower]

        # 3. Clean domain-aware generic strategy (Business, Economics, Humanities, Crafts, Languages, Health)
        return GenericDomainStrategy(domain=domain_lower)


# ============================================================================
# UNIFIED PROMPT BUILDER
# ============================================================================

class PromptBuilder:
    """Builds authoritative LLM prompts with complete domain context and zero copy-paste."""

    @staticmethod
    def build_lesson_prompt(
        template: LessonTemplate,
        subtopic_title: str,
        domain_title: str,
        category_title: str,
        style_directives: str,
        latex_policy: str
    ) -> str:
        latex_clause = {
            "forbidden": "FORMATTING MANDATE: STRICTLY NO LaTeX ($...$ or $$...$$). Use clean plain-text notation or code blocks.",
            "required": "FORMATTING MANDATE: Use standard LaTeX for all mathematical expressions ($...$ inline, $$...$$ display block).",
            "optional": "FORMATTING MANDATE: Standard Markdown formatting. Use LaTeX if beneficial for complex equations."
        }.get(latex_policy, "")

        sections_formatted = "\n\n".join(template.sections)

        return f"""Write {template.title} for the masterclass curriculum on '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: {template.audience}
Goal: {template.goal}

{style_directives}

{latex_clause}

Structure:
# {template.title}

{sections_formatted}

Remember: Write in rich, continuous book prose like an authoritative textbook author.
Output publication-grade Markdown only."""

    @staticmethod
    def build_lab_prompt(
        template: LessonTemplate,
        subtopic_title: str,
        domain_title: str,
        category_title: str,
        toolchain: Toolchain,
        style_directives: str
    ) -> str:
        sections_formatted = "\n\n".join(template.sections)

        toolchain_desc = [f"Environment Type: {toolchain.environment_type.value}"]
        if toolchain.primary_language:
            toolchain_desc.append(f"Primary Toolchain / Language: {toolchain.primary_language}")
        if toolchain.frameworks:
            toolchain_desc.append(f"Authentic Tooling / Frameworks: {', '.join(toolchain.frameworks)}")
        if toolchain.diagnostic_tools:
            toolchain_desc.append(f"Diagnostic Instruments: {', '.join(toolchain.diagnostic_tools)}")
        if toolchain.verification_commands:
            toolchain_desc.append(f"Verification Commands: {', '.join(toolchain.verification_commands)}")
        if toolchain.setup_instructions:
            toolchain_desc.append(f"Setup Instructions: {toolchain.setup_instructions}")

        toolchain_block = "\n".join(toolchain_desc)

        return f"""Write the complete {template.title} guide for '{subtopic_title}'.
Domain: '{domain_title}' | Discipline/Course: '{category_title}'.

Target Audience: {template.audience}
Goal: {template.goal}

{style_directives}

DOMAIN TOOLCHAIN CONTEXT:
{toolchain_block}

Structure:
# {template.title}: {subtopic_title}

{sections_formatted}

Rules:
- Provide full, executable exercises, code, commands, or operational procedures with ZERO placeholders.
- Every exercise must strictly utilize authentic tooling and procedures native to '{domain_title}' and '{category_title}'.
- Output publication-grade Markdown only."""


GLOBAL_REGISTRY = StrategyRegistry()

def build_topic_modules(domain: str, category: str, subtopic_id: str, subtopic_title: str) -> List[Dict[str, str]]:
    """
    Clean, domain-aware module builder.
    Dispatches to dedicated DomainStrategy and renders structured lesson and lab prompts.
    """
    domain_title = domain.replace("_", " ").title()
    category_title = category.replace("_", " ").title()

    strategy = GLOBAL_REGISTRY.get_strategy(domain, category, subtopic_id)
    blueprint = strategy.get_blueprint(subtopic_title, category_title)

    modules = []
    for lesson in blueprint.lessons:
        if lesson.filename == "labs.md":
            prompt = PromptBuilder.build_lab_prompt(
                template=lesson,
                subtopic_title=subtopic_title,
                domain_title=domain_title,
                category_title=category_title,
                toolchain=blueprint.toolchain,
                style_directives=blueprint.style_directives
            )
        else:
            prompt = PromptBuilder.build_lesson_prompt(
                template=lesson,
                subtopic_title=subtopic_title,
                domain_title=domain_title,
                category_title=category_title,
                style_directives=blueprint.style_directives,
                latex_policy=blueprint.latex_policy
            )

        modules.append({
            "filename": lesson.filename,
            "title": lesson.title,
            "prompt": prompt
        })

    return modules
