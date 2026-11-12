<div align="center">
  <img src="app/frontend/public/favicon.svg" alt="Synapse Logo" width="100" />
  <h1>Synapse</h1>
  <p><strong>AI Learning Workspace & Socratic Curriculum Engine</strong></p>

  <a href="https://github.com/yourusername/synapse/actions">
    <img src="https://img.shields.io/badge/build-passing-success" alt="Build Status">
  </a>
  <a href="https://github.com/yourusername/synapse/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
  </a>
  <a href="#desktop-shell">
    <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey" alt="Platforms">
  </a>
  <a href="https://fastapi.tiangolo.com/">
    <img src="https://img.shields.io/badge/FastAPI-1.0-teal" alt="FastAPI">
  </a>
  <a href="https://vitejs.dev/">
    <img src="https://img.shields.io/badge/Vite%20%2B%20React-18-blueviolet" alt="React">
  </a>
</div>

<br />

**Synapse** is an advanced, self-hosted Learning Workspace and automated Curriculum Engine. It autonomously generates textbook-grade masterclasses, operational labs, and flashcards across a strict taxonomy of 12 domains and 80 disciplines using multi-node local LLM clusters.

Once the curriculum is generated, Synapse provides a rich native **Socratic Workbench** (available as a web app or standalone Electron desktop shell) featuring a dual-pane markdown reader, an integrated PTY terminal, and an interactive AI Mentor.

---

## 🎯 Features

- **Automated Curriculum Generation (`generate_all.py`):** Automatically drafts, audits, and refines multi-stage technical lessons (Beginner, Intermediate, Advanced) and hands-on terminal labs.
- **Multi-Node Cluster Orchestration:** Distributes LLM workloads across a fleet of local instances (e.g., Ollama, LocalAI) and cloud providers (Anthropic Claude 3.5), employing cross-model adversarial peer review.
- **Native Socratic Workbench:** A beautiful, responsive Electron / React frontend featuring:
  - **Topic Tree Navigation:** Canonical 3-level taxonomy hierarchy.
  - **Dynamic Lesson Reader:** Supports Mermaid.js diagrams, KaTeX math blocks, and markdown rendering.
  - **AI Mentor Chat:** Context-aware AI tutor hooked directly into your current lesson.
  - **Integrated PTY Terminal:** Live WebSocket-bridged host terminal for executing operational labs and interactive verification.
- **SynPack Curriculum Store:** Export and sideload full topic masterclasses as portable `.synpack` archives via the integrated Addon Store.
- **Mastery & Knowledge Graph:** Track learning progress, unlock prerequisites, and export Anki-compatible `.csv` flashcard decks.

---

## 🏗 Architecture

Synapse is separated into three highly decoupled components:

1. **`learning_engine/` (Python):** The core intelligence layer. Manages the LLM orchestration, taxonomy enforcement, `.synpack` packaging, and the knowledge DAG.
2. **`app/backend/` (FastAPI):** A lightweight asynchronous REST and WebSocket server. Bridges the frontend to the local file system and handles the live PTY terminal session.
3. **`app/frontend/` & `app/desktop/` (React/Vite & Electron):** The UI presentation layer. Can run as a web app served by FastAPI or bundled into a native desktop `.app` / `.exe`.

---

## 🚀 Quick Start & Installation

Most users do not need to install Python, Node.js, or build packages from source. Choose the installation method that fits your workflow:

### Option 1: 1-Click Desktop App (Zero Build Required)
Download the standalone, zero-dependency desktop application directly from the **[Releases](https://gitea.2464.cz/ai/synapse/releases)** page:

| Platform | Download | Instructions |
| :--- | :--- | :--- |
| **macOS (Apple Silicon)** | **[`Synapse-Workbench-1.0.0-arm64.dmg`](https://gitea.2464.cz/ai/synapse/releases/tag/v1.0.0-rc.1)** | Open the `.dmg`, drag **Synapse Workbench** to `Applications`, and launch! |
| **macOS (Portable)** | **[`Synapse-Workbench-1.0.0-arm64-mac.zip`](https://gitea.2464.cz/ai/synapse/releases/tag/v1.0.0-rc.1)** | Unzip and launch **Synapse Workbench.app** directly. |

*The desktop shell automatically manages its internal backend sidecar, connects to your local Ollama instance on `127.0.0.1:11434`, and requires zero terminal setup.*

---

### Option 2: 1-Click Docker Compose (Universal Container)
Run the full Synapse Socratic Workbench in an isolated, multi-stage production container:

```bash
# Clone and launch in one command
git clone https://gitea.2464.cz/ai/synapse.git && cd synapse
docker compose up -d
```

- **Open:** Visit **`http://localhost:8000`** in your browser.
- **Persistence:** Local curriculum (`./topics`), SQLite mastery database (`./data`), and exported packages (`./exports`) are automatically volume-mounted and persisted on your host machine.
- **Host Ollama Bridge:** Pre-configured with `host.docker.internal:host-gateway` to connect seamlessly to local Ollama running on your host machine.

To shut down:
```bash
docker compose down
```

---

### Option 3: Developer & Source Setup
For contributors developing the Python learning engine or React UI:

```bash
# 1. Clone repository
git clone https://gitea.2464.cz/ai/synapse.git && cd synapse

# 2. Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Build frontend SPA
cd app/frontend
npm install
npm run build
cd ../..

# 4. Launch Web Workbench
./bin/synapse serve --port 8000
# Open http://localhost:8000 in your browser
```

To run the native desktop shell from source:
```bash
./bin/synapse desktop
```

---

## 📦 Building Standalone Binaries (Release Candidates)

Synapse can be packaged into zero-dependency native desktop applications using `electron-builder`.

```bash
cd app/desktop
npm install

# Build for macOS (.app and .dmg)
npm run build:mac

# Build for Windows (.exe / NSIS)
npm run build:win

# Build for Linux (.AppImage / .deb)
npm run build:linux
```
Compiled binaries will be output to `dist/desktop/`.

---

## 🧠 Generating Curriculum

You can command the `learning_engine` to autonomously research and write masterclasses for empty topics in your syllabus. 

```bash
# Generate all missing topics across all 12 domains using your local cluster
./bin/synapse generate --domain all

# Generate a specific topic using Anthropic's Claude 3.5 Sonnet
./bin/synapse generate --topic computing/systems/bash --provider anthropic
```

---

## 🛡️ Terminal Security & Host Safety

Synapse features an integrated WebSocket PTY terminal that binds to your local host shell (`zsh` or `bash`). 
To prevent accidental destruction of your host machine during operational labs, Synapse employs an **in-stream command verification interceptor**.

If a destructive command is detected (e.g., `rm -rf /`, `mkfs`, fork bombs), the terminal will pause execution, intercept the keystroke, and require you to type `CONFIRM` to proceed.

---

## 📚 Documentation

For detailed multi-platform guides and operational procedures, see the `docs/` directory:

- [Installation & Multi-Platform Guide (macOS, Windows, Linux)](docs/INSTALLATION.md)
- [Terminal Sandboxes: Rancher Desktop, Docker, k3s & Host Safety](docs/CONTAINERS_AND_SANDBOX.md)
- [SynPack Curriculum Distributions & Addon Store](docs/PACKAGES_AND_STORE.md)
- [Clean Packaging & Workspace Data Management](docs/CLEANUP_AND_DATA_MANAGEMENT.md)

---

## 📄 License

Synapse is open-source software licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
