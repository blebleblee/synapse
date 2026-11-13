# Changelog

All notable changes to the **Synapse AI-Native Learning Workbench** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
  * Seamlessly connects to local Ollama clusters (`127.0.0.1`, LAN nodes) and low-latency cloud gateways (`apikey.vnaipro.app` routed to Claude Opus 5.5).
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
* **macOS Desktop App:** `Synapse Workbench-1.0.0-arm64.dmg` & `Synapse Workbench-1.0.0-arm64-mac.zip`
* **Python Distribution:** `synapse-1.0.0-py3-none-any.whl` & `synapse-1.0.0.tar.gz`
* **CLI Utility:** `bin/synapse` (`serve`, `doctor`, `audit`, `generate`, `enhance`, `pack`)
