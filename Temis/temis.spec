# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller spec file for TEMIS Desktop Application
Builds a standalone Windows executable with all dependencies
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get the project root directory
block_cipher = None
project_root = os.path.abspath('.')

# Collect all hidden imports
hiddenimports = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    'tkinter.scrolledtext',
    'sqlalchemy',
    'sqlalchemy.ext.declarative',
    'sqlalchemy.orm',
    'requests',
    'google.auth',
    'google.oauth2',
    'googleapiclient',
    'googleapiclient.discovery',
    'googleapiclient.http',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'pydantic',
    'fastapi',
    'uvicorn',
    'python-docx',
    'PyPDF2',
    'openpyxl',
    'schedule',
    'desktop.core',
    'desktop.ui',
    'backend.models',
    'backend.services',
    'backend.routers',
]

# Collect all submodules
hiddenimports += collect_submodules('desktop')
hiddenimports += collect_submodules('backend')
hiddenimports += collect_submodules('config')

# Data files to include
datas = [
    ('.env.example', '.'),
    ('README.md', '.'),
    ('requirements.txt', '.'),
]

# Add docs folder if exists
if os.path.exists('docs'):
    datas.append(('docs', 'docs'))

# Analysis
a = Analysis(
    ['desktop/main.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'pytest',
        'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TEMIS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one: 'path/to/icon.ico'
    version_file=None,
)

# Optional: Create a single folder distribution (uncomment if needed)
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='TEMIS',
# )
