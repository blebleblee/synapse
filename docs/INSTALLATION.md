# Synapse Installation & Platform Guide

Comprehensive guide for installing, running, and building **Synapse** across **macOS**, **Windows**, and **Linux**.

---

## 🚀 1. 1-Click Desktop App (Zero Build / Zero Terminal)

The easiest way to run Synapse. No Python, Node.js, or package compilation required.

Download pre-compiled Release Candidate binaries from the **[Releases](https://gitea.2464.cz/ai/synapse/releases)** page:

| Platform | Download Format | Installation Instructions |
| :--- | :--- | :--- |
| **macOS (Apple Silicon)** | **`.dmg` (Disk Image Installer)** | Open `Synapse-Workbench-1.0.0-arm64.dmg`, drag **Synapse Workbench** to `/Applications`, and launch from Spotlight or Launchpad. |
| **macOS (Portable Bundle)** | **`.zip` (App Archive)** | Decompress `Synapse-Workbench-1.0.0-arm64-mac.zip` and launch **Synapse Workbench.app** directly. |
| **Windows / Linux** | **Docker Compose** | See Docker Deployment below. |

*The native desktop shell includes automatic background sidecar lifecycle management, native window framing, and connects automatically to your local Ollama cluster on `127.0.0.1:11434`.*

---

## 🐳 2. 1-Click Docker Compose Deployment

Run the complete Socratic Workbench inside an isolated, multi-stage production container with zero local toolchain setup.

### Quick Start
```bash
# Clone the repository
git clone https://gitea.2464.cz/ai/synapse.git
cd synapse

# Launch with Docker Compose
docker compose up -d
```

### Access & Persistence
- **Web UI:** Open **`http://localhost:8000`** in any web browser.
- **Volume Mounts:**
  - `./topics`: Mapped to `/workspace/topics` to persist all generated lessons and labs.
  - `./data`: Mapped to `/workspace/data` to persist your SQLite mastery state and settings.
  - `./exports`: Mapped to `/workspace/exports` for `.synpack` course packages.
- **Ollama Host Connectivity:** The container includes `extra_hosts: host.docker.internal:host-gateway`, enabling immediate connectivity to Ollama running on your host machine at `http://host.docker.internal:11434`.

### Shutdown
```bash
docker compose down
```

---

## 🛠 3. Developer Source Setup

For engineers developing the Python curriculum engine or React frontend.

### Prerequisites

| Platform | Minimum OS | Python | Node.js | Recommended LLM Engine |
| :--- | :--- | :--- | :--- | :--- |
| **macOS** | macOS 12+ (Apple Silicon / Intel) | 3.11+ | 20+ (LTS) | Ollama (native Metal acceleration) |
| **Windows** | Windows 10/11 (PowerShell or WSL2) | 3.11+ | 20+ (LTS) | Ollama for Windows (CUDA / DirectML) |
| **Linux** | Ubuntu 22.04+, Fedora 38+, Arch | 3.11+ | 20+ (LTS) | Ollama (native ROCm / CUDA) or LocalAI |

### Source Installation Steps

#### Step 1: Clone Repository
```bash
git clone https://gitea.2464.cz/ai/synapse.git
cd synapse
```

#### Step 2: Python Backend Environment
Set up an isolated virtual environment:

**macOS & Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### Step 3: Frontend Compilation
Install frontend dependencies and build production assets:
```bash
cd app/frontend
npm install
npm run build
cd ../..
```

#### Step 4: Launching from Source

**Web Workbench:**
```bash
./bin/synapse serve --port 8000
# Open http://localhost:8000
```

**Desktop Shell (Electron):**
```bash
./bin/synapse desktop
```

---

## 4. Packaging Standalone Desktop Installers

To compile zero-dependency standalone binaries:

```bash
cd app/desktop
npm install

# macOS (.app bundle and .dmg disk image)
npm run build:mac

# Windows (.exe installer and portable binary)
npm run build:win

# Linux (.AppImage and .deb package)
npm run build:linux
```

All compiled binaries are generated in `dist/desktop/`.
