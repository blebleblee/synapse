# Synapse Installation & Platform Guide

Comprehensive guide for installing, running, and building **Synapse** across **macOS**, **Windows**, and **Linux**.

---

## 🚀 1. 1-Click Desktop App (Zero Build / Zero Terminal)

The easiest way to run Synapse. No Python, Node.js, or package compilation required.

Download pre-compiled Release Candidate binaries from the **[Releases](https://gitea.2464.cz/ai/synapse/releases)** page:

| Platform | Download Format | Installation Instructions |
| :--- | :--- | :--- |
| **Windows (Portable)** | **`.exe` (Standalone Portable App)** | Download `Synapse-Workbench-Portable-1.0.0.exe`. Place your `./topics/` curriculum folder alongside the executable and double-click to launch! No Python or installation required. |
| **macOS (Apple Silicon)** | **`.dmg` (Disk Image Installer)** | Open `Synapse-Workbench-1.0.0-arm64.dmg`, drag **Synapse Workbench** to `/Applications`, and launch from Spotlight or Launchpad. |
| **macOS (Portable Bundle)** | **`.zip` (App Archive)** | Decompress `Synapse-Workbench-1.0.0-arm64-mac.zip` and launch **Synapse Workbench.app** directly. |
| **Linux (CLI / Server)** | **`.whl` (Python Wheel)** | See Python Wheel Installation below. |
| **Any Platform** | **Docker Compose** | See Docker Deployment below. |

*The native desktop shell includes automatic background sidecar lifecycle management, native window framing, and connects automatically to your local Ollama cluster on `127.0.0.1:11434` or cloud inference gateways.*

---

## 🪟 2. Windows Portable Binary & Topics Addon Architecture

The Windows distribution is fully decoupled from Python environments:

1. **Executable Structure:**
   ```text
   Synapse-Portable-Windows/
   ├── Synapse-Workbench-Portable-1.0.0.exe
   ├── README.txt
   └── topics/                   <-- Curriculum Addon (Pure Markdown)
       ├── arts/
       ├── computing/
       └── ...
   ```
2. **Platform-Independent Addon:** The curriculum content is strictly externalized. Synapse discovers `./topics/` next to the executable (or via `SYNAPSE_TOPICS_DIR`). You can upgrade or add topics without updating the `.exe`.
3. **Native Shell Execution:** The terminal drawer features built-in Windows PowerShell/CMD bridging, allowing commands and labs to be executed directly without requiring WSL.

---

## 📦 3. Python Wheel (`.whl`) Installation (Linux, macOS & Windows WSL2)

The `.whl` package (`synapse-1.0.0-py3-none-any.whl`) is pure Python and runs across **Linux**, **macOS**, and **Windows (via WSL2)**.

### A. Linux Installation (Ubuntu, Debian, Fedora, Arch, SUSE)
Linux is a first-class citizen with 100% native POSIX PTY terminal support:

```bash
# 1. Ensure Python 3.10+ and venv are installed
sudo apt update && sudo apt install -y python3 python3-venv  # Debian/Ubuntu
# or: sudo dnf install python3                              # Fedora/RHEL

# 2. Create and activate an isolated environment
python3 -m venv ~/synapse-env
source ~/synapse-env/bin/activate

# 3. Install the official Synapse wheel directly from Gitea
pip install https://gitea.2464.cz/ai/synapse/releases/download/v1.0.0/synapse-1.0.0-py3-none-any.whl

# 4. Launch Synapse Workbench
synapse serve --port 8000
```
Open **`http://localhost:8000`** in any web browser.

### B. Windows Installation (via WSL2)
For full native terminal drawer support on Windows, run inside **WSL2** (Windows Subsystem for Linux):

1. Open PowerShell and ensure WSL2 is active:
   ```powershell
   wsl --install
   ```
2. Launch your WSL2 terminal (Ubuntu) and execute the standard Linux commands:
   ```bash
   python3 -m venv ~/synapse-env
   source ~/synapse-env/bin/activate
   pip install https://gitea.2464.cz/ai/synapse/releases/download/v1.0.0/synapse-1.0.0-py3-none-any.whl
   synapse serve --port 8000
   ```
3. Open **`http://localhost:8000`** in Chrome, Edge, or Firefox in Windows.

*(Note: On raw native Windows Command Prompt or PowerShell without WSL, the CLI curriculum engine functions normally, but the interactive in-browser PTY terminal requires POSIX drivers provided by WSL).*

### C. Useful CLI Commands
Once the wheel is installed, the global `synapse` command is available in your environment:
```bash
synapse serve --port 8000       # Start the Socratic Workbench server
synapse status                  # Show workspace curriculum completion statistics
synapse lint --domain arts      # Run semantic linter & markdown quality checks
synapse review computing/linux  # Run adversarial cross-model quality audit
synapse export computing        # Compile complete domain into printable handbook
```

---

## 🐳 4. 1-Click Docker Compose Deployment

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
