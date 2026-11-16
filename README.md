<div align="center">
  <img src="app/frontend/public/favicon.svg" alt="Synapse Logo" width="100" />
  <h1>Synapse</h1>
  <p><strong>AI Learning Workspace & Socratic Curriculum Engine</strong></p>

  <a href="CHANGELOG.md">
    <img src="https://img.shields.io/badge/version-1.0.0-emerald?style=flat" alt="Version 1.0.0">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
  </a>
  <a href="#-quick-start--installation">
    <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey" alt="Platforms">
  </a>
  <a href="https://fastapi.tiangolo.com/">
    <img src="https://img.shields.io/badge/FastAPI-1.0-teal" alt="FastAPI">
  </a>
  <a href="https://vitejs.dev/">
    <img src="https://img.shields.io/badge/Vite%20%2B%20React-19-blueviolet" alt="React 19">
  </a>
  <a href="https://anthropic.com">
    <img src="https://img.shields.io/badge/Claude%20Opus-5.5-orange" alt="Claude Opus 5.5">
  </a>
  <a href="https://buymeacoffee.com/blebleblee" target="_blank">
    <img src="https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donate-yellow.svg?style=flat&logo=buy-me-a-coffee" alt="Buy Me A Coffee">
  </a>
</div>

<br />

**Synapse** is an advanced, self-hosted AI Learning Workspace and automated Curriculum Engine. It autonomously researches, scopes, drafts, peer-reviews, and enhances textbook-grade masterclasses and hands-on operational labs across a canonical taxonomy of **12 engineering, scientific, and polymath domains** and **80 disciplines**.

Once the curriculum is assembled, Synapse provides a native **Socratic Workbench** (available as a web app or standalone Electron desktop application) featuring a dual-pane reader, an integrated PTY terminal with smart command synthesis, and an interactive, multilingual AI Mentor.

---

## 🎯 Key Features & Capabilities

### 1. Autonomous Masterclass Curriculum Engine
- **Textbook-Grade Depth:** Automatically authors sequential, multi-module masterclasses following the rigorous O'Reilly / MIT Press standard:
  - *Foundations & Invariants:* First-principles mathematical and theoretical groundwork.
  - *Architecture & Mechanics:* Internal data structures, execution pipelines, and clean ASCII/Mermaid diagrams.
  - *Deep Dive & Concurrency:* Memory models, locking mechanisms, failure modes, and mitigation patterns.
  - *Operational Verification Labs:* Hands-on terminal diagnostics, benchmarks, and chaos testing scenarios.
- **Parallel Multi-Node Generation (`generate_all.py`):** Orchestrates generation across local multi-node Ollama clusters or cloud providers (**Anthropic Claude Opus 5.5 / Sonnet 5**) using work-stealing queues and multi-threaded parallel drafting.
- **Deep Content Enhancer (`--enhance`):** Rigorously audits existing lessons and labs, purging hallucinations, standardizing Mermaid.js diagrams, expanding real-world code (C, Rust, Go, Python, SQL), and enriching architectural explanations.
- **Live Terminal Monitor (`monitor.py`):** Dedicated terminal dashboard with auto-updating progress counters, active worker status, file insertion statistics, and live log tailing (`--watch`, `--tail`).

### 2. Native Socratic Workbench UI
- **Canonical Topic Tree:** Fast navigation across 12 domains and 80 disciplines with completion badges, multi-lesson expansion, and a redesigned **`icon-btn-sm`** sort toggle (`ArrowDownAZ` / `TrendingUp`).
- **Dynamic Math & Diagram Reader:** Real-time rendering of KaTeX display and inline math (`$$...$$`), syntax-highlighted code blocks, and self-healing **Mermaid.js** architecture graphs.
- **Smart Terminal Command Synthesizer:** Intelligently wraps code blocks (SQL, Kubernetes manifests, Python, C, Rust) into safe, executable shell wraps ready to run directly in your terminal with one click.
- **Visual DAG Knowledge Graph:** Toggle between an interactive DAG pipeline view and a detailed timeline to visualize prerequisites, domain pathways, and learning trajectories.
- **Bilingual & Polyglot Reader:** Side-by-side bilingual reading mode supporting on-the-fly language comparisons.

### 3. Socratic AI Mentor
- **Active Lesson Grounding:** Chat prompts are continuously grounded in the active lesson or lab open on your screen.
- **Live Terminal Context Interception:** Automatically tracks your active shell session, executed commands (`LAST_TERMINAL_COMMAND`), and console outputs, directly diagnosing exit codes, errors, and syntax without confusion.
- **Full Multilingual Fluency:** Seamlessly converses in **English, Czech (Čeština), German (Deutsch), Spanish (Español), or Russian (Русский)** while keeping code identifiers exact.
- **Resilient Model Fallback:** Auto-discovers local models, handles single-model nodes automatically, and cascades to Cloud Claude Opus/Sonnet if local Ollama is offline.

### 4. Deep Theme & Appearance Engine
- **7 Curated Base Themes:** Studio Obsidian, GitHub Dimmed, Nordic Frost, Monokai Pro, Dracula Noir, Solarized Dark, and Titanium Daybreak.
- **5 Accent Highlight Colors:** Amber Gold, Electric Cyan, Matrix Emerald, Royal Amethyst, and Crimson Rose.
- **Reading Typography:** Modern Sans (Inter), Academic Serif (Charter/Merriweather), or Technical Mono (JetBrains Mono).
- **Line Spacing & Density:** Configurable reader line height (Compact 1.45, Balanced 1.68, Relaxed 1.92).

### 5. Dedicated System & Maintenance Hub
- Dedicated settings tab for transient session cleanup (`.workspace_sessions`), cluster model pin resets (`.synapse_node_pins.json`), database health (`data/synapse.db`), and generation log viewing.

---

## 🏗 Architecture

```mermaid
graph TB
    subgraph Frontend ["Presentation Layer (React 19 + TypeScript + Vite / Electron)"]
        UI["Topic Tree & Lesson Viewer"]
        Graph["Visual DAG Knowledge Graph"]
        Chat["Socratic Mentor Panel"]
        Term["Integrated xterm.js PTY Terminal"]
        Synthesizer["Smart Command Synthesizer"]
    end

    subgraph Backend ["Application Layer (FastAPI Asynchronous Gateway)"]
        API["REST Endpoints (/api/tree, /api/chat, /api/settings)"]
        WS["PTY WebSocket Bridge (/ws/terminal)"]
        Safety["Host Safety Command Interceptor"]
        Buffer["Terminal Buffer & Command History"]
    end

    subgraph Engine ["Intelligence Layer (Python Learning Engine)"]
        Cluster["Ollama Multi-Node Cluster & Host Pinner"]
        Claude["Anthropic Claude Provider (Opus 5.5 / Sonnet 5)"]
        Generator["Parallel Curriculum Generator"]
        Enhancer["Deep Content Enhancer & Mermaid Normalizer"]
        Store["SynPack Addon Packager & Exporter"]
        DB[(SQLite Cache & Mastery DB: synapse.db)]
    end

    UI --> API
    Chat --> API
    Term <--> WS
    WS --> Safety --> Buffer
    API --> Engine
    Generator --> Claude
    Generator --> Cluster
```

---

## 🚀 Quick Start & Installation

### Option 1: 1-Click Desktop App (Zero Build Required)
Download the standalone, zero-dependency desktop application from the project releases:

| Platform | Download | Instructions |
| :--- | :--- | :--- |
| **Windows (Portable)** | **`Synapse-Workbench-Portable-1.0.0.exe`** | Standalone portable `.exe` (no Python or installation required). Place `./topics/` alongside the executable and launch! |
| **macOS (Apple Silicon)** | **`Synapse-Workbench-1.0.0-arm64.dmg`** | Open the `.dmg`, drag **Synapse Workbench** to `Applications`, and launch! |
| **macOS (Portable)** | **`Synapse-Workbench-1.0.0-arm64-mac.zip`** | Unzip and launch **Synapse Workbench.app** directly. |
| **Linux (CLI / Server)** | **`synapse-1.0.0-py3-none-any.whl`** | See Python Wheel Installation below. |
| **Any Platform** | **Docker Compose** | See Docker Deployment below. |

---

### Windows Portable App & Modular Topics Addon
The Windows desktop distribution is packaged as a **standalone portable binary** (`Synapse-Workbench-Portable-1.0.0.exe`).
- **Zero Dependencies:** Bundles the native Electron desktop shell and Python backend sidecar. No Python installation or build tools required.
- **External Topics Addon:** Curriculum topics remain pure, platform-independent Markdown files. Keep the `topics/` folder directly alongside `Synapse-Workbench-Portable.exe`. You can edit, update, or drop in new topic packs without touching or rebuilding the executable.
- **Cross-Platform Shell Bridge:** Features native Windows shell integration (`powershell.exe`/`cmd.exe`) for terminal drawer execution.

---

## 📦 How Synapse Works: App Shell + Modular `.synpack` Addons

Synapse separates the **Application Engine** (the reader, Socratic AI mentor, KaTeX math engine, and terminal) from the **Curriculum Knowledge Base**. The desktop installer is a lightweight, zero-dependency binary (~90 MB), while masterclasses are packaged as modular `.synpack` curriculum archives.

```mermaid
flowchart TD
    subgraph App ["Synapse Workbench Core (~90 MB)"]
        SHELL["Electron Shell & FastAPI Backend<br/>(Reader · Socratic Mentor · KaTeX Math · PTY Terminal)"]
    end

    subgraph Addons ["Curriculum Addons (*.synpack)"]
        MASTER["synapse_complete_curriculum.synpack<br/>(All 12 Domains · 539 Topics · ~33.5 MB)"]
        MODULAR["Modular Domain Packs<br/>(computing.synpack · engineering.synpack · arts.synpack · etc.)"]
    end

    MASTER -->|"1-Click Sideload or Store"| SHELL
    MODULAR -->|"Download specific subjects"| SHELL

    style App fill:#1e293b,stroke:#38bdf8,color:#f8fafc
    style Addons fill:#0f172a,stroke:#a855f7,color:#f8fafc
```

### How to Install Curriculum Addons

#### Option 1: 1-Click Master Pack (Recommended)
Download the complete global curriculum from the [Project Releases](https://github.com/blebleblee/synapse/releases):
1. Download **`synapse_complete_curriculum.synpack`** (33.5 MB).
2. Open Synapse Workbench $\rightarrow$ Click **Settings ⚙** $\rightarrow$ **Curriculum Store & Addons**.
3. Under **Sideload Local Package**, drop or select `synapse_complete_curriculum.synpack`.
4. *Done!* All 12 domains and 539 masterclass topics will immediately appear in your sidebar.

#### Option 2: Individual Modular Domain Packs
If you only need specific subjects (e.g., just Computing or Engineering):
- Download only the `.synpack` files you want from Releases (`computing.synpack`, `engineering.synpack`, etc.).
- Sideload them via Settings ⚙ $\rightarrow$ Curriculum Store.

#### Option 3: Command Line / Air-Gapped Sideloading
For server, Docker, or headless environments:
```bash
# Sideload any .synpack package from the terminal
synapse pack install path/to/synapse_complete_curriculum.synpack

# List installed packages
synapse pack list
```

#### Option 4: Portable Desktop (Drop & Go)
If using the portable Windows binary (`Synapse-Workbench-Portable.exe`) or macOS `.app`, you can place an uncompressed `topics/` folder directly alongside the executable. Synapse detects local topics automatically without installation.

---

### Option 2: Python Wheel (`.whl`) Installation (Linux, macOS, Windows WSL2)

Install and run Synapse via standard Python packaging across Linux, macOS, or Windows (WSL2):

```bash
# 1. Create and activate a virtual environment
python3 -m venv synapse-env
source synapse-env/bin/activate

# 2. Install the official wheel
pip install dist/python/synapse-1.0.0-py3-none-any.whl

# 3. Launch the Socratic Workbench
synapse serve --port 8000
# Open http://localhost:8000 in your browser
```

* **Linux:** 100% native support out of the box with embedded POSIX PTY terminal drivers.
* **Windows:** Use the Portable Windows Binary above for native execution, or WSL2 (`wsl --install`) for POSIX environments.
* **CLI Utilities:** Once installed, use `synapse status` for curriculum completion stats or `synapse lint` for quality auditing.

---

### Option 3: 1-Click Docker Compose
Run the full Socratic Workbench in an isolated, multi-stage production container:

```bash
git clone <repo-url> && cd synapse
docker compose up -d
```

- **Open:** Visit **`http://localhost:8000`** in your browser.
- **Persistence:** Local curriculum (`./topics`), SQLite mastery database (`./data`), and exported packages (`./exports`) are volume-mounted.
- **Ollama Host Bridge:** Pre-configured with `host.docker.internal:host-gateway` to connect seamlessly to local Ollama on your host machine.

To shut down:
```bash
docker compose down
```

---

### Option 4: Developer & Source Setup

```bash
# 1. Clone repository
git clone <repo-url> && cd synapse

# 2. Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Build frontend SPA
cd app/frontend
npm install
npm run build
cd ../..

# 4. Launch Synapse Web Workbench
.venv/bin/uvicorn app.backend.main:app --host 127.0.0.1 --port 8000
# Open http://localhost:8000 in your browser
```

For hot-reloading frontend development:
```bash
npm --prefix app/frontend run dev
# Open http://localhost:5173
```

---

## 🧠 Curriculum Generation & Enhancement

Synapse can autonomously research, author, or deeply enhance curriculum units using Claude Opus 5.5 or local Ollama clusters.

### Running the Parallel Generator
```bash
# Enhance all existing topics in the computing domain with Claude Opus 5.5
python3 scripts/generate_all.py --domain computing --enhance

# Draft all unwritten topics across the entire taxonomy
python3 scripts/generate_all.py --provider anthropic

# Target a specific domain with local Ollama
python3 scripts/generate_all.py --domain formal_sciences --provider ollama
```

### Live Generation Monitoring
```bash
# Follow the live token stream and elapsed times in real time
tail -f generator.log

# Open the auto-updating visual terminal dashboard
python3 scripts/monitor.py --watch

# Print a one-time status snapshot
python3 scripts/monitor.py
```

---

## 🛡️ Security, Host Safety & Credential Isolation

- **Isolated Credentials:** Cloud API keys (Anthropic, Gemini) are stored strictly outside the repository tree in `~/.config/synapse/env` with restricted `600` file permissions. They are never committed to git.
- **Host Safety Guard:** The integrated PTY terminal actively intercepts destructive command patterns (`rm -rf /`, `mkfs`, raw block writes, fork bombs) and pauses execution until you explicitly type `CONFIRM`.
- **Root-Anchored Runtime DB:** Runtime caches and SQLite databases (`/data/`, `/exports/`) are anchored to root in `.gitignore`, guaranteeing authored topics in `topics/computing/data/` are never accidentally ignored.

---

## 📚 Documentation Index

For detailed guides, see the `docs/` directory:

- [Curriculum Generation & Models Guide](docs/CURRICULUM_GENERATION_AND_MODELS.md)
- [Pipeline & Release Operational Runbook](docs/RUNBOOK_PIPELINE_AND_RELEASE.md)
- [Socratic Workbench & UI Architecture](docs/SOCRATIC_WORKBENCH_AND_UI.md)
- [Configuration, Node Pinning & Security](docs/CONFIG_AND_SECURITY.md)
- [Terminal Sandboxes: Docker, k3s & Host Safety](docs/CONTAINERS_AND_SANDBOX.md)
- [Installation & Multi-Platform Guide](docs/INSTALLATION.md)
- [SynPack Distributions & Addon Store](docs/PACKAGES_AND_STORE.md)
- [Clean Packaging & Workspace Data Management](docs/CLEANUP_AND_DATA_MANAGEMENT.md)

---

## ☕ Support the Project

Synapse is **100% free, private, and open-source**. If you find this learning workbench or the generated curricula valuable for your daily engineering practice, studies, or team training, consider buying me a coffee to support continued development, model inference, and infrastructure costs:

<p align="center">
  <a href="https://buymeacoffee.com/blebleblee" target="_blank">
    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="180" />
  </a>
</p>

---

## 📄 License

Synapse is open-source software licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
