const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const net = require('net');
const http = require('http');

let mainWindow;
let backendProcess;

function getFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.listen(0, '127.0.0.1', () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
    server.on('error', reject);
  });
}

function waitForServer(port, retries = 30) {
  return new Promise((resolve, reject) => {
    const check = (attempt) => {
      http.get(`http://127.0.0.1:${port}/`, (res) => resolve())
        .on('error', () => {
          if (attempt >= retries) reject(new Error('Backend did not start'));
          else setTimeout(() => check(attempt + 1), 500);
        });
    };
    check(0);
  });
}

app.whenReady().then(async () => {
  const port = await getFreePort();
  const isDev = !app.isPackaged;
  const ext = process.platform === 'win32' ? '.exe' : '';

  let backendPath;
  let args;
  let cwd;

  if (isDev) {
    // Prefer the built exe, fall back to python manage.py
    const exePath = path.join(__dirname, 'dist', `clinic-backend${ext}`);
    if (fs.existsSync(exePath)) {
      console.log(`[electron] Resolved backend path: ${exePath}`);
      console.log(`[electron] Using built exe: ${exePath}`);
      backendPath = exePath;
      args = ['runserver', `127.0.0.1:${port}`, '--noreload'];
    } else {
      console.log('[electron] Using python manage.py (no built exe found)');
      backendPath = 'python';
      args = ['manage.py', 'runserver', `127.0.0.1:${port}`, '--noreload'];
      cwd = __dirname;
    }
  } else {
    backendPath = path.join(process.resourcesPath, 'backend', `clinic-backend${ext}`);
    console.log(`[electron] Resolved backend path: ${backendPath}`);
    args = ['runserver', `127.0.0.1:${port}`, '--noreload'];
  }

  backendProcess = spawn(backendPath, args, { cwd, stdio: 'pipe' });

  backendProcess.stdout.on('data', (d) => console.log(`[backend] ${d}`));
  backendProcess.stderr.on('data', (d) => console.error(`[backend] ${d}`));

  try {
    await Promise.race([
      waitForServer(port),
      new Promise((_, rej) => {
        backendProcess.on('exit', (code) => rej(new Error(`Backend exited with code ${code}`)));
      }),
    ]);
  } catch (err) {
    console.error('Failed to start backend:', err);
    app.quit();
    return;
  }

  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  });

  mainWindow.loadURL(`http://127.0.0.1:${port}/`);
  mainWindow.on('closed', () => { mainWindow = null; });
});

app.on('window-all-closed', () => {
  if (backendProcess) { backendProcess.kill(); }
  app.quit();
});
