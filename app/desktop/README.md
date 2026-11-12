# Synapse Native Desktop Shell (Electron Wrapper)

Standalone desktop application wrapper for the **Synapse AI Learning Workbench**, packaging the compiled web workstation and managing the local Python backend service as a resilient sidecar.

---

## 1. Architecture

* **Frontend:** Loads the compiled single-page application from `app/frontend/dist` via `http://127.0.0.1:8000/`.
* **Backend Sidecar:** Automatically checks whether `./bin/synapse serve` is already running on port 8000; if not, spawns and monitors the Python FastAPI service as a managed child process.
* **PTY Terminal & WebSocket:** Connects natively to the local FastAPI WebSocket PTY server on `/ws/terminal`.
* **Security:** Runs with strict `contextIsolation: true`, `sandbox: true`, and `nodeIntegration: false`.

---

## 2. Quick Start & Development

### A. Prerequisites
Ensure the frontend is compiled:
```bash
cd app/frontend
npm run build
```

### B. Launching Desktop Shell
From the repository root using the canonical CLI:
```bash
./bin/synapse desktop
```

Or from `app/desktop`:
```bash
cd app/desktop
npm install
npm start
```

### C. Live Development Mode
To connect the desktop window to a running Vite dev server (`http://localhost:5173`):
```bash
npm run dev
```

---

## 3. Packaging Standalone Binaries

The desktop shell uses `electron-builder` to package native installer packages:

### macOS (.app and .dmg)
```bash
cd app/desktop
npm run build:mac
```
Output: `dist/desktop/Synapse Workbench-1.0.0.dmg` and `.app`.

### Windows (.exe / NSIS Installer)
```bash
cd app/desktop
npm run build:win
```

### Linux (AppImage / .deb)
```bash
cd app/desktop
npm run build:linux
```
