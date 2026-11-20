/**
 * Synapse Desktop Shell - Main Electron Process
 * Orchestrates native window lifecycle, local Python backend sidecar, and native menus.
 */

const { app, BrowserWindow, Menu, shell, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { spawn } = require('child_process');

// Explicitly define application display name across OS process tree
process.title = 'Synapse Workbench';
app.name = 'Synapse Workbench';
app.setName('Synapse Workbench');

// Prevent unhandled EPIPE crashes when launched as a GUI app without a terminal
if (process.stdout) {
  process.stdout.on('error', (err) => {
    if (err && err.code === 'EPIPE') return;
  });
}
if (process.stderr) {
  process.stderr.on('error', (err) => {
    if (err && err.code === 'EPIPE') return;
  });
}

process.on('uncaughtException', (err) => {
  if (err && (err.code === 'EPIPE' || err.message?.includes('EPIPE'))) {
    return;
  }
  try {
    console.error('[UncaughtException]', err);
  } catch (_) {}
});

let logStream = null;
const origLog = console.log;
const origError = console.error;

console.log = function (...args) {
  if (logStream) {
    try {
      logStream.write(`[LOG ${new Date().toISOString()}] ${args.join(' ')}\n`);
    } catch (_) {}
  }
  try {
    origLog.apply(console, args);
  } catch (err) {
    if (err && err.code === 'EPIPE') return;
  }
};

console.error = function (...args) {
  if (logStream) {
    try {
      logStream.write(`[ERR ${new Date().toISOString()}] ${args.join(' ')}\n`);
    } catch (_) {}
  }
  try {
    origError.apply(console, args);
  } catch (err) {
    if (err && err.code === 'EPIPE') return;
  }
};

let mainWindow = null;
let backendProcess = null;
let isQuitting = false;
let lastBackendError = '';
let activeWorkspaceDir = '';

const BACKEND_PORT = process.env.SYNAPSE_PORT || 8000;
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;
const WORKSPACE_ROOT = path.resolve(__dirname, '../../..');

/**
 * Checks if the Synapse FastAPI backend is responsive.
 */
function checkBackendHealth(timeoutMs = 4000) {
  return new Promise((resolve) => {
    const urls = [
      `http://127.0.0.1:${BACKEND_PORT}/api/health`,
      `http://localhost:${BACKEND_PORT}/api/health`,
      `http://127.0.0.1:${BACKEND_PORT}/api/status`,
    ];

    let settled = false;
    let attemptsLeft = urls.length;

    for (const url of urls) {
      try {
        const req = http.get(url, { timeout: timeoutMs }, (res) => {
          let body = '';
          res.on('data', (chunk) => { body += chunk; });
          res.on('end', () => {
            if (!settled && res.statusCode === 200) {
              try {
                const data = JSON.parse(body);
                if (data.status === 'ok' && data.version === app.getVersion()) {
                  settled = true;
                  resolve(true);
                  return;
                } else {
                  console.log(`[Desktop] Found backend at ${url} but version mismatch (expected ${app.getVersion()}, got ${data.version}). Ignoring.`);
                }
              } catch (_) {}
            }
            attemptsLeft -= 1;
            if (attemptsLeft === 0 && !settled) resolve(false);
          });
        });
        req.on('error', () => {
          attemptsLeft -= 1;
          if (attemptsLeft === 0 && !settled) resolve(false);
        });
        req.on('timeout', () => {
          req.destroy();
          attemptsLeft -= 1;
          if (attemptsLeft === 0 && !settled) resolve(false);
        });
      } catch (_) {
        attemptsLeft -= 1;
        if (attemptsLeft === 0 && !settled) resolve(false);
      }
    }
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

  const isWin = process.platform === 'win32';
  let spawnCmd = null;
  let spawnArgs = null;

  // 1. On Windows, prioritize bundled embedded Python runtime (resources/python/python.exe)
  if (isWin) {
    const candidatePythons = [
      path.join(process.resourcesPath || '', 'python', 'python.exe'),
      path.join(path.dirname(process.execPath), 'python', 'python.exe'),
      path.join(path.dirname(process.execPath), 'resources', 'python', 'python.exe'),
      path.join(WORKSPACE_ROOT, 'dist', 'python-win', 'python.exe'),
    ];

    for (const pyPath of candidatePythons) {
      if (fs.existsSync(pyPath)) {
        spawnCmd = pyPath;
        spawnArgs = ['-m', 'learning_engine.cli', 'serve', '--port', String(BACKEND_PORT)];
        console.log(`[Desktop] Found bundled embedded Windows Python sidecar: ${spawnCmd}`);
        break;
      }
    }
  }

  // 2. On macOS/Linux (or Windows if standalone PyInstaller binary is present), check compiled sidecar
  if (!spawnCmd) {
    const exeName = isWin ? 'synapse.exe' : 'synapse';
    const candidateBins = [
      path.join(process.resourcesPath || '', 'bin', exeName),
      path.join(process.resourcesPath || '', exeName),
      path.join(path.dirname(process.execPath), 'bin', exeName),
      path.join(path.dirname(process.execPath), exeName),
      path.join(WORKSPACE_ROOT, 'dist', 'bin', exeName),
    ];

    for (const binPath of candidateBins) {
      if (fs.existsSync(binPath)) {
        try {
          if (fs.statSync(binPath).size > 1024 * 1024) {
            spawnCmd = binPath;
            spawnArgs = ['serve', '--port', String(BACKEND_PORT)];
            if (process.platform !== 'win32') {
              try { fs.chmodSync(spawnCmd, 0o755); } catch (_) {}
            }
            console.log(`[Desktop] Found standalone backend sidecar: ${spawnCmd}`);
            break;
          }
        } catch (_) {}
      }
    }
  }

  // 3. Fallback to Python venv in development mode
  if (!spawnCmd) {
    const pythonBin = isWin
      ? path.join(WORKSPACE_ROOT, '.venv', 'Scripts', 'python.exe')
      : path.join(WORKSPACE_ROOT, '.venv', 'bin', 'python');
    const synapseBin = path.join(WORKSPACE_ROOT, 'bin', 'synapse');

    if (fs.existsSync(pythonBin)) {
      spawnCmd = pythonBin;
      spawnArgs = [synapseBin, 'serve', '--port', String(BACKEND_PORT)];
    } else {
      spawnCmd = isWin ? 'python' : 'python3';
      spawnArgs = ['-m', 'learning_engine.cli', 'serve', '--port', String(BACKEND_PORT)];
    }
  }

  // Resolve persistent writable workspace and topics directories
  let workspaceDir;
  let topicsDir;

  const isDev = !app.isPackaged;
  if (isDev && fs.existsSync(path.join(WORKSPACE_ROOT, 'topics'))) {
    workspaceDir = WORKSPACE_ROOT;
    topicsDir = path.join(WORKSPACE_ROOT, 'topics');
  } else {
    const portableBase = process.env.PORTABLE_EXECUTABLE_DIR || path.dirname(process.execPath);
    const portableTopics = path.join(portableBase, 'topics');

    if (process.platform === 'win32' && (fs.existsSync(portableTopics) || process.env.PORTABLE_EXECUTABLE_DIR)) {
      workspaceDir = portableBase;
      topicsDir = portableTopics;
    } else {
      const userData = app.getPath('userData');
      workspaceDir = userData;
      topicsDir = path.join(userData, 'topics');
    }
  }

  try {
    fs.mkdirSync(topicsDir, { recursive: true });
    fs.mkdirSync(path.join(workspaceDir, 'data'), { recursive: true });
    fs.mkdirSync(path.join(workspaceDir, 'exports', 'packages'), { recursive: true });
  } catch (err) {
    console.error('[Desktop] Failed to prepare workspace directories:', err);
  }

  activeWorkspaceDir = workspaceDir;
  const logFile = path.join(workspaceDir, 'backend.log');
  if (!logStream) {
    try {
      logStream = fs.createWriteStream(logFile, { flags: 'a' });
    } catch (_) {}
  }

  const spawnEnv = {
    ...process.env,
    LANG: process.env.LANG || 'en_US.UTF-8',
    LC_ALL: process.env.LC_ALL || 'en_US.UTF-8',
    PYTHONUNBUFFERED: '1',
    SYNAPSE_WORKSPACE: workspaceDir,
    SYNAPSE_TOPICS_DIR: topicsDir,
    SYNAPSE_RESOURCES_PATH: process.resourcesPath || '',
  };

  if (process.platform === 'darwin') {
    const defaultMacPaths = ['/opt/homebrew/bin', '/usr/local/bin', '/usr/bin', '/bin', '/usr/sbin', '/sbin'];
    const currentPath = process.env.PATH || '';
    const missing = defaultMacPaths.filter((p) => !currentPath.includes(p));
    if (missing.length > 0) {
      spawnEnv.PATH = `${missing.join(':')}:${currentPath}`;
    }
  }

  if (spawnCmd) {
    const pyDir = path.dirname(spawnCmd);
    const sitePkgs = path.join(pyDir, 'site-packages');
    const pathSep = isWin ? ';' : ':';
    spawnEnv.PATH = `${pyDir}${pathSep}${path.join(pyDir, 'Scripts')}${pathSep}${process.env.PATH || ''}`;
    spawnEnv.PYTHONPATH = `${sitePkgs}${pathSep}${pyDir}${pathSep}${process.env.PYTHONPATH || ''}`;
  }

  try {
    backendProcess = spawn(spawnCmd, spawnArgs, {
      cwd: workspaceDir,
      env: spawnEnv,
      stdio: ['ignore', 'pipe', 'pipe'],
      detached: false,
    });

    backendProcess.stdout.on('data', (data) => {
      const msg = data.toString().trim();
      console.log(`[Backend stdout] ${msg}`);
    });

    backendProcess.stderr.on('data', (data) => {
      const msg = data.toString().trim();
      console.error(`[Backend stderr] ${msg}`);
      lastBackendError = (lastBackendError + '\n' + msg).slice(-1500);
    });

    backendProcess.on('exit', (code, signal) => {
      console.log(`[Desktop] Backend process exited with code ${code}, signal ${signal}`);
      if (code !== 0 && code !== null) {
        lastBackendError = (lastBackendError + `\nProcess exited with code ${code}`).slice(-1500);
      }
      backendProcess = null;
    });

    // Poll until backend is online (up to 45 seconds on cold launch)
    const startTime = Date.now();
    while (Date.now() - startTime < 45000) {
      await new Promise((r) => setTimeout(r, 800));
      if (await checkBackendHealth()) {
        console.log(`[Desktop] Synapse backend online and verified at ${BACKEND_URL}`);
        return true;
      }
      if (!backendProcess) {
        break;
      }
    }

    console.error('[Desktop] Backend failed to start within timeout');
    if (fs.existsSync(logFile)) {
      const lastLogs = fs.readFileSync(logFile, 'utf8').split('\n').slice(-20).join('\n');
      console.error(`[Desktop] Recent backend log output:\n${lastLogs}`);
    }
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
  const appIcon = path.join(__dirname, '../assets/icon.png');

  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1024,
    minHeight: 700,
    backgroundColor: '#121214',
    title: 'Synapse Workbench',
    icon: fs.existsSync(appIcon) ? appIcon : undefined,
    frame: true,
    titleBarStyle: 'default',
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
        {
          label: 'Clear Cache & Hard Reload',
          click: async () => {
            const { session } = require('electron');
            await session.defaultSession.clearCache();
            if (mainWindow) mainWindow.reload();
          }
        },
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
      if (process.platform === 'win32') {
        const { execSync } = require('child_process');
        try {
          execSync(`taskkill /pid ${backendProcess.pid} /T /F`, { stdio: 'ignore' });
        } catch (_) {
          backendProcess.kill();
        }
      } else {
        backendProcess.kill('SIGTERM');
        setTimeout(() => {
          if (backendProcess) {
            backendProcess.kill('SIGKILL');
          }
        }, 2000);
      }
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
  app.setName('Synapse Workbench');

  // Automatic Cache Busting on Version Upgrade
  const { session } = require('electron');
  const versionFile = path.join(app.getPath('userData'), 'last-version.txt');
  const currentVersion = app.getVersion();
  try {
    const lastVersion = fs.existsSync(versionFile) ? fs.readFileSync(versionFile, 'utf8').trim() : '';
    if (lastVersion !== currentVersion) {
      console.log(`[Desktop] App version changed from '${lastVersion}' to '${currentVersion}'. Clearing Chromium cache...`);
      await session.defaultSession.clearCache();
      fs.writeFileSync(versionFile, currentVersion, 'utf8');
    }
  } catch (err) {
    console.error('[Desktop] Cache clear check failed:', err);
  }

  // Set dock icon on macOS
  if (process.platform === 'darwin' && app.dock) {
    const dockIcon = path.join(__dirname, '../assets/icon.png');
    if (fs.existsSync(dockIcon)) {
      app.dock.setIcon(dockIcon);
    }
  }

  setupNativeMenu();

  const ready = await ensureBackendRunning();
  if (!ready) {
    const detail = lastBackendError.trim() || 'Backend process exited prematurely or timed out waiting for http://127.0.0.1:8000/api/status.';
    const logPath = path.join(activeWorkspaceDir || app.getPath('userData'), 'backend.log');
    dialog.showErrorBox(
      'Backend Launch Error',
      `Synapse backend service could not be started.\n\nDiagnostic Output:\n${detail}\n\nLog file location:\n${logPath}`
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
