import { app, BrowserWindow, ipcMain, Menu } from 'electron';
import path from 'path';
import { fileURLToPath } from 'url';
import isDev from 'electron-is-dev';
import { spawn, execFile } from 'child_process';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

let mainWindow;
let backendProcess = null;

const createWindow = () => {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    title: 'A2A Multi-Agent System',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
    },
    frame: true,
    titleBarStyle: 'default',
  });

  const startURL = isDev
    ? 'http://localhost:5173'
    : `file://${path.join(__dirname, '../dist/index.html')}`;

  mainWindow.loadURL(startURL);

  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
};

const startBackend = async () => {
  return new Promise((resolve, reject) => {
    // In dev: backend lives at <project>/run_backend.py and cwd is the project root.
    // When packaged: backend source is copied under resources/backend/ by
    // extraResources, and the SQLite/chroma data files must live somewhere
    // writable (Program Files is read-only), so cwd is the userData dir.
    let backendRoot, backendScript, cwd, pythonPath;
    if (isDev) {
      backendRoot = path.join(__dirname, '../../');
      backendScript = path.join(backendRoot, 'run_backend.py');
      cwd = backendRoot;
      pythonPath = backendRoot;
    } else {
      backendRoot = path.join(process.resourcesPath, 'backend');
      backendScript = path.join(backendRoot, 'run_backend.py');
      // Writable working dir: userData. The backend's relative paths
      // (./agents.db, ./data/agent_memory.db, ./data/chroma) land here.
      // Program Files is read-only, so we can't use the install dir.
      cwd = app.getPath('userData');
      fs.mkdirSync(path.join(cwd, 'data'), { recursive: true });
      pythonPath = backendRoot;
    }

    if (!fs.existsSync(backendScript)) {
      reject(new Error('Backend script not found: ' + backendScript));
      return;
    }

    try {
      backendProcess = spawn('python', [backendScript], {
        cwd: cwd,
        stdio: ['pipe', 'pipe', 'pipe'],
        env: {
          ...process.env,
          PYTHONPATH: pythonPath,
        },
      });

      backendProcess.stdout.on('data', (data) => {
        console.log('[Backend]', data.toString());
        if (data.toString().includes('Application startup complete')) {
          resolve();
        }
      });

      backendProcess.stderr.on('data', (data) => {
        console.error('[Backend Error]', data.toString());
      });

      backendProcess.on('close', (code) => {
        console.log('[Backend] Process closed with code:', code);
        backendProcess = null;
      });

      backendProcess.on('error', (err) => {
        console.error('[Backend] Error starting process:', err);
        reject(err);
      });

      setTimeout(() => {
        if (!backendProcess) {
          reject(new Error('Backend startup timeout'));
        }
      }, 30000);
    } catch (err) {
      reject(err);
    }
  });
};

const setupMenu = () => {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Exit',
          accelerator: 'Ctrl+Q',
          click: () => {
            app.quit();
          },
        },
      ],
    },
    {
      label: 'View',
      submenu: [
        {
          label: 'Toggle Developer Tools',
          accelerator: 'F12',
          click: () => {
            mainWindow.webContents.toggleDevTools();
          },
        },
        {
          label: 'Refresh',
          accelerator: 'Ctrl+R',
          click: () => {
            mainWindow.webContents.reload();
          },
        },
      ],
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About',
          click: () => {
            console.log('A2A Multi-Agent System v1.0.0');
          },
        },
      ],
    },
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
};

app.on('ready', async () => {
  try {
    console.log('Starting backend server...');
    await startBackend();
    console.log('Backend server started successfully');
  } catch (err) {
    console.error('Failed to start backend:', err);
  }

  createWindow();
  setupMenu();
});

app.on('window-all-closed', () => {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
  app.quit();
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

ipcMain.handle('get-backend-status', () => {
  return {
    running: backendProcess !== null && !backendProcess.killed,
  };
});

ipcMain.handle('restart-backend', async () => {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
  try {
    await startBackend();
    return { success: true };
  } catch (err) {
    return { success: false, error: err.message };
  }
});