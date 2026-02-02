# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Lista de archivos adicionales (assets, etc.)
added_files = [
    ('Logo_MaxiBot.png', '.'), 
    ('MaxiBot.ico', '.'),
    ('.env.example', '.'), # Opcional: incluir ejemplo de env
]

a = Analysis(
    ['MaxiBot_V4.6.2_DevOpsMCP.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'PIL._tkinter_finder',
        'keycloak_auth',
        'keycloak_config',
        'devops_mcp',
        'api_key_manager',
        'operaciones_tab',
        'googleapiclient',
        'google.auth',
        'google.generativeai',
        # MCP y dependencias async
        'mcp',
        'mcp.client',
        'mcp.client.session',
        'mcp.client.stdio',
        'asyncio',
        'asyncio.tasks',
        'asyncio.taskgroups',
        'httpx',
        'httpx._client',
        'httpx._transports',
        'httpcore',
        'h11',
        'h2',
        # Otras dependencias
        'dotenv',
        'pandas',
        'openpyxl',
        'PyPDF2',
        'docx',
        'sqlite3',
        'json',
        're',
        'datetime',
        'threading',
        'queue',
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
    name='MaxiBot_V4.6.2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Cambiar a True si se desea ver la terminal de depuración
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='MaxiBot.ico'
)
