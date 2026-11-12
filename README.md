# Synapse — AI-Native Engineering & Polymath Workbench

<p align="center">
  <img src="app/frontend/public/favicon.svg" width="96" height="96" alt="Synapse Logo" />
</p>

**Synapse** is an automated, production-grade AI learning workspace, knowledge graph, and Socratic engineering workbench. It treats the filesystem as a Git-backed database across **12 atomic domains**, **54 disciplines**, and over **700 calibrated technical topics** structured for deep systems engineering, mathematical rigor, and operational mastery.

---

## 1. Architecture & Taxonomy

Synapse follows a clean **3-Level Flat Taxonomy** that eliminates arbitrary directory nesting and fragmented file sprawl:

$$\text{Domain (L1)} \;\longrightarrow\; \text{Discipline (L2)} \;\longrightarrow\; \text{Topic / Course (L3)}$$

### The 12 Core Domains
1. **`computing`** — Linux Kernel, Systems Software, Infrastructure (Kubernetes, eBPF, Harvester), Security (Web, Exploitation, Hardware Hacking), AI/ML, and Data Systems.
2. **`engineering`** — Computer Architecture, Assembly (x86/ARM), Embedded Systems, Circuits, Hardware Hacking, and Robotics.
3. **`motorsports`** — Performance Driving Dynamics, Motorcycle Riding Dynamics, Vehicle Telemetry, Diagnostics & Powertrain.
4. **`crafts`** — Engineering Mechanisms, Precision Machining & CNC, 3D Printing & CAD, Retro Hardware Restoration, Woodworking.
5. **`formal_sciences`** — Pure Math (Abstract Algebra, Category Theory), Applied Math (Game Theory, Cryptography), Mathematical Logic, Discrete Mathematics.
6. **`natural_sciences`** — Quantum Physics, Classical Mechanics, Organic/Physical Chemistry, Molecular Biology.
7. **`arts`** — Music Performance (Bass, Drums, Piano, Electric Guitar), Audio DSP, Modular Synthesis, Orchestral Scoring, Visual Arts.
8. **`languages`** — Germanic (English, German), Slavic (Czech, Russian), Romance (Spanish), and Comparative Linguistics.
9. **`humanities`** — Classical Philosophy, Epistemology, Global Intellectual History, Analytical Thinking.
10. **`business`** — Corporate Finance, M&A, Private Equity, Market Microstructure, Wealth Management.
11. **`economics`** — Macroeconomics, Microeconomics, Game Theory, Central Banking & Monetary Policy.
12. **`health_sciences`** — Exercise Physiology, Nutritional Biochemistry, Sports Medicine, Human Anatomy.

---

## 2. Masterclass Multi-Lesson Curriculum

Every topic directory is self-contained and structured as a publication-grade, O'Reilly / MIT Press-level technical textbook chapter series:

```text
topics/computing/data/postgresql/
├── lesson_01_foundations_and_invariants.md
├── lesson_02_architecture_and_process_model.md
├── lesson_03_mvcc_wal_and_vacuum.md
├── lesson_04_query_planning_and_indexing.md
├── lesson_05_high_availability_and_replication.md
├── lesson_06_curriculum_summary.md
└── labs.md
```

- **Numbered Lessons (`lesson_01_*.md` to `lesson_06_*.md`):** Deep, flowing narrative prose written from first principles. Features byte-level binary layouts, ASCII memory maps, mathematical invariants, and valid Mermaid architecture diagrams.
- **Operational Verification Labs (`labs.md`):** Hands-on diagnostic labs with exact, runnable Linux/BSD CLI commands, profiling steps, and fault-injection scripts with zero placeholders.
- **Granular Lesson Mastery:** Completion is tracked per lesson (`✓`) and persisted atomically to `topics/mastery.json`.

---

## 3. Clustered 4-Node Local AI Engine (Author-Reviewer Architecture)

Synapse orchestrates a local hardware-tiered Ollama cluster that parallelizes curriculum generation and enforces **cross-node adversarial fact-checking**:

```text
[ Module Drafted ] ──► [ Primary Worker Node ] ──► [ Independent Auditor Node ] ──► [ Verified & Pushed ]
Lesson 1 (32B)         localhost (32B)             node-studio (32B)                Git Commit + Remote Push
Lesson 2 (32B)         node-studio (32B)           node-gpu (24GB)                  Git Commit + Remote Push
Lesson 3 (30B)         node-gpu (24GB)             localhost (32B)                  Git Commit + Remote Push
Labs (32B)             localhost (32B)             node-studio (32B)                Git Commit + Remote Push
```

- **Node 1 (Local):** `http://127.0.0.1:11434` (Ollama • Large VRAM • `qwen2.5-coder:32b`, `deepseek-r1:32b`)
- **Node 2 (Studio Node):** `http://node-studio:11434` (Ollama • Large VRAM • `qwen2.5-coder:32b`)
- **Node 3 (GPU Server):** `http://192.168.1.100:8080` (LocalAI / OpenAI • 24GB GPU • `Qwen3-Coder-30B`)
- **Node 4 (Auxiliary Node):** `http://node-aux:11434` (Ollama • 12GB VRAM • `llama3.1:8b`)
- **Cloud Provider (Anthropic):** Claude 3.5 Sonnet / Opus via official Anthropic API or custom gateway proxy.
  > **Security Note:** Cloud API keys (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`) are stored strictly in your local, git-ignored SQLite database (`data/synapse.db`) or user environment. They are never committed to source control.
- **Cross-Node Adversarial Review:** No model reviews its own output. Independent auditor nodes verify kernel structs, syscall signatures, and CLI syntax, auto-correcting any hallucinations or syntax errors before committing.

---

## 4. Web Workbench (Synapse Dashboard)

Open **`http://127.0.0.1:8000`** in any browser. The single integrated FastAPI service hosts the API, WebSockets, and compiled React SPA together on port 8000:

### Streamlined 3-Tab Reader
- **`[ Study ]` Tab:** 
  - Permanent, non-shifting lesson bar with full lesson title dropdown and numeric pills (`[All] [1] [2]...`).
  - Fluid reading column with enlarged typography (`16px`, line-height `1.75`), $\LaTeX$ math equations (KaTeX), and clean code execution buttons.
  - Bottom navigation bar with **Previous / Next** and an interactive **`[ Mark Complete ✓ ]`** toggle.
- **`[ Labs ]` Tab:** Dedicated operational verification exercises, shell diagnostic cheat sheets, and step-by-step CLI procedures.
- **`[ Quiz ]` Tab:** Socratic interactive quiz with immediate rationale explanations and score tracking.

### Interactive Diagram & Media Lightbox
- Flowcharts and sequence diagrams automatically expand up to **900px** with responsive typography.
- Clicking on **any Mermaid diagram or image** opens a full-screen **Zoom & Pan Lightbox Modal** supporting:
  - **40% to 400% Zooming:** Via modal controls or **mouse wheel scroll**.
  - **Click-and-Drag Panning:** Move enlarged diagrams freely across the viewport.
  - **Keyboard Hotkeys:** `Esc` to close, `+` / `-` to zoom, `0` to reset.

### Socratic AI Mentor & Terminal Awareness
- **Sub-Second Streaming:** Chat requests route to low-latency local 8B models with live Server-Sent Events (SSE) token streaming (<1–2s total response time).
- **Strict Socratic Mandate:** Concise 2–4 sentence responses that provide direct intuition followed by one guiding question.
- **Dynamic Context Switching:** Automatically reloads saved session history and adapts the mentor persona to the active domain (e.g., *Systems Software & Kernel Architect* for computing vs. *Pure Mathematics & Formal Logic Mentor* for formal sciences).
- **Live Terminal Window Awareness:** A server-side circular PTY ring buffer automatically provides the AI mentor with the last 40 lines of terminal output and errors. Ask *"Why did that command fail?"* and the AI will diagnose the error directly without manual copy-pasting.

### Responsive Embedded Terminal Drawer
- POSIX PTY terminal supporting `Host Shell (Local)`, `Linux Sandbox (Docker)`, and `Kubernetes DevPod (k3s)`.
- Responsive container auto-fitting with full multiline line-wrapping without truncation, and `ps -ww` integration.

---

## 5. CLI Command Reference (`synapse`)

Accessible via `./bin/synapse`:

```bash
# Launch the Integrated Web Workbench (Port 8000)
./bin/synapse serve
./bin/synapse serve --daemon --port 8000   # Background daemon mode
./bin/synapse stop                         # Stop daemon

# Modernized Curriculum & Cluster Status
./bin/synapse status                       # View L1/L2/L3 taxonomy, authored lessons, labs, mastery, and cluster health
./bin/synapse tree                         # Print curriculum tree with lesson counts
./bin/synapse tree --domain computing

# Clustered Batch Generation (Author-Reviewer Pipeline)
.venv/bin/python scripts/generate_all.py --topic computing/data/postgresql --force
.venv/bin/python scripts/generate_all.py --domain computing --force

# Navigation, Search & Linting
./bin/synapse search "eBPF verifier"       # Full-text regex search with highlighted context
./bin/synapse graph                        # Cross-disciplinary prerequisite DAG
./bin/synapse lint                         # Audit files for depth, headers, and placeholders

# Export, SynPack & Flashcards
./bin/synapse export computing             # Compile domain handbook (.md)
./bin/synapse flashcards postgresql        # Generate Anki active-recall CSV deck

# Granular Mastery Tracking
./bin/synapse mastery                      # View personal mastery counts and percentages
./bin/synapse mastery computing/data/postgresql --set mastered
```

---

## 6. Deployment & Services

### Run as macOS Background Service (Launchd)
```bash
cp deploy/com.synapse.workbench.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.synapse.workbench.plist
```

### Run as Linux Service (Systemd)
```bash
sudo cp deploy/learning-workbench.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now learning-workbench
```

### Windows Support (WSL2)
Synapse requires POSIX pseudo-terminals (`pty`, `termios`, `fcntl`). Running on Windows is supported via **WSL2** (`wsl --install -d Ubuntu`). Clone inside WSL2 and execute `./bin/synapse serve`.

---

## 7. Version Control & Git Synchronization

All generated curriculum units, audits, session debriefs, and flashcards are automatically versioned and synchronized with your upstream Git repository (e.g. `origin/main`).
