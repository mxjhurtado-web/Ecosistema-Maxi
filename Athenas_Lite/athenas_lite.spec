# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for ATHENAS Lite Refactored
Includes: Keycloak auth, multi-key management, rubrics, all dependencies
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all submodules from athenas_lite package
athenas_hiddenimports = collect_submodules('athenas_lite')

# Additional hidden imports
additional_imports = [
    # Google APIs
    'google.generativeai',
    'google.generativeai.types',
    'google.oauth2',
    'google.oauth2.service_account',
    'googleapiclient',
    'googleapiclient.discovery',
    'googleapiclient.http',
    
    # Keycloak & Auth
    'requests',
    'urllib3',
    'http.server',
    'webbrowser',
    'threading',
    
    # Data processing
    'pandas',
    'numpy',
    'json',
    'base64',
    'datetime',
    
    # Environment
    'dotenv',
    'python-dotenv',
    
    # UI
    'tkinter',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.ttk',
    'tkinter.font',
    'tkinter.scrolledtext',  # For TxtViewer
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    
    # Audio processing
    'mutagen',
    'soundfile',
    'pygame',  # For audio playback
    'pygame.mixer',
    
    # PDF generation
    'reportlab',
    'reportlab.lib',
    'reportlab.lib.pagesizes',
    'reportlab.lib.styles',
    'reportlab.lib.units',
    'reportlab.lib.colors',
    'reportlab.lib.enums',
    'reportlab.platypus',
    
    # Utilities
    'logging',
    'pathlib',
    'unicodedata',
    're',
]

a = Analysis(
    ['athenas_lite/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Logo/Icon
        ('athenas2.png', '.'),
        ('Athenas.ico', '.'),
        ('maxisend_logo.png', '.'),  # Maxi logo for PDF export
        
        # Rubricas folder (CRITICAL - contains department JSON files)
        ('rubricas', 'rubricas'),
        
        # Config folder structure (for api_keys.json template)
        ('athenas_lite/config', 'athenas_lite/config'),
        
        # .env.example for reference
        ('athenas_lite/.env.example', 'athenas_lite'),
    ],
    hiddenimports=athenas_hiddenimports + additional_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pytest',
        'setuptools',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Athenas_Lite_v4',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='Athenas.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Athenas_Lite_v4',
)
