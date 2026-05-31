const { app, BrowserWindow, Menu } = require('electron');
const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const net = require('net');
const http = require('http');

let mainWindow;
let backendProcess;

function killBackend() {
  if (!backendProcess) return;
  try {
    if (process.platform === 'win32') {
      execSync(`taskkill /F /T /PID ${backendProcess.pid}`, {
        stdio: 'ignore', windowsHide: true,
      });
    } else {
      backendProcess.kill('SIGTERM');
    }
  } catch (_) {}
  backendProcess = null;
}

function cleanupOrphans() {
  try {
    if (process.platform === 'win32') {
      execSync('taskkill /F /IM clinic-backend.exe 2>nul', { stdio: 'ignore' });
    }
  } catch (_) {}
}

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

function loadingPageHTML() {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Loading…</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f8fafc; display: flex; align-items: center; justify-content: center;
  height: 100vh; color: #1e293b;
}
.container { text-align: center; }
.spinner {
  width: 40px; height: 40px; margin: 0 auto 20px;
  border: 4px solid #e2e8f0; border-top-color: #0d9488;
  border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
h1 { font-size: 18px; font-weight: 600; margin-bottom: 6px; }
p { font-size: 13px; color: #64748b; }
#error { display: none; margin-top: 16px; padding: 12px 16px; background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; color: #991b1b; font-size: 13px; }
#error.show { display: block; }
</style>
</head>
<body>
<div class="container">
  <svg width="140" height="36" viewBox="0 0 200 50" style="margin:0 auto 16px">
    <text x="100" y="32" font-family="Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif" font-size="22" font-weight="700" fill="#1e293b" text-anchor="middle">Clinic Manager</text>
  </svg>
  <div class="spinner" id="spinner"></div>
  <p id="status">Loading application…</p>
  <div id="error"></div>
</div>
</body>
</html>`;
}

app.whenReady().then(async () => {
  const loadingHTML = loadingPageHTML();
  const loadingDataURL = `data:text/html;charset=utf-8,${encodeURIComponent(loadingHTML)}`;

  Menu.setApplicationMenu(null);

  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    autoHideMenuBar: true,
    show: false,
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  });

  mainWindow.loadURL(loadingDataURL);
  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.on('closed', () => { mainWindow = null; });

  cleanupOrphans();

  const port = await getFreePort();
  const isDev = !app.isPackaged;
  const ext = process.platform === 'win32' ? '.exe' : '';

  let backendPath;
  let args;
  let cwd;

  if (isDev) {
    const exePath = path.join(__dirname, 'dist', `clinic-backend${ext}`);
    if (fs.existsSync(exePath)) {
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
    args = ['runserver', `127.0.0.1:${port}`, '--noreload'];
  }

  console.log(`[electron] Spawning: ${backendPath} ${args.join(' ')}`);

  backendProcess = spawn(backendPath, args, { cwd, stdio: 'pipe' });

  backendProcess.stdout.on('data', (d) => console.log(`[backend] ${d}`));
  backendProcess.stderr.on('data', (d) => console.error(`[backend] ${d}`));

  function showError(msg) {
    try {
      mainWindow.webContents.executeJavaScript(`
        document.getElementById('spinner').style.display = 'none';
        document.getElementById('status').textContent = 'Failed to start';
        var e = document.getElementById('error');
        e.textContent = ${JSON.stringify(msg)};
        e.className = 'show';
      `);
    } catch (_) {}
  }

  try {
    await Promise.race([
      waitForServer(port),
      new Promise((_, rej) => {
        backendProcess.on('exit', (code) => rej(new Error(`Backend exited with code ${code}`)));
      }),
    ]);
  } catch (err) {
    console.error('Failed to start backend:', err);
    showError(err.message);
    return;
  }

  mainWindow.loadURL(`http://127.0.0.1:${port}/`);
});

app.on('before-quit', killBackend);
app.on('will-quit', killBackend);
process.on('exit', killBackend);
