# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Obtener la ruta base del proyecto
project_dir = os.path.abspath('.')

# Recolectar archivos de datos de tkinterdnd2
datas = collect_data_files('tkinterdnd2')

# Agregar archivos estáticos del proyecto
datas += [
    ('Logo_Hades.png', '.'), 
    ('flama2.png', '.'),
    ('Hades_ico.ico', '.')
]

# Definir archivos del proyecto que deben incluirse
added_files = [
    'i18n_strings.py',
    'keycloak_auth.py',
    'keycloak_config.py',
    'ocr_translation.py',
    'policy_templates.py',
    'translation_utils.py'
]

a = Analysis(
    ['hadeslite_2.2_semaforo.py'],
    pathex=[project_dir],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'google.generativeai',
        'requests',
        'PIL.Image',
        'PIL.ImageTk',
        'pandas',
        'tkinterdnd2',
        'jwt',
        'google.auth',
        'google_auth_oauthlib',
        'googleapiclient.discovery'
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Hades_Ultimate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
