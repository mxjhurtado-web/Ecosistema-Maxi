# Oportunidades de Mejora - MaxiBot V4.6.1

Este documento identifica oportunidades de mejora en la base de código de MaxiBot, organizadas por categorías y priorizadas por impacto en mantenibilidad, escalabilidad y calidad del código.

---

## 📋 Tabla de Contenidos

1. [Arquitectura y Estructura](#1-arquitectura-y-estructura)
2. [Gestión de Configuración y Secretos](#2-gestión-de-configuración-y-secretos)
3. [Manejo de Errores y Logging](#3-manejo-de-errores-y-logging)

---

## 1. Arquitectura y Estructura

### 🔴 Prioridad Alta: Modularización del Archivo Principal

**Situación Actual:**
- `MaxiBot_V4.6.1_mcp.py` tiene 1610 líneas con ~70 funciones/clases
- Mezcla responsabilidades: UI, lógica de negocio, parsers, integraciones con Google, Gemini, etc.
- Dificulta mantenimiento, testing y colaboración en equipo

**Mejora Propuesta:**
Dividir en módulos especializados:

```
maxibot/
├── __init__.py
├── config/
│   ├── __init__.py
│   ├── settings.py          # Configuración centralizada
│   └── constants.py          # Constantes globales
├── auth/
│   ├── __init__.py
│   ├── keycloak.py          # keycloak_auth.py actual
│   └── email_verifier.py    # verificar_correo_online()
├── ui/
│   ├── __init__.py
│   ├── components.py        # Widgets reutilizables (bubbles, chips, etc.)
│   ├── screens.py           # Pantallas (chat, bienvenida, alias, etc.)
│   └── styles.py            # COLORS, FONT
├── services/
│   ├── __init__.py
│   ├── google_sheets.py     # sheets_service(), sheets_get_rows()
│   ├── google_drive.py      # drive_service(), _drive_list_children_recursive()
│   ├── gemini.py            # _post_gemini(), buscar_con_gemini()
│   └── avisos.py            # _avisos_poller(), get_avisos_historial()
├── parsers/
│   ├── __init__.py
│   ├── pdf_parser.py        # _parse_pdf()
│   ├── docx_parser.py       # _parse_docx()
│   ├── xlsx_parser.py       # _parse_xlsx()
│   └── pbix_parser.py       # _parse_pbix_basic()
├── core/
│   ├── __init__.py
│   ├── bot.py               # MaxiBotCore
│   ├── memory.py            # ConversationMemory
│   ├── tools.py             # KBTool, DocsTool, MCPTool
│   └── session.py           # export_sesion_to_drive()
└── main.py                  # Punto de entrada, orquestación
```

**Beneficios:**
- ✅ Separación de responsabilidades (SRP - Single Responsibility Principle)
- ✅ Facilita testing unitario de cada módulo
- ✅ Múltiples desarrolladores pueden trabajar sin conflictos
- ✅ Reutilización de código entre componentes
- ✅ Fácil navegación y localización de funcionalidades

**Esfuerzo Estimado:** 3-5 días

---

### 🟡 Prioridad Media: Patrón de Diseño para UI

**Situación Actual:**
- Funciones UI (mostrar_chat, mostrar_alias, mostrar_verificacion) manipulan widgets globales directamente
- Variables globales (`app`, `chat_area`, `entry`, etc.) hacen el código difícil de testear

**Mejora Propuesta:**
Implementar patrón MVP (Model-View-Presenter) o similar:

```python
# ui/screens/chat_screen.py
class ChatScreen:
    """Pantalla de chat con presenter separado"""

    def __init__(self, root, presenter):
        self.root = root
        self.presenter = presenter
        self._build_ui()

    def _build_ui(self):
        """Construye widgets sin lógica de negocio"""
        self.frame = tk.Frame(self.root)
        self.chat_area = ScrolledText(...)
        self.entry = tk.Entry(...)
        # ...

    def add_message(self, who: str, text: str, is_user: bool):
        """Método público para agregar mensaje"""
        bubble = create_bubble(self.chat_area, text, is_user)
        # ...

    def clear(self):
        """Limpia la pantalla"""
        for widget in self.frame.winfo_children():
            widget.destroy()

# core/presenters/chat_presenter.py
class ChatPresenter:
    """Lógica de negocio para chat"""

    def __init__(self, bot_core: MaxiBotCore, view: ChatScreen):
        self.bot = bot_core
        self.view = view

    def handle_send_message(self, message: str):
        """Procesa envío de mensaje"""
        if not message.strip():
            return

        self.view.add_message("user", message, is_user=True)
        response = self.bot.responder(message)
        self.view.add_message("bot", response, is_user=False)
```

**Beneficios:**
- ✅ Separación UI / Lógica de negocio
- ✅ Testing más fácil (mock del view)
- ✅ Reutilización de lógica entre diferentes UIs (ej: CLI, Web)

**Esfuerzo Estimado:** 2-3 días

---

## 2. Gestión de Configuración y Secretos

### 🔴 Prioridad Alta: Secretos Hardcoded

**Situación Actual:**
```python
# keycloak_config.py línea 26
CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "mOLonfMkGYnhq3M4CSnzY4p7fFakNciu")

# MaxiBot_V4.6.1_mcp.py línea 71
SA_JSON_B64 = os.environ.get("ATHENAS_SA_JSON_B64", "<valor-largo-hardcoded>")

# MaxiBot_V4.6.1_mcp.py línea 90
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyDmW4Xh0J6v65oYKXMD1u2iiyvUeJrOnuo"
```

**Problemas:**
- 🔴 **Riesgo de seguridad**: Secretos expuestos en código fuente
- 🔴 **Git history**: Aunque se eliminen, quedan en el historial
- 🔴 **Rotación difícil**: Cambiar secretos requiere modificar código

**Mejora Propuesta:**

1. **Usar archivo `.env` NO versionado:**

```bash
# .env (agregar a .gitignore)
KEYCLOAK_CLIENT_SECRET=mOLonfMkGYnhq3M4CSnzY4p7fFakNciu
ATHENAS_SA_JSON_B64=ewogICJ0eXBlIjogInNl...
GEMINI_API_KEY=AIzaSyDmW4Xh0J6v65oYKXMD1u2iiyvUeJrOnuo
```

2. **Usar python-dotenv para cargar:**

```python
# config/settings.py
from dotenv import load_dotenv
import os

load_dotenv()  # Carga .env automáticamente

# Validar que existan variables críticas
REQUIRED_VARS = [
    "KEYCLOAK_CLIENT_SECRET",
    "ATHENAS_SA_JSON_B64",
    "GEMINI_API_KEY"
]

missing = [var for var in REQUIRED_VARS if not os.getenv(var)]
if missing:
    raise RuntimeError(f"Variables de entorno faltantes: {', '.join(missing)}")

# Exportar configuración
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET")
SA_JSON_B64 = os.getenv("ATHENAS_SA_JSON_B64")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
```

3. **Proveer `.env.example` para el equipo:**

```bash
# .env.example (SÍ se versiona)
KEYCLOAK_CLIENT_SECRET=tu-client-secret-aqui
ATHENAS_SA_JSON_B64=base64-del-service-account
GEMINI_API_KEY=tu-api-key-de-gemini
```

**Beneficios:**
- ✅ Secretos fuera del código fuente
- ✅ Fácil rotación sin cambios de código
- ✅ Diferentes valores por entorno (dev, staging, prod)
- ✅ Onboarding más fácil con `.env.example`

**Esfuerzo Estimado:** 2-3 horas

---

### 🟡 Prioridad Media: Configuración Centralizada

**Situación Actual:**
- Constantes dispersas en el archivo principal (líneas 68-100)
- IDs de Google Sheets/Drive hardcoded
- Configuración mezclada con código

**Mejora Propuesta:**

```python
# config/settings.py
from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class GoogleConfig:
    """Configuración de servicios Google"""
    kb_sheet_id: str
    auth_sheet_id: str
    sessions_folder_id: str
    newresp_folder_id: str
    docs_folder_id: str
    avisos_sheet_id: str
    avisos_tab_name: str = "Avisos"

    @classmethod
    def from_env(cls):
        return cls(
            kb_sheet_id=os.getenv("GS_KB_SHEET_ID", "1wrtj7SZ6wB9h1yd_9h613DYNPGjI69_Zj1gLigiUHtE"),
            auth_sheet_id=os.getenv("GS_AUTH_SHEET_ID", "1Ev3i55QTW1TJQ_KQP01TxEiLmZJVkwVFJ1cn_p9Vlr0"),
            # ...
        )

@dataclass
class AppConfig:
    """Configuración general de la app"""
    version: str = "V4.6.1"
    ask_before_web: bool = True
    avisos_poll_sec: int = 60

    google: GoogleConfig
    keycloak: 'KeycloakConfig'

    @classmethod
    def load(cls):
        return cls(
            google=GoogleConfig.from_env(),
            keycloak=KeycloakConfig.from_env(),
        )

# Uso:
config = AppConfig.load()
print(config.google.kb_sheet_id)
```

**Beneficios:**
- ✅ Configuración centralizada y tipada
- ✅ Validación en un solo lugar
- ✅ Fácil de testear con configs mock
- ✅ Documentación automática con dataclasses

**Esfuerzo Estimado:** 1 día

---

## 3. Manejo de Errores y Logging

### 🔴 Prioridad Alta: Reemplazar `print()` por Logging Estructurado

**Situación Actual:**
```python
# keycloak_auth.py
print("Iniciando servidor de callback...")
print(f"Abriendo navegador para autenticación...")
print("Esperando autenticación en Keycloak...")
print("✅ Autenticación exitosa: {email}")

# MaxiBot_V4.6.1_mcp.py
print("🔐 Iniciando flujo SSO...")
print(f"📡 Resultado: success={success}, message={message}")
```

**Problemas:**
- ❌ No se pueden filtrar por nivel (DEBUG, INFO, ERROR)
- ❌ Difícil debugging en producción
- ❌ No hay timestamps ni contexto
- ❌ No se pueden redirigir a archivos

**Mejora Propuesta:**

```python
# config/logging_config.py
import logging
import sys
from pathlib import Path

def setup_logging(level: str = "INFO", log_file: str = None):
    """Configura logging estructurado"""

    # Formato con timestamp, nivel, módulo y mensaje
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    handlers = [console_handler]

    # Handler para archivo (opcional)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # Configurar root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=handlers
    )

    # Silenciar logs verbosos de librerías externas
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

# auth/keycloak.py
import logging

logger = logging.getLogger(__name__)

class KeycloakAuth:
    def authenticate(self):
        logger.info("Iniciando flujo de autenticación SSO")
        logger.debug(f"Auth URL: {auth_url}")

        try:
            success, message = self.exchange_code_for_tokens(code)
            if not success:
                logger.error(f"Error obteniendo tokens: {message}")
                return False, message

            logger.info(f"Autenticación exitosa: {email}")
            return True, "OK"
        except Exception as e:
            logger.exception("Excepción durante autenticación")
            return False, str(e)
```

**Uso:**
```python
# main.py
from config.logging_config import setup_logging

setup_logging(
    level="DEBUG" if os.getenv("DEBUG") else "INFO",
    log_file="logs/maxibot.log"
)
```

**Beneficios:**
- ✅ Filtrado por nivel (DEBUG en desarrollo, INFO en producción)
- ✅ Timestamps automáticos
- ✅ Logs persistentes en archivos
- ✅ Stack traces completos con `logger.exception()`
- ✅ Facilita troubleshooting en producción

**Esfuerzo Estimado:** 1-2 días

---

### 🟡 Prioridad Media: Manejo de Excepciones Específicas

**Situación Actual:**
```python
# Catch genéricos en múltiples lugares
try:
    # operación
except Exception as e:
    print(f"Error: {e}")
```

**Problemas:**
- Captura excepciones que no deberían manejarse (ej: KeyboardInterrupt)
- Dificulta identificar causa raíz
- Pérdida de contexto

**Mejora Propuesta:**

```python
# services/google_sheets.py
class SheetsError(Exception):
    """Error base para operaciones de Sheets"""
    pass

class SheetNotFoundError(SheetsError):
    """Sheet no encontrado"""
    pass

class InsufficientPermissionsError(SheetsError):
    """Permisos insuficientes"""
    pass

def sheets_get_rows(sheet_id: str, title: str) -> List[List[str]]:
    """Obtiene filas de una sheet con manejo de errores específico"""
    try:
        svc = sheets_service()
        result = svc.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=title
        ).execute()
        return result.get('values', [])

    except HttpError as e:
        if e.resp.status == 404:
            raise SheetNotFoundError(f"Sheet '{title}' no encontrada en {sheet_id}")
        elif e.resp.status == 403:
            raise InsufficientPermissionsError(f"Sin permisos para acceder a {sheet_id}")
        else:
            raise SheetsError(f"Error HTTP {e.resp.status}: {e}")

    except Exception as e:
        logger.exception("Error inesperado obteniendo rows")
        raise SheetsError(f"Error obteniendo datos: {e}") from e

# En código cliente:
try:
    rows = sheets_get_rows(sheet_id, "Sheet1")
except SheetNotFoundError:
    logger.warning("Sheet no existe, usando valores por defecto")
    rows = []
except InsufficientPermissionsError:
    logger.error("Verificar permisos del Service Account")
    raise
except SheetsError as e:
    logger.error(f"Error de Sheets: {e}")
    raise
```

**Beneficios:**
- ✅ Manejo diferenciado por tipo de error
- ✅ Mensajes de error más descriptivos
- ✅ Facilita debugging
- ✅ Permite retry selectivo

**Esfuerzo Estimado:** 2-3 días