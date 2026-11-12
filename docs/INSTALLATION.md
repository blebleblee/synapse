# Synapse Installation & Platform Guide

Comprehensive guide for installing, running, and building **Synapse** across **macOS**, **Windows**, and **Linux**.

---

## 1. System Prerequisites

| Platform | Minimum OS | Python | Node.js | Recommended LLM Engine |
| :--- | :--- | :--- | :--- | :--- |
| **macOS** | macOS 12+ (Apple Silicon / Intel) | 3.11+ | 20+ (LTS) | Ollama (native Metal acceleration) |
| **Windows** | Windows 10/11 (PowerShell or WSL2) | 3.11+ | 20+ (LTS) | Ollama for Windows (CUDA / DirectML) |
| **Linux** | Ubuntu 22.04+, Fedora 38+, Arch | 3.11+ | 20+ (LTS) | Ollama (native ROCm / CUDA) or LocalAI |

---

## 2. Installation Steps

### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/synapse.git
cd synapse
```

### Step 2: Python Backend Environment
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

### Step 3: Frontend Compilation
Install frontend dependencies and build production assets:
```bash
cd app/frontend
npm install
npm run build
cd ../..
```

---

## 3. Running Synapse

### Mode A: Integrated Web Workbench
Serves the responsive single-page workstation, FastAPI REST APIs, and WebSocket PTY terminal on port 8000:
```bash
./bin/synapse serve --port 8000
```
Open **`http://localhost:8000`** in Chrome, Firefox, Safari, or Edge.

### Mode B: Native Desktop Window (Electron)
Launches the standalone desktop window with native macOS titlebar integration, custom menus, and automatic backend sidecar management:
```bash
./bin/synapse desktop
```
*(On first execution, dependencies in `app/desktop` will be installed automatically).*

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
