# MaxiBot.spec

block_cipher = None

from PyInstaller.utils.hooks import copy_metadata
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

datas_meta = []
try:
    datas_meta += copy_metadata('google-api-python-client')
except Exception:
    pass

a = Analysis(
    ['MaxiBot_V4.6.1_Keycloack.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Archivos que tu app usa en tiempo de ejecución:
        ('Logo_MaxiBot.png', '.'),

        # Opcional: incluir también el propio .ico junto al exe
        ('MaxiBot.ico', '.'),

        # Si quieres cargar un .env desde el exe, descomenta:
        # ('.env', '.'),
    ] + datas_meta,
    hiddenimports=[
        'googleapiclient',
        'googleapiclient.discovery',
        'googleapiclient.http',
        'google.oauth2.service_account',
        'PyPDF2',
        'docx',
        'openpyxl',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'mcp',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MaxiBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # sin consola negra
    icon='MaxiBot.ico',     # 👈 aquí usamos tu ícono
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MaxiBot',
)
