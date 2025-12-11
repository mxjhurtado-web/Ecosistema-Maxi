# MaxiBot.spec
# Actualizado para MaxiBot_V4.6.2_DevOpsMCP.py

block_cipher = None

import certifi  # ✅ Para incluir certificados SSL
from PyInstaller.utils.hooks import copy_metadata
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

datas_meta = []
try:
    datas_meta += copy_metadata('google-api-python-client')
except Exception:
    pass

a = Analysis(
    ['MaxiBot_V4.6.2_DevOpsMCP.py'],  # ✅ Actualizado al nuevo archivo
    pathex=['.'],
    binaries=[],
    datas=[
        # Archivos que tu app usa en tiempo de ejecución:
        ('Logo_MaxiBot.png', '.'),

        # Opcional: incluir también el propio .ico junto al exe
        ('MaxiBot.ico', '.'),

        # ✅ Certificados SSL para requests/HTTPS (CRÍTICO para DevOps MCP)
        (certifi.where(), 'certifi'),

        # Si quieres cargar un .env desde el exe, descomenta:
        # ('.env', '.'),
    ] + datas_meta,
    hiddenimports=[
        # Google APIs
        'googleapiclient',
        'googleapiclient.discovery',
        'googleapiclient.http',
        'google.oauth2.service_account',
        
        # Document parsers
        'PyPDF2',
        'docx',
        'openpyxl',
        
        # Image handling
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        
        # MCP
        'mcp',
        
        # ✅ Módulos nuevos de MaxiBot V4.6.2
        'devops_mcp',
        'weather_direct',
        'news_direct',
        'operaciones_tab',
        'registro',
        'registro_adapter',
        'keycloak_auth',
        'keycloak_config',
        'api_key_manager',  # ✅ Sistema de rotación de API Keys
        
        # Dependencias adicionales
        'pandas',
        'requests',
        
        # ✅ SSL/HTTPS support (CRÍTICO para DevOps MCP)
        'certifi',
        'urllib3',
        'urllib3.util',
        'urllib3.util.ssl_',
        'urllib3.util.retry',
        'urllib3.contrib',
        'urllib3.contrib.pyopenssl',
        'charset_normalizer',
        'charset_normalizer.md',
        
        # ✅ Requests library dependencies
        'requests.adapters',
        'requests.auth',
        'requests.models',
        'requests.sessions',
        'requests.packages',
        'requests.packages.urllib3',
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
