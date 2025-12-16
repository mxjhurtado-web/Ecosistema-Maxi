# -*- mode: python ; coding: utf-8 -*-
# HADES Lite 2.2 - PyInstaller Spec File
# Generado para crear ejecutable con imágenes y recursos embebidos
# Actualizado: Incluye Keycloak SSO y Splash Screen

block_cipher = None

# Definir los datos adicionales (imágenes y recursos)
added_files = [
    ('flama2.png', '.'),           # Imagen de flama para animación
    ('Logo_Hades.png', '.'),       # Logo principal de HADES
    ('Hades_ico.ico', '.'),        # Ícono de la aplicación
    ('keycloak_auth.py', '.'),     # Módulo de autenticación Keycloak
    ('keycloak_config.py', '.'),   # Configuración de Keycloak
]

a = Analysis(
    ['hadeslite_2.2.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        # Google AI / Gemini
        'google.generativeai',
        'google.oauth2',
        'google.oauth2.service_account',
        'google.auth',
        'google.auth.transport',
        'google.auth.transport.requests',
        'googleapiclient',
        'googleapiclient.discovery',
        'googleapiclient.http',
        
        # Keycloak y autenticación
        'keycloak_auth',
        'keycloak_config',
        'http.server',
        'http.client',
        'urllib',
        'urllib.parse',
        'urllib.request',
        'webbrowser',
        
        # PIL / Pillow (imágenes)
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageOps',
        'PIL.ImageGrab',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        
        # Tkinter (GUI)
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.simpledialog',
        'tkinterdnd2',
        
        # Procesamiento de datos
        'pandas',
        'numpy',
        
        # HTTP y JSON
        'requests',
        'json',
        'base64',
        'io',
        
        # Sistema y utilidades
        'pathlib',
        'datetime',
        'time',
        're',
        'os',
        'sys',
        'tempfile',
        'unicodedata',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Excluir librerías no necesarias para reducir tamaño
        'matplotlib',
        'scipy',
        'numpy.testing',
        'pytest',
        'IPython',
        'jupyter',
        'notebook',
        'sphinx',
        # 'setuptools',  # Comentado - necesario para PyInstaller
        # 'distutils',   # Comentado - necesario para PyInstaller
        'pydoc',
        'doctest',
        'argparse',
        'pdb',
        'unittest',
        'test',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HADES_Lite_2.2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,              # Sin consola (aplicación GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='Hades_ico.ico',       # Ícono del ejecutable
)
