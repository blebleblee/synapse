# Synapse Installation & Platform Guide

Comprehensive guide for installing, running, and building **Synapse** across **macOS**, **Windows**, and **Linux**.

---

## 🚀 1. 1-Click Desktop App (Zero Build / Zero Terminal)

The easiest way to run Synapse. No Python, Node.js, or package compilation required.

Download the latest version from the [Releases page](https://github.com/blebleblee/synapse/releases/latest):

| Platform | File | How to start |
| :--- | :--- | :--- |
| **macOS (Apple Silicon)** | `Synapse-Workbench-<version>-arm64.dmg` | Open it, drag **Synapse Workbench** to `/Applications`, launch it. (`…-arm64.zip` contains the same app without an installer.) |
| **Windows** | `Synapse-Workbench-Setup-<version>.exe` | Run the installer. |
| **Windows (no install)** | `Synapse-Workbench-Portable-<version>.exe` | Run it directly. |
| **Windows (offline bundle)** | `Synapse-Workbench-Portable-<version>-win-x64.zip` | Unzip and run the `.exe`. The curriculum is a `topics/` folder next to it. |
| **Linux / any OS** | `synapse-<version>-py3-none-any.whl` | See the Python wheel section below. |
| **Any platform** | Docker Compose | See the Docker section below. |

The desktop apps include the Python backend and start and stop it with the window. They connect to Ollama on `127.0.0.1:11434` or to a configured cloud provider.

---

## 🪟 2. Windows Offline Bundle

The offline bundle keeps the curriculum outside the executable:

```text
Synapse-Workbench-Portable-<version>-win-x64/
├── Synapse-Workbench-Portable.exe
├── README.txt
└── topics/            <-- curriculum as plain Markdown
    ├── arts/
    ├── computing/
    └── ...
```

Synapse finds `topics/` next to the executable (or uses `SYNAPSE_TOPICS_DIR`), so you can update or add topics without a new `.exe`. The terminal uses PowerShell/CMD; WSL isn't required.

---

## 📦 3. Python Wheel (`.whl`) Installation (Linux, macOS & Windows WSL2)

The `.whl` package (`synapse-<version>-py3-none-any.whl`) is pure Python and runs across **Linux**, **macOS**, and **Windows (via WSL2)**.

### A. Linux Installation (Ubuntu, Debian, Fedora, Arch, SUSE)
Linux is a first-class citizen with 100% native POSIX PTY terminal support:

```bash
# 1. Ensure Python 3.10+ and venv are installed
sudo apt update && sudo apt install -y python3 python3-venv  # Debian/Ubuntu
# or: sudo dnf install python3                              # Fedora/RHEL

# 2. Create and activate an isolated environment
python3 -m venv ~/synapse-env
source ~/synapse-env/bin/activate

# 3. Install the official Synapse wheel
pip install synapse-<version>-py3-none-any.whl

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
   pip install synapse-<version>-py3-none-any.whl
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
git clone <repo-url>
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
git clone <repo-url>
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
