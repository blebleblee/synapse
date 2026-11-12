/**
 * Synapse Desktop Shell - Main Electron Process
 * Orchestrates native window lifecycle, local Python backend sidecar, and native menus.
 */

const { app, BrowserWindow, Menu, shell, ipcMain, dialog } = require('electron');
const path = require('path');
const http = require('http');
const { spawn } = require('child_process');

let mainWindow = null;
let backendProcess = null;
let isQuitting = false;

const BACKEND_PORT = process.env.SYNAPSE_PORT || 8000;
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;
const WORKSPACE_ROOT = path.resolve(__dirname, '../../..');

/**
 * Checks if the Synapse FastAPI backend is responsive.
 */
function checkBackendHealth(timeoutMs = 1500) {
  return new Promise((resolve) => {
    const req = http.get(`${BACKEND_URL}/api/status`, { timeout: timeoutMs }, (res) => {
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });
  });
}

/**
 * Starts the local Synapse backend server if not already running.
 */
async function ensureBackendRunning() {
  const isRunning = await checkBackendHealth();
  if (isRunning) {
    console.log(`[Desktop] Synapse backend already active at ${BACKEND_URL}`);
    return true;
  }

  console.log(`[Desktop] Spawning local Synapse backend service on port ${BACKEND_PORT}...`);
  const pythonBin = path.join(WORKSPACE_ROOT, '.venv/bin/python');
  const synapseBin = path.join(WORKSPACE_ROOT, 'bin/synapse');

  try {
    backendProcess = spawn(pythonBin, [synapseBin, 'serve', '--port', String(BACKEND_PORT)], {
      cwd: WORKSPACE_ROOT,
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
      stdio: ['ignore', 'pipe', 'pipe'],
      detached: false,
    });

    backendProcess.stdout.on('data', (data) => {
      console.log(`[Backend stdout] ${data.toString().trim()}`);
    });

    backendProcess.stderr.on('data', (data) => {
      console.error(`[Backend stderr] ${data.toString().trim()}`);
    });

    backendProcess.on('exit', (code, signal) => {
      console.log(`[Desktop] Backend process exited with code ${code}, signal ${signal}`);
      backendProcess = null;
    });

    // Poll until backend is online (up to 20 seconds)
    const startTime = Date.now();
    while (Date.now() - startTime < 20000) {
      await new Promise((r) => setTimeout(r, 600));
      if (await checkBackendHealth()) {
        console.log(`[Desktop] Synapse backend online and verified at ${BACKEND_URL}`);
        return true;
      }
    }

    console.error('[Desktop] Backend failed to start within timeout');
    return false;
  } catch (err) {
    console.error('[Desktop] Failed to spawn backend process:', err);
    return false;
  }
}

/**
 * Creates the primary native window.
 */
function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1024,
    minHeight: 700,
    backgroundColor: '#121214',
    title: 'Synapse AI Learning Workbench',
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    trafficLightPosition: { x: 14, y: 14 },
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
    },
  });

  const targetUrl = process.env.ELECTRON_DEV ? 'http://localhost:5173' : BACKEND_URL;

  mainWindow.loadURL(targetUrl).catch((err) => {
    console.error('[Desktop] Failed to load URL:', err);
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http:') || url.startsWith('https:')) {
      shell.openExternal(url);
    }
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

/**
 * Sets up native application menu.
 */
function setupNativeMenu() {
  const isMac = process.platform === 'darwin';

  const template = [
    ...(isMac
      ? [
          {
            label: app.name,
            submenu: [
              { role: 'about' },
              { type: 'separator' },
              { role: 'services' },
              { type: 'separator' },
              { role: 'hide' },
              { role: 'hideOthers' },
              { role: 'unhide' },
              { type: 'separator' },
              { role: 'quit' },
            ],
          },
        ]
      : []),
    {
      label: 'File',
      submenu: [isMac ? { role: 'close' } : { role: 'quit' }],
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' },
      ],
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        { role: 'zoom' },
        ...(isMac
          ? [{ type: 'separator' }, { role: 'front' }, { type: 'separator' }, { role: 'window' }]
          : [{ role: 'close' }]),
      ],
    },
    {
      role: 'help',
      submenu: [
        {
          label: 'Synapse Project Repository',
          click: async () => {
            await shell.openExternal('https://github.com');
          },
        },
      ],
    },
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

/**
 * Graceful termination of backend child process.
 */
function terminateBackend() {
  if (backendProcess) {
    console.log('[Desktop] Terminating backend child process...');
    try {
      backendProcess.kill('SIGTERM');
      setTimeout(() => {
        if (backendProcess) {
          backendProcess.kill('SIGKILL');
        }
      }, 2000);
    } catch (e) {
      console.error('[Desktop] Error terminating backend:', e);
    }
    backendProcess = null;
  }
}

// IPC Handlers
ipcMain.handle('open-external', async (_, url) => {
  if (url && (url.startsWith('http:') || url.startsWith('https:'))) {
    await shell.openExternal(url);
  }
});

ipcMain.on('reload-app', () => {
  if (mainWindow) mainWindow.reload();
});

ipcMain.on('toggle-devtools', () => {
  if (mainWindow) mainWindow.webContents.toggleDevTools();
});

// App Lifecycle
app.whenReady().then(async () => {
  setupNativeMenu();

  const ready = await ensureBackendRunning();
  if (!ready) {
    dialog.showErrorBox(
      'Backend Launch Error',
      'Synapse backend service could not be started. Ensure python and dependencies are installed in .venv.'
    );
  }

  createMainWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on('before-quit', () => {
  isQuitting = true;
  terminateBackend();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
