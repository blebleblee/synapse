# Synapse — AI-Native Engineering & Polymath Workbench

<p align="center">
  <img src="app/frontend/public/favicon.svg" width="96" height="96" alt="Synapse Logo" />
</p>

**Synapse** is an automated, production-grade AI learning workspace, knowledge graph, and Socratic engineering workbench. It treats the filesystem as a Git-backed database across **11 atomic domains**, **41 disciplines**, and over **360 calibrated study units** structured for deep 2–3 hour focused milestones.

---

## 1. Architecture & Taxonomy

Synapse follows a strict **4-Level Maximum Hierarchy** that eliminates monolithic cognitive overload:

$$\text{Domain (L1)} \;\longrightarrow\; \text{Discipline (L2)} \;\longrightarrow\; \text{Course (L3)} \;\longrightarrow\; \text{Study Unit (L4)}$$

### The 11 Core Domains
1. **`computing`** — Linux Kernel, Systems Programming, Infrastructure (Kubernetes, eBPF, Harvester), Security (Web, Exploitation, Hardware Hacking), AI/ML, and Data Systems.
2. **`engineering`** — Computer Architecture, Assembly (x86/ARM), Embedded Systems, Circuits, Hardware Hacking, and Robotics.
3. **`motorsports`** — Performance Driving Dynamics, Motorcycle Riding Dynamics, Vehicle Telemetry, Diagnostics & Maintenance.
4. **`crafts`** — Metalworking (TIG/MIG Welding), Precision Machining & CNC, 3D Printing, Retro Gaming Hardware & Arcade Restoration, Woodworking.
5. **`formal_sciences`** — Pure Math (Abstract Algebra, Category Theory), Applied Math (Game Theory, Cryptography), Mathematical Logic, Discrete Mathematics.
6. **`natural_sciences`** — Quantum Physics, Classical Mechanics, Organic/Physical Chemistry, Molecular Biology.
7. **`arts`** — Music Performance (Bass, Drums, Piano, Electric Guitar), Audio DSP, Modular Synthesis, Orchestral Scoring, Visual Arts.
8. **`languages`** — Germanic (English, German), Slavic (Czech, Russian), Romance (Spanish), and Comparative Linguistics.
9. **`humanities`** — Classical Philosophy, Epistemology, Global Intellectual History.
10. **`business`** — Corporate Finance, M&A, Private Equity, Market Microstructure, Wealth Management.
11. **`economics`** — Macroeconomics, Microeconomics, Game Theory, Central Banking & Monetary Policy.

---

## 2. Progressive 3-Tier Pedagogy

Every leaf study unit is calibrated to a **2–3 hour evening session** and contains:
- **`SUMMARY.md`**: Living executive summary synthesizing invariants, architecture, and user discussion takeaways. Auto-regenerates as you converse with the AI tutor.
- **`beginner/`**, **`intermediate/`**, **`advanced/`**: Progressive difficulty tiers, each containing:
  - **`FOUNDATION.md`**: First-principles mental model, core invariants, ASCII/Mermaid architecture diagrams, and common misconceptions.
  - **`LESSON.md`**: In-depth theoretical derivations, exact protocol states, production manifests, and low-level failure domains.
  - **`LABS.md`**: Step-by-step hands-on operational lab with concrete verification commands and debugging scenarios.

---

## 3. Clustered Multi-Node Ollama Engine

Synapse operates across a multi-node Ollama cluster load-balancing between local and homelab machines with model parity:
- **Node 1 (Local):** `http://localhost:11434` (`qwen2.5-coder:32b`, `deepseek-r1:32b`)
- **Node 2 (Remote Homelab):** `http://homelab.local:11434` (`qwen2.5-coder:32b`)
- **Cloud Fallback:** Optional Google Gemini API integration.
- **Adversarial Peer Review:** Cross-model auditor (`deepseek-r1:32b`) audits generated units for hallucinations, wrong flags, and placeholders.

---

## 4. CLI Command Reference (`synapse`)

The CLI is registered as a standard command `synapse` (also accessible via `./bin/synapse`):

```bash
# Launch the Web Workbench (UI + Socratic Chat + PTY Sandbox Terminal)
synapse serve
synapse serve --daemon --port 8000   # Background daemon mode
synapse stop                         # Stop daemon

# Curriculum Status & Inspection
synapse status                       # View completion stats across all 11 domains
synapse tree                         # Print hierarchical tree with [FLB] status badges
synapse tree --domain computing

# Navigation & Search
synapse search "eBPF verifier"       # Full-text regex search with highlighted context
synapse graph                        # Display 39-edge cross-disciplinary prerequisite DAG
synapse lint                         # Audit files for depth, section headers, and placeholders

# Export & In-App Spaced Repetition
synapse export formal_sciences       # Compile entire domain into a single-file Markdown handbook
synapse flashcards ebpf              # Generate Anki active-recall CSV deck

# User Competence Tracking
synapse mastery                      # View personal mastery counts and percentages
synapse mastery computing/infrastructure/kubernetes/01_control_plane_and_etcd --set mastered

# Adversarial Quality & Hallucination Audit
synapse review kubernetes/01_control_plane_and_etcd --model deepseek-r1:32b
synapse review ebpf/01_virtual_machine_and_isa --fix   # Auto-fix detected errors

# Creation & Socratic Terminal
synapse add computing infrastructure kubernetes/09_service_mesh --title "Service Mesh Architecture"
synapse generate kubernetes/01_control_plane_and_etcd  # Generate units via cluster
synapse chat ebpf                                     # Interactive terminal Socratic mentor
```

---

## 5. Web Workbench (Synapse Dashboard)

Open **`http://127.0.0.1:8000`** in any browser:

- **Sidebar Tree (Left):**
  - Clean collapsed-by-default initial state with one-click **Expand/Collapse All** toggle.
  - Interactive sorting dropdown: **Default (Curated)**, **A to Z**, and **Progress**.
  - Live predictive filter that auto-expands matching courses and units.
  - Distinct matched Lucide icons for all 11 domains.
  - Sized-up typography (`13.5px`) with high contrast.
- **Lesson Viewer (Center):**
  - **Unified Zero-Shift Navigation Bar:** Persistent 42px header anchoring tabs (`Summary`, `Foundation`, `Lesson`, `Labs`, `Quiz`) on the left and Difficulty Tier (`[BEG] [INT] [ADV]`) on the right. Switching difficulty levels preserves your active tab without resetting.
  - Fluid reading column with enlarged typography (`16px`, line-height `1.75`) that eliminates empty whitespace chasms.
  - KaTeX mathematical typography ($\LaTeX$) and live Mermaid.js architecture diagrams.
  - One-click actions: **Mastery State Dropdown**, **Anki CSV Deck Export**, **Handbook Markdown Export**, and **Regenerate Summary**.
- **Socratic AI Tutor (Right):**
  - **Resizable Chat Column:** Drag the left border handle to adjust width freely from `320px` to `800px`.
  - **Zero Manual Work Auto-Saving:** Every message exchange is automatically persisted to `sessions/active_session.md` and `sessions/chat_history.json`, staged in Git, and restored when reopening the topic.
- **Terminal Sandbox Drawer (Bottom):**
  - **Draggable Height Resizing:** Adjust height between `120px` and `85vh`, or click `<Maximize2 />` for Fullscreen focus mode.
  - **Isolated Execution Profiles:**
    - `Host Shell (Local)`: Bare-metal macOS shell for Git and workspace operations.
    - `Linux Sandbox (Docker / Rancher)`: Disposable Ubuntu Linux container live-mounting `/workspace` with pre-installed `clang`, `gcc`, `bpftool`, `gdb`, and networking utilities.
    - `Kubernetes DevPod (k3s)`: Direct shell inside an internal cluster diagnostics pod (`netshoot`) for cluster DNS and network policy inspection.
- **Settings Modal (`⚙`):**
  - Switch color schemes on the fly: **Studio Dark**, **Titanium Obsidian**, **Monokai Pro**, **Nordic Slate**.
  - Adjust base UI font size (`Compact`, `Standard`, `Large`) and reading width.
  - Configure Ollama host URLs, primary model, and reviewer model.

---

## 6. Docker & Homelab Deployment

### Run via Docker Compose
```bash
docker compose -f deploy/docker-compose.yml up -d
```

### Install as macOS Service (Launchd)
```bash
cp deploy/com.synapse.workbench.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.synapse.workbench.plist
```

### Install as Linux Service (Systemd)
```bash
sudo cp deploy/learning-workbench.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now learning-workbench
```

---

## 7. Git & Version Control

All generated lessons, summaries, flashcards, and discussion session debriefs are automatically committed and synchronized with your upstream Git repository configured as `origin`.
