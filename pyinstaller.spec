# -*- mode: python ; coding: utf-8 -*-
import subprocess
import sys
import warnings
from pathlib import Path

block_cipher = None

PROJ = Path.cwd()

# Validate required dirs
for d in ['conf', 'core', 'templates']:
    if not (PROJ / d).is_dir():
        warnings.warn(f'Missing directory: {PROJ / d}')

# Migrate + collectstatic before bundling
python = sys.executable
manage = str(PROJ / 'manage.py')

result = subprocess.run([python, manage, 'migrate', '--noinput'], cwd=str(PROJ))
if result.returncode != 0:
    raise SystemExit('migrate failed — aborting build')

result = subprocess.run([python, manage, 'collectstatic', '--noinput'], cwd=str(PROJ))
if result.returncode != 0:
    raise SystemExit('collectstatic failed — aborting build')

db = PROJ / 'db.sqlite3'
if not db.exists():
    raise SystemExit(
        f'ERROR: {db} not found.\n'
        f'Run "python manage.py migrate && python manage.py createsuperuser" first.'
    )

a = Analysis(
    ['manage.py'],
    pathex=[str(PROJ)],
    binaries=[],
    datas=[
        (str(PROJ / 'conf'), 'conf'),
        (str(PROJ / 'core'), 'core'),
        (str(PROJ / 'templates'), 'templates'),
        (str(PROJ / 'staticfiles'), 'staticfiles'),
        (str(db), '.'),
    ],
    hiddenimports=[
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'django.template.loaders.filesystem',
        'django.template.loaders.app_directories',
        'core',
        'core.migrations',
        'core.middleware',
        'template_partials',
        'template_partials.templatetags.partials',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'unittest',
        'test',
        'tkinter',
        'matplotlib',
        'PIL',
        'pandas',
        'numpy',
        'scipy',
        'werkzeug',
        'sphinx',
        'zmq',
        'jedi',
        'parso',
        'IPython',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='clinic-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
