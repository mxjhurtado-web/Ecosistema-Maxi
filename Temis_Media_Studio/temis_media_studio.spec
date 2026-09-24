# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

datas = [
    ('resources/ffmpeg/ffmpeg.exe', 'resources/ffmpeg'),
    ('resources/models/base.pt', 'resources/models'),
    ('resources/models/medium.pt', 'resources/models'),
    ('resources/assets', 'resources/assets'),
    ('whisper', 'whisper'),
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'whisper',
        'docx',
        'google.generativeai',
        'PIL',
        'tkinter',
        'ttkthemes'
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
    name='TEMIS_Media_Studio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/assets/app_icon.ico' if os.path.exists('resources/assets/app_icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TEMIS_Media_Studio',
)
