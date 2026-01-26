# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_all

block_cipher = None

# Obtener la ruta base del proyecto
project_dir = os.path.abspath('.')

# Recolectar TODO de las librerías pesadas/críticas
datas = []
binaries = []
hiddenimports = [
    'google.generativeai',
    'requests',
    'PIL.Image',
    'PIL.ImageTk',
    'pandas',
    'tkinterdnd2',
    'jwt',
    'google.auth',
    'google_auth_oauthlib',
    'googleapiclient.discovery',
    'google.api_core',
    'google_auth_httplib2',
    'certifi',
    'httplib2'
]

# Librerías que suelen dar problemas en el empaquetado
for lib in ['tkinterdnd2', 'google.generativeai', 'pandas', 'google.api_core', 'googleapiclient', 'google_auth_httplib2']:
    tmp_ret = collect_all(lib)
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]

# Agregar archivos estáticos del proyecto manualmente
datas += [
    ('Logo_Hades.png', '.'), 
    ('flama2.png', '.'),
    ('Hades_ico.ico', '.')
]

a = Analysis(
    ['hadeslite_2.2_semaforo.py'],
    pathex=[project_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Hades_Ultimate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False, # DESACTIVADO para mayor compatibilidad y peso real
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='Hades_ico.ico',
)
