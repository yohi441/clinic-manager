# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

block_cipher = None

# Collect static files before building
os.system(f'{sys.executable} manage.py collectstatic --noinput --clear')

# Paths relative to project root
PROJ = Path(os.path.abspath('.'))

a = Analysis(
    ['manage.py'],
    pathex=[str(PROJ)],
    binaries=[],
    datas=[
        (str(PROJ / 'conf'), 'conf'),
        (str(PROJ / 'core'), 'core'),
        (str(PROJ / 'templates'), 'templates'),
        (str(PROJ / 'staticfiles'), 'staticfiles'),
        (str(PROJ / 'db.sqlite3'), '.'),
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
