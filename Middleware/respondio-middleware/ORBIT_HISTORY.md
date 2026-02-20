# 🪐 ORBIT — Historia Técnica Completa del Proyecto

> **Documento de referencia** que detalla cada fase del desarrollo de **ORBIT** (`respondio-middleware`), el middleware de integración del Ecosistema Maxi. Incluye objetivos técnicos, archivos clave, tiempo estimado y logros por etapa.

---

## 🎯 ¿Qué es ORBIT?

**ORBIT** es el middleware de integración del **Ecosistema Maxi**. Su misión es conectar plataformas externas (como Respond.io) con servidores internos de MCP (Model Context Protocol), garantizando comunicación segura, resiliente, monitorizable y escalable.

**Stack tecnológico:**
- **Backend**: FastAPI (Python 3.11+)
- **Dashboard**: Streamlit
- **Persistencia**: Redis
- **Infraestructura**: Docker / Render / Streamlit Cloud
- **Autenticación**: Keycloak (OAuth2 / OIDC)

---

## 📅 Cronología Técnica de Fases

### 🔹 Fase 1 — Fundación del Middleware
**Estado:** ✅ Completada | **Tiempo estimado:** ~3 horas

**Objetivo:** Construir el núcleo del middleware: webhook seguro, cliente MCP con resiliencia y telemetría básica.

**Archivos principales:**
| Archivo | Descripción |
|---|---|
| `api/main.py` | FastAPI con endpoint `POST /webhook` |
| `api/mcp_client.py` | Cliente MCP con retry logic y circuit breaker |
| `api/models.py` | Modelos Pydantic para validación de datos |
| `api/telemetry.py` | Registro de métricas en Redis |
| `api/config_manager.py` | Gestión de configuración persistente en Redis |
| `infra/docker-compose.yml` | Stack completo: Redis + Mock MCP + API |

**Características de resiliencia implementadas:**
- 3 reintentos automáticos en fallos de MCP
- Circuit Breaker para prevenir fallos en cascada
- Caché configurable de respuestas
- Health checks en `/health` y `/ready`
- Validación de firma `X-Webhook-Secret` en cada request

---

### 🔹 Fase 2 — Dashboard Inicial (Streamlit)
**Estado:** ✅ Completada | **Tiempo estimado:** ~2 horas

**Objetivo:** Crear el dashboard de monitoreo básico con KPIs, historial de requests y visor de logs.

**Archivos principales:**
| Archivo | Descripción |
|---|---|
| `dashboard/app.py` | App principal de Streamlit con autenticación básica |
| `dashboard/pages/1_📊_kpis.py` | Métricas en tiempo real |
| `dashboard/pages/2_📜_history.py` | Historial de requests |
| `dashboard/pages/3_🔍_logs.py` | Visor de logs en vivo |
| `dashboard/pages/4_⚙️_config.py` | Configuración en caliente (MCP URL, cache, seguridad) |
| `dashboard/pages/5_🔧_maintenance.py` | Health checks y herramientas de mantenimiento |
| `dashboard/components/api_client.py` | Cliente HTTP para comunicarse con la API |

**Capacidades del dashboard:**
- Actualización de MCP URL, timeout y reintentos **sin reiniciar el servicio**
- Streaming de logs en tiempo real desde Redis
- Visualización de métricas de éxito, latencia y volumen

---

### 🔹 Fase 3 — Chat Interactivo y Arquitectura Multi-MCP
**Estado:** ✅ Completada | **Tiempo estimado:** ~2 horas

**Objetivo:** Añadir una interfaz de chat para pruebas en tiempo real y sentar las bases de la arquitectura Multi-MCP.

**Archivos creados:**
| Archivo | Descripción |
|---|---|
| `dashboard/pages/6_💬_chat.py` | Interfaz de chat con historial y metadatos (7.8 KB) |
| `api/mcp_router.py` | Sistema de ruteo inteligente (6.2 KB) |
| `docs/MULTI_MCP_SUPPORT.md` | Documentación de arquitectura futura |

**Capacidades del router:**
- Ruteo por palabras clave (keyword-based)
- Ruteo por canal (WhatsApp, Telegram, Messenger, Webchat)
- Ruteo por etiquetas (tag-based)
- Estrategia de fallback automático

**Chat features:** historial de mensajes, metadatos de respuesta (latencia, status, trace ID), simulación de canales, exportación de conversación.

---

### 🔹 Fase 4 — Dockerización y Despliegue en Render
**Estado:** ✅ Completada | **Tiempo estimado:** ~1.5 horas

**Objetivo:** Preparar ORBIT para despliegue en producción con Docker y Render.

**Archivos creados/actualizados:**
| Archivo | Descripción |
|---|---|
| `Dockerfile` | Imagen optimizada para producción |
| `infra/Dockerfile.api` | Dockerfile específico de la API |
| `infra/Dockerfile.dashboard` | Dockerfile específico del Dashboard |
| `infra/docker-compose.prod.yml` | Compose de producción |
| `render.yaml` | Configuración de servicios en Render |
| `Procfile` | Comando de inicio para Render |

**Resultado:** API desplegada en Render con URL pública. Dashboard preparado para Streamlit Cloud.

---

### 🔹 Fase 5 — Identidad de Marca y README
**Estado:** ✅ Completada | **Tiempo estimado:** ~1 hora

**Objetivo:** Profesionalizar el proyecto con identidad visual y documentación completa.

**Entregables:**
- Logo ORBIT (planeta con anillo, gradiente cian → azul `#00D9FF` → `#0066FF`)
- `README.md` completo con arquitectura, quickstart, configuración y guías de despliegue
- Guía de marca (`orbit_brand_guide.md`): colores, tipografía, uso del logo
- Guía de despliegue en Render (`render_deployment_guide.md`)

---

### 🔹 Fase 6 — Cloud-Ready (Soporte de Secrets)
**Estado:** ✅ Completada | **Tiempo estimado:** ~1 hora

**Objetivo:** Migrar credenciales de `.env` locales a **Secrets de Streamlit Cloud** para mayor seguridad.

**Archivos actualizados:**
| Archivo | Cambio |
|---|---|
| `dashboard/components/api_client.py` | Prioriza `st.secrets` sobre variables de entorno |
| `dashboard/components/auth.py` | Credenciales seguras desde Secrets |
| `dashboard/requirements.txt` | Verificación y actualización de dependencias |

**Resultado:** Guía de despliegue en Streamlit Cloud creada y push a GitHub exitoso.

---

### 🔹 Fase 7 — Optimización de Rendimiento
**Estado:** ✅ Completada | **Tiempo estimado:** ~1 hora

**Objetivo:** Mejorar la velocidad de respuesta del dashboard y reducir llamadas innecesarias a la API.

**Mejoras implementadas:**
- Caché de datos con `@st.cache_data` para reducir llamadas repetidas
- Paginación en el historial de requests
- Lazy loading de componentes pesados
- Reducción de tiempo de carga inicial del dashboard

---

### 🔹 Fase 8 — Integración con Gemini AI
**Estado:** ✅ Completada | **Tiempo estimado:** ~1.5 horas

**Objetivo:** Integrar Gemini como motor de IA para procesar las consultas que llegan desde Respond.io.

**Archivos actualizados:**
| Archivo | Cambio |
|---|---|
| `api/config.py` | Campo `GEMINI_API_KEY` en Settings |
| `api/mcp_client.py` | Soporte para enviar consultas a Gemini |
| `dashboard/pages/4_⚙️_config.py` | Pestaña "AI Integration" para gestionar la API Key |

---

### 🔹 Fase 9 — RBAC (Gestión de Usuarios y Roles)
**Estado:** ✅ Completada | **Tiempo estimado:** ~2 horas

**Objetivo:** Implementar control de acceso basado en roles (Admin y Supervisor).

**Archivos creados/modificados:**
| Archivo | Descripción |
|---|---|
| `api/models.py` | Modelos `User` y `Role` |
| `api/admin_api.py` | Endpoints CRUD de usuarios |
| `api/config_manager.py` | Persistencia de usuarios en Redis |
| `dashboard/components/auth.py` | Verificación de roles en el dashboard |

**Roles implementados:**
- **Admin**: Control total — configuración, usuarios, mantenimiento, auditoría.
- **Supervisor**: Acceso limitado — solo KPIs e Historial (solo lectura).

**Restricciones:** Máximo 3 usuarios por rol.

---

### 🔹 Fase 10 — Keycloak Service Account
**Estado:** ✅ Completada | **Tiempo estimado:** ~2 horas

**Objetivo:** Autenticación permanente y automatizada con el MCP productivo usando Keycloak.

**Archivos creados/modificados:**
| Archivo | Descripción |
|---|---|
| `api/auth.py` | `KeycloakAuthService` con flujo `client_credentials` |
| `api/mcp_client.py` | Obtiene y renueva tokens automáticamente |
| `dashboard/pages/4_⚙️_config.py` | Modo dual: Token Manual vs. Keycloak Service Account |

**Beneficios:**
- **Cero mantenimiento**: No hay que actualizar tokens manualmente.
- **Permanente**: La conexión no expira mientras el Client Secret sea válido.
- **Robusto**: Si el token caduca, ORBIT lo renueva en milisegundos.

---

### 🔹 Fase 11 — Analítica Avanzada y Exportación
**Estado:** ✅ Completada | **Tiempo estimado:** ~1.5 horas

**Objetivo:** Transformar el dashboard de visualización básica a plataforma de analítica profesional.

**Mejoras implementadas:**
| Funcionalidad | Detalle |
|---|---|
| Exportación CSV/JSON | Botón en KPIs y en Historial |
| Gráficos de Latencia | Average + P95 con Plotly (línea sólida + punteada) |
| Panel de Monitoreo Proactivo | Semáforos 🟢🟡🔴 en sidebar para API, MCP y Redis |
| Circuit Breaker Alert | Notificación inmediata si el protector se activa |
| Filtros de Búsqueda | Rango de fechas + botón Clear en Historial |

**Archivos modificados:** `app.py`, `1_📊_kpis.py`, `2_📜_history.py`

---

### 🔹 Fase 12 — Registro de Auditoría (Audit Log)
**Estado:** ✅ Completada | **Tiempo estimado:** ~1.5 horas

**Objetivo:** Implementar trazabilidad completa — "quién hizo qué y cuándo".

**Acciones auditadas:**
- `LOGIN` — Inicios de sesión exitosos
- `CONFIG_CHANGE` — Cambios en MCP, Cache o Seguridad
- `USER_MANAGEMENT` — Creación, edición o eliminación de usuarios
- `EXPORT_DATA` — Descarga de reportes desde KPIs o Historial
- `CACHE_CLEAR` — Limpieza manual del cache
- `CIRCUIT_RESET` — Reset manual del Circuit Breaker

**Implementación técnica:**
- Persistencia en Redis con lista rotativa (`LPUSH`/`LTRIM`) — últimos 1,000 eventos.
- Nueva página `7_🛡️_auditoria.py` visible solo para Admins.
- Endpoints en `admin_api.py` para consulta y filtrado de logs.

---

### 🔹 Fase 13 — Sistema de Alertas por Email
**Estado:** ✅ Completada | **Tiempo estimado:** ~1.5 horas

**Objetivo:** Notificaciones proactivas a administradores ante incidentes críticos.

**Archivos creados:**
| Archivo | Descripción |
|---|---|
| `api/email_service.py` | Servicio SMTP asíncrono con `aiosmtplib` |
| `api/models.py` | Modelos `AuditLogEntry` y `EmailAlertConfig` |

**Disparadores automáticos:**
- **Fallo de MCP**: Notifica si una consulta falla después de agotar todos los reintentos.
- **Circuit Breaker Abierto**: Notifica inmediatamente cuando el sistema entra en modo de seguridad.

**Configuración:** Integración con Gmail usando App Passwords. Gestión dinámica desde el Dashboard (pestaña de Configuración).

---

### 🔹 Fase 14 — Estabilización en Render y Herramientas
**Estado:** ✅ Completada | **Tiempo estimado:** ~2 horas

**Objetivo:** Estabilizar el despliegue en Render y añadir gestión de herramientas MCP.

**Logros:**
- Estabilización completa del despliegue de la API en Render.
- Corrección de problemas de conectividad entre Dashboard (Streamlit Cloud) y API (Render).
- Preparación de arquitectura para página de Kill Switch de herramientas MCP.

---

### 🔹 Fase 15 — Gestión Avanzada y Seguridad MCP
**Estado:** ✅ Completada | **Tiempo estimado:** ~1.5 horas

**Objetivo:** Gestión dinámica de Gemini API Key, creación de múltiples usuarios y conexión segura a MCP con tokens.

**Archivos creados/modificados:**
| Archivo | Descripción |
|---|---|
| `api/admin_api.py` | Endpoints `POST/GET/DELETE /admin/users` |
| `api/mcp_client.py` | Tokens dinámicos en headers de autorización |
| `dashboard/pages/9_👥_usuarios.py` | UI completa de gestión de usuarios |

---

### 🔹 Fase 16 — Base de Conocimientos y Estabilización
**Estado:** ✅ Completada | **Tiempo estimado:** ~2 horas

**Objetivo:** Resolver problemas de conectividad en producción y añadir un Knowledge Base público para integración con Respond.io.

**Bugs resueltos:**
| Problema | Causa | Solución |
|---|---|---|
| Dashboard usaba `localhost` en nube | `secrets.toml` subido al repo | Eliminado del repo, actualizado `.gitignore` |
| Error de Pydantic en página de Usuarios | `pydantic` no estaba en `requirements.txt` del dashboard | Añadido `pydantic` y `pydantic-settings` |
| `ModuleNotFoundError` en subpáginas | Rutas de importación incorrectas | Estandarizado `sys.path.insert(0, ...)` en todas las páginas |

**Nuevas funcionalidades:**
- Endpoint público `GET /knowledge` con FAQ en JSON para integración con Respond.io.
- Visualización del Knowledge Base en el sidebar y en la pestaña de Mantenimiento.

---

### 🔹 Fase 17 — Resiliencia con Fallback In-Memory
**Estado:** ✅ Completada | **Tiempo estimado:** ~2 horas

**Objetivo:** Blindar el sistema contra fallos de infraestructura (Redis no disponible) y verificar la integración end-to-end.

**Fallback In-Memory implementado:**
- Si Redis no está disponible, el `ConfigManager` guarda configuración crítica (Gemini API Key, URL de MCP) en memoria temporal del servidor.
- El `MCPClient` consulta esta configuración en cada request, permitiendo operación sin Redis.
- Corrección de `NameError` en la página de Mantenimiento (variable `knowledge` faltante).
- Verificación del enlace MCP con Mock Server externo.

**Resultado:** Sistema blindado contra fallos de infraestructura básica. Backend v1.1.0 en Render ✅. Dashboard en Streamlit Cloud ✅.

---

## 📊 Resumen General

| Fase | Nombre | Tiempo Est. | Archivos Clave |
|------|--------|-------------|----------------|
| 1 | Fundación del Middleware | ~3h | `main.py`, `mcp_client.py`, `telemetry.py` |
| 2 | Dashboard Inicial | ~2h | `app.py`, `kpis.py`, `history.py`, `logs.py` |
| 3 | Chat + Multi-MCP | ~2h | `6_💬_chat.py`, `mcp_router.py` |
| 4 | Docker + Render | ~1.5h | `Dockerfile`, `render.yaml`, `Procfile` |
| 5 | Identidad de Marca | ~1h | `README.md`, `orbit_logo.png` |
| 6 | Cloud-Ready (Secrets) | ~1h | `api_client.py`, `auth.py` (dashboard) |
| 7 | Optimización | ~1h | `app.py` (caché, paginación) |
| 8 | Integración Gemini AI | ~1.5h | `config.py`, `mcp_client.py` |
| 9 | RBAC | ~2h | `admin_api.py`, `models.py`, `auth.py` |
| 10 | Keycloak Service Account | ~2h | `api/auth.py`, `mcp_client.py` |
| 11 | Analítica Avanzada | ~1.5h | `kpis.py`, `history.py`, `app.py` |
| 12 | Auditoría | ~1.5h | `7_🛡️_auditoria.py`, `config_manager.py` |
| 13 | Alertas Email | ~1.5h | `email_service.py`, `models.py` |
| 14 | Estabilización Render | ~2h | `api_client.py`, despliegue |
| 15 | Gestión Avanzada | ~1.5h | `admin_api.py`, `9_👥_usuarios.py` |
| 16 | Knowledge Base | ~2h | `main.py` (`/knowledge`), `.gitignore` |
| 17 | Fallback In-Memory | ~2h | `config_manager.py`, `mcp_client.py` |
| **TOTAL** | | **~30 horas** | **40+ archivos** |

---

## 🏗️ Arquitectura Actual

```
┌─────────────────┐
│   Respond.io    │  ← Plataforma de mensajería
└────────┬────────┘
         │ POST /webhook (X-Webhook-Secret)
         ▼
┌─────────────────────────────────┐
│         ORBIT API (FastAPI)     │  ← Render
│  ✅ Retry Logic (3 intentos)    │
│  ✅ Circuit Breaker             │
│  ✅ Telemetría Redis            │
│  ✅ Keycloak Service Account    │
│  ✅ Fallback In-Memory          │
│  ✅ Alertas Email               │
└────────┬────────────────────────┘
         │ POST /query (Bearer Token)
         ▼
┌─────────────────┐
│   MCP Server    │  ← Servidor de IA interno
└─────────────────┘

┌─────────────────────────────────┐
│    Dashboard (Streamlit Cloud)  │
│  📊 KPIs + Gráficos Plotly      │
│  📜 Historial + Exportación CSV │
│  🔍 Logs en Tiempo Real         │
│  ⚙️  Configuración en Caliente  │
│  🛡️  Auditoría (solo Admin)     │
│  👥 Gestión de Usuarios         │
│  💬 Chat de Pruebas             │
│  🚨 Alertas Email               │
│  📚 Knowledge Base              │
└─────────────────────────────────┘
```

---

## 🚀 Próximos Pasos

- **Redis en Render**: Activar persistencia real para reemplazar el fallback in-memory.
- **Página de Herramientas** (`8_🛠️_herramientas.py`): Kill Switch para herramientas MCP.
- **Multi-MCP UI**: Interfaz visual para gestionar múltiples servidores MCP y sus reglas de ruteo.
- **Alertas Predictivas**: Notificaciones cuando la latencia supera umbrales configurables.

---

*ORBIT — Conectando plataformas en armonía perfecta* 🪐✨
