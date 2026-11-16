# Changelog

All notable changes to the **Synapse AI-Native Learning Workbench** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-11-16

### Summary
Milestone release marking the full 100.0% completion of the **Synapse Global Masterclass Curriculum** (539 topics across 12 domains, comprising 2,945 lessons and operational verification labs). This release packages the complete master curriculum into a unified 33.5 MB distribution (`synapse_complete_curriculum.synpack`), upgrades over 3,100 diagrams to vector Mermaid.js flowcharts, adds official KaTeX `mhchem` chemical formula rendering, and prepares the repository for public release on GitHub.

---

### Key Features & Enhancements

#### 1. Complete Global Polymath Curriculum (539 / 539 Topics)
* **100% Taxonomical Coverage:** All 12 domains fully authored and verified:
  * **Computing & Systems:** 162 topics (10.6 MB)
  * **Arts & Music:** 67 topics (3.4 MB)
  * **Crafts & Fabrication:** 60 topics (2.7 MB)
  * **Business & Strategy:** 41 topics (2.5 MB)
  * **Engineering:** 39 topics (2.8 MB)
  * **Humanities:** 39 topics (2.5 MB)
  * **Formal Sciences:** 33 topics (2.2 MB)
  * **Economics:** 32 topics (2.3 MB)
  * **Natural Sciences:** 30 topics (2.3 MB)
  * **Health Sciences:** 20 topics (1.0 MB)
  * **Motorsports:** 10 topics (0.7 MB)
  * **Languages:** 6 topics (0.5 MB)
* **Master Unified Addon:** Introduced `synapse_complete_curriculum.synpack` (33.5 MB), enabling 1-click installation of all 539 topics and 2,945 lessons/labs at once.

#### 2. Vector Graphics & Mathematical Rendering Engine
* **Vector Mermaid.js Upgrades:** Converted over 900 legacy ASCII box diagrams into modern, vector Mermaid.js flowcharts (` ```mermaid flowchart TD ... ``` `). Over 50% of all curriculum units (1,484 files) now feature vector Mermaid diagrams (3,172 total diagrams across the workspace).
* **High-Contrast Dark Mode Rendering:** Automated luminance-based text contrast enforcement for Mermaid nodes in dark mode.
* **KaTeX Chemical Equations (`mhchem`):** Integrated official `katex/contrib/mhchem` extension into both the React desktop renderer and headless validation suite for native chemical formula rendering (e.g. `\ce{C4H10 -> 2 C2H5}`).
* **HTML Comparison Escaping:** Fixed bare less-than numerical comparisons (`< 0.2s`, `< 10%`) to prevent browser HTML parsers from mistaking comparisons for invalid HTML tags.

#### 3. Desktop UI & Onboarding Polish
* **Helpful Empty State:** Added an intuitive Empty State to the sidebar when no topics are installed, with an embedded one-click **`[ Open Curriculum Store ]`** button.
* **Visual Documentation:** Added a comprehensive visual guide in `README.md` explaining the App Shell + Modular SynPack architecture and 4 distinct installation paths.

#### 4. Infrastructure & Verification
* **Zero-Defect Quality Linter:** Scanned all 2,945 curriculum files with 0 errors, validating terminal sentence completion, multi-section invariants, and balanced code blocks.
* **Headless Render Validation:** Verified 133,544 KaTeX math formulas and 3,172 Mermaid diagrams through headless browser parsers (`validate_render.mjs`).
* **Automated Test Suite:** 59 / 59 Pytest tests passing (100%).

---

## [1.0.0] - 2026-11-13

### Summary
Initial production release of **Synapse** — the AI-native engineering and polymath learning workbench. Synapse combines textbook-grade masterclass curricula (O'Reilly / MIT Press depth) with an interactive Socratic AI Mentor, an embedded PTY terminal with host and sandbox execution modes, a responsive Cytoscape knowledge graph, and distributed multi-node inference clustering.

Curriculum domains are distributed modularly via the Synapse Package Manager (`synpack/v1`), shipping with the complete core Computing masterclass suite and enabling additional domain and localized language bundles as modular add-ons.

---

### Key Features & Architectural Highlights

#### 1. Socratic Workbench & Desktop Shell
* **Native Desktop Shell (macOS arm64):** Production Electron shell orchestrating native window lifecycle, menu bar controls, and automatic FastAPI backend sidecar management.
* **Interactive Terminal Drawer:**
  * Dual-mode terminal supporting both native Host OS execution and isolated Docker sandboxes (`Dockerfile.sandbox`).
  * Resilient PTY line discipline enabling `ICRNL` translation (`\r` $\rightarrow$ `\n`), ensuring instant execution on Enter keystrokes.
  * Real-time ANSI and OSC terminal escape sequence sanitization to prevent prompt redraw loops.
  * Host safety guard intercepting high-risk commands (`rm -rf /`, `mkfs`, fork bombs) until explicit confirmation is provided.
* **Multilingual Socratic AI Mentor:**
  * Context-aware conversational tutor automatically grounded in the active lesson, syllabus invariants, and terminal buffer.
  * Exact command tracking (`LAST_TERMINAL_COMMAND`) to diagnose terminal inputs without confusing commands with output text.
  * Full localization across 5 languages (English, Čeština, Deutsch, Español, Русский) with prompt-level language mandate injection.
* **Theme & Appearance Engine:**
  * 7 curated base themes (Default Dark, Cyberpunk, Forest, Monokai, Nord, Midnight, Paper White).
  * 5 accent color options (Indigo, Amber, Rose, Emerald, Cyan), typography choices (Sans, Serif, Mono), and reader line-height scaling.
  * Redesigned compact domain sort toggle with alphabetical and progress-oriented sorting modes.
* **System & Maintenance Dashboard:**
  * Dedicated System & Maintenance tab in Settings for runtime data cleanup and one-click lesson completion progress reset.

#### 2. Learning Engine & Distributed Inference
* **Multi-Node Cluster & Cloud Gateway:**
  * Seamlessly connects to local Ollama clusters (`127.0.0.1`, LAN nodes) and low-latency cloud gateways routed to Anthropic Claude Sonnet & Opus.
  * Dynamic cluster host normalization and node-specific model pinning saved to `.synapse_node_pins.json`.
* **Parallel Content Enhancement Pipeline (`enhancer.py`):**
  * Concurrent thread pool engine with automated exponential backoff retries and 600-second socket timeouts to handle massive 8,192-token masterclass files.
* **Pre-Commit Gatekeeper & Semantic Linter (`linter.py`):**
  * Pre-save validation stripping outer code fences (` ```markdown `).
  * Automated Mermaid subgraph ID normalization (`subgraph sub_id ["Title"]`).
  * Cross-domain bleed and template stub detection blocking generic boilerplate or misplaced toolchains.

#### 3. Curriculum & Package Store Architecture
* **Computing Masterclass Suite:** 45 complete courses (238 files) written to O'Reilly and MIT Press standards, featuring C/Rust kernel diagnostics, distributed Raft consensus, and production Kubernetes manifests.
* **Dedicated Infrastructure Labs:** Custom operational verification labs for Cloud Native (`containerd`, OCI, Envoy), SRE (SLI/SLO error budgets, Prometheus, Chaos Mesh), DevOps (BuildKit, Trivy, Argo CD), and Systems Automation (Ansible, Terraform).
* **Modular Add-On Store (`synpack/v1`):** Complete decoupling of curriculum data from the workbench runtime, enabling curriculum expansion packs and localized translation trees to be packaged, verified, and installed via Synapse Package Manager.

---

### Packaging & Binaries Included
* **Windows Portable Desktop App:** `Synapse-Workbench-Portable-1.0.0.exe` (Zero-dependency portable executable with embedded backend sidecar; curriculum topics loaded as an external, platform-independent addon folder `./topics` alongside the `.exe`).
* **macOS Desktop App:** `Synapse Workbench-1.0.0-arm64.dmg` & `Synapse Workbench-1.0.0-arm64-mac.zip`
* **Python Distribution:** `synapse-1.0.0-py3-none-any.whl` & `synapse-1.0.0.tar.gz`
* **CLI Utility:** `bin/synapse` (`serve`, `status`, `lint`, `review`, `search`, `export`, `flashcards`, `mastery`)
