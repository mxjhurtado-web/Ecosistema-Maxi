# 🗺️ Manual de Arquitectura y Mapa de Código: Backend Middleware ORBIT v4.7
**Maxitransfers | Ecosistema Maxi**  
*Documento de Traspaso Técnico para Desarrolladores Backend*

---

## 📌 1. Visión General de la Arquitectura

El **Middleware ORBIT** es la capa backend en **FastAPI (Python 3.13)** que orquesta la inteligencia conversacional, las reglas de negocio (RNE.01 - RNE.59), la validación de transacciones en base de datos PostgreSQL (Supabase), la gestión de estado conversacional en memoria (Redis) y las notificaciones a los 9 canales dedicados de **Google Chat**.

```mermaid
flowchart TD
    WA["📱 WhatsApp / Respond.io"] <-->|HTTP POST /agent/interact| API["🚀 FastAPI Backend (ORBIT)"]
    
    subgraph Almacenamiento y Estado
        API <-->|Sesiones y Caché| REDIS["🔴 Redis Cache"]
        API <-->|Consultas de Envíos| SUPA["🐘 Supabase PostgreSQL"]
        API <-->|Reglas y Scripts| GSHEETS["📊 Google Sheets API"]
    end
    
    subgraph Notificaciones Departamentales
        API -->|Notificar Alertas| GCHAT["💬 Google Chat (9 Espacios Dedicated)"]
    end
```

---

## 📁 2. Estructura de Archivos y Mapa de Responsabilidades

Todo el backend de ORBIT habita dentro del directorio `respondio-middleware/api/`.

```
respondio-middleware/
├── api/
│   ├── main.py                   # 🧠 NÚCLEO PRINCIPAL: Routers FastAPI, FSM de estado, Enrutador de Departamentos, Reglas de Negocio
│   ├── config.py                 # ⚙️ CONFIGURACIÓN: Variables de entorno, Pydantic Settings, IDs de Google Sheets y Espacios de Google Chat
│   ├── google_chat_service.py    # 💬 GOOGLE CHAT: Servicio de autenticación con Service Account (SA) y envío de notificaciones HTTP/JSON
│   ├── shared_logic.py           # 🛠️ LÓGICA COMPARTIDA: Conexión a PostgreSQL (Supabase), cliente Redis, traducción e idioma dinámico (LNG.02)
│   ├── admin_api.py              # 🔧 ADMIN ENDPOINTS: Webhooks directos de notificación, endpoints administrativos y callbacks
│   └── telemetry.py              # 📈 TELEMETRÍA: Registro de métricas y eventos en Google Sheets de Telemetría
├── tests/
│   ├── test_api.py               # 🧪 SUITE DE PRUEBAS: 61 pruebas unitarias e integrales (Pytest)
│   └── test_scripts_rules.py     # 🧪 PRUEBAS DE REGLAS: Validación de lectura de Google Sheets
├── requirements.txt              # 📦 Dependencias del proyecto (FastAPI, Uvicorn, Redis, psycopg2, httpx, etc.)
└── MAPA_ARQUITECTURA_ORBIT.md    # 🗺️ Este documento
```

---

## 🔍 3. Guía de Archivos: ¿Dónde hacer cada cambio?

### 🎯 **A. Si necesitas modificar o agregar un Enrutamiento Departamental (Google Chat / Equipos)**
* **Archivo principal:** `api/main.py`
* **Sección exacta:** Buscar el bloque `# ENRUTADOR INTELIGENTE DE DEPARTAMENTOS`.
* **Cómo funciona:** El backend evalúa palabras clave prioritarias. Si detecta la intención, dispara la alerta a Google Chat, aplica el script correspondiente (`SC.013`, etc.) y devuelve el parámetro `derivacion` hacia Respond.io (`AgentOversight`, `Capacitacion`, `Cumplimiento`, `Cobranza`, `Cheques`, `AgenteComunicador`, `VentasInternas`, `DerivacionFraudes`, `DerivacionBSA`).

### 📜 **B. Si necesitas ajustar los Scripts de Cumplimiento o Reglas de Negocio**
* **Google Sheets en Vivo (Leídos automáticamente con caché de Redis):**
  * **Reglas de Negocio (RNE 01-59):** `1eFm3L_ALVr78wTDBB2bsg7Wq6DT9ZoGzIX9tKLN9nGw`
  * **Scripts Oficiales (SC.001 - SC.036):** `18VE3tdVt4E-eNrf0dD4zlk1aLV2nfv9_ncdUvLPaNic`
* **Archivo de código:** `api/main.py`
* **Funciones:** `get_compliance_scripts()` y `get_business_rules()`.

### 🖐️ **C. Si necesitas modificar el Script de Bienvenida Obligatorio (`CU.A1`) o Idioma Dinámico (`LNG.02`)**
* **Garantía de Bienvenida (Turno 1):** `api/main.py` en la función decorada `@app.post("/api/v1/agent/interact")`. Aquí se verifica `session:welcome_sent:{contact_id}` en Redis. Si es Turno 1, antepone `CU.A1` sin excepción.
* **Idioma Dinámico (`LNG.02`):** `api/shared_logic.py` en la función `translate_script_if_needed()`. Restablece automáticamente a español si detecta texto en español.

### 💾 **D. Si necesitas modificar la consulta de Envíos en Base de Datos (Supabase)**
* **Archivo:** `api/main.py`
* **Funciones clave:** `check_transaction_status_inner()`, `check_bill_status_inner()`, `check_topup_status_inner()`.
* **Conexión a BD:** `api/shared_logic.py` -> `get_db_connection()`.
* **Tabla principal:** `"Base_completa"` en PostgreSQL Supabase.

---

## 🔑 4. Tabla de Espacios Oficiales de Google Chat

| Departamento | Variable en `api/config.py` | Space ID Canónico en GCP |
| :--- | :--- | :--- |
| **Agent Oversight** | Hardcoded / Config | `spaces/AAQAJiVCDAU` |
| **Capacitación** | Hardcoded / Config | `spaces/AAQAMKgsazw` |
| **Cumplimiento (AML/KYC)** | Hardcoded / Config | `spaces/AAQAbvCUAko` |
| **Cobranza** | Hardcoded / Config | `spaces/AAQAcEu8NTc` |
| **Cheques** | `GOOGLE_CHATS_CHEQUES_SPACE` | `spaces/AAQAGZ_m434` |
| **Soporte Técnico** | `GOOGLE_CHATS_SOPORTE_SPACE` | `spaces/AAQAQhx5RTM` |
| **Ventas Internas** | Hardcoded / Config | `spaces/AAQAUghCztE` |
| **Prevención de Fraudes**| `GOOGLE_CHATS_FRAUDES_SPACE` | `spaces/AAQAQM9pDpg` |
| **Monitoreo BSA** | `GOOGLE_CHATS_BSA_SPACE` | `spaces/AAQA3WL2JIk` |

---

## 🔑 5. Variables de Entorno Clave (`.env`)

```ini
# Secreto del Webhook para autenticación de llamadas HTTP desde Respond.io
WEBHOOK_SECRET=maxi-secret-2025

# Base de Datos PostgreSQL Supabase
SUPABASE_URI=postgresql://postgres:PruebaBoot2025.*@db.tzlomvpugmrpdfatscxe.supabase.co:5432/postgres

# Redis Cache URL (en Render o local)
REDIS_URL=redis://red-cu1...:6379

# Credenciales de Service Account de Google Chat (Base64 del JSON de GCP)
GOOGLE_CHATS_SA_BASE64=<base64_string>
```

---

## 🛠️ 6. Comandos Utilitarios para el Desarrollador (Workflow Tradicional)

### 1. **Ejecutar el servidor localmente:**
```bash
cd Middleware/respondio-middleware
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. **Ejecutar la suite completa de 61 pruebas unitarias:**
```bash
pytest tests/
```

### 3. **Validar sintaxis de un archivo antes de commit:**
```bash
python -m py_compile api/main.py
```

### 4. **Despliegue a Producción:**
El despliegue es **automático** al hacer push a la rama principal de GitHub:
```bash
git add .
git commit -m "feat/fix: descripcion del cambio"
git push origin main
```
* **URL de Producción (Render):** `https://orbit-api-ewov.onrender.com`
* **Swagger UI / Documentación Interactiva:** `https://orbit-api-ewov.onrender.com/docs`
