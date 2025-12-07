# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['athenas_lite/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include internal assets (like logo for UI) inside the bundle
        ('athenas_lite/Athenas2.png', 'athenas_lite'),
        # Note: 'rubricas' folder is treated as external config by code design
        # so we don't bundle it into datas unless we want a readonly default.
        # User requested "junto y dentro", so code now looks next to EXE.
    ],
    hiddenimports=[
        'mutagen',
        'soundfile',
        'numpy',
        'pandas',
        'google.generativeai',
        'dotenv',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.ttk'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='Athenas_Lite_Refactored',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # Set to True if you want to see terminal output for debug
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='athenas_lite/Athenas.ico'
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Athenas_Lite_Refactored',
)
