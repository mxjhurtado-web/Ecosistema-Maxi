# Agente de Estatus en Respond.io — Configuración Completa

**Fecha de configuración:** 2026-03-17  
**Estado actual:** En prueba — acción HTTP funcional, ajuste de integración MCP pendiente

---

## Arquitectura del Flujo

```
WhatsApp → Respond.io (AI Agent) → HTTP Action → MCP Maxi Estatus → Supabase
```

El AI Agent de Respond.io llama directamente al servidor MCP (sin pasar por orbit-api) para consultar el estatus del envío.

---

## Servicios involucrados

| Servicio | URL | Plataforma |
|---|---|---|
| MCP Maxi Estatus | `https://mcp-maxi-estatus.onrender.com` | Render (free) |
| Orbit API | `https://orbit-api-xnyd.onrender.com` | Render (free) |
| Base de datos | Supabase — tabla `Base_completa` | Supabase |

---

## Configuración del AI Agent en Respond.io

### Datos generales
- **Nombre**: `Agente Estatus Maxi`
- **Emoji**: 📦 (o el que prefieras)
- **Descripción**: Agente especializado en consulta de estatus de envíos Maxi

### Instrucciones (prompt del agente)
```
Eres el Agente de Estatus de MAXI. Tu única función es consultar el estado de envíos.

CUANDO RECIBAS UN CÓDIGO DE ENVÍO:
- Ejecuta inmediatamente la acción HTTP "ConsultarEstatus"
- Responde con la información exacta que retorne el sistema
- NO inventes ni supongas información

SI EL CLIENTE NO DA EL CÓDIGO:
- Pide amablemente: "Para consultar tu envío, necesito tu código de envío (ej: CE17016886149). ¿Me lo puedes proporcionar?"

TONO: Profesional, amable y conciso.
```

---

## Acción HTTP: ConsultarEstatus

### ¿Cuándo ejecutarla?
```
Usa esta acción cuando el cliente quiera saber el estado de su envío o 
proporcione un código de envío. Ejecuta la acción con el código que el 
cliente te dé.
```

### Campo requerido por el agente
| Nombre | Formato | Descripción |
|---|---|---|
| `codigo_envio` | Text | Código de envío del cliente (ej: CE17016886149). Pídelo si no lo proporciona. |

### Configuración de la solicitud HTTP

> ⚠️ **IMPORTANTE:** Llamar directamente al MCP — NO a orbit-api (orbit-api tiene problemas de Redis en Render free tier)

| Campo | Valor |
|---|---|
| **Method** | `POST` |
| **URL** | `https://mcp-maxi-estatus.onrender.com/query` |

**Cabeceras:**
| Clave | Valor |
|---|---|
| `Content-Type` | `application/json` |

**Cuerpo (JSON):**
```json
{
  "query": "$codigo_envio"
}
```

---

## Configuración de Supabase

- **Proyecto:** `tzlomvpugmrpdfatscxe`
- **URL:** `https://tzlomvpugmrpdfatscxe.supabase.co`
- **Tabla:** `Base_completa`
- **RLS:** DESACTIVADO (para permitir lectura con anon key)
- **Anon Key:** guardada en Render como variable `SUPABASE_ANON_KEY`

---

## Configuración de Render (mcp-maxi-estatus)

| Variable | Valor |
|---|---|
| `SUPABASE_URL` | `https://tzlomvpugmrpdfatscxe.supabase.co` |
| `SUPABASE_ANON_KEY` | *(ver Render → Environment — clave anon de Supabase)* |

**Start Command:**
```
PYTHONPATH=. uvicorn api.m_cp:app --host 0.0.0.0 --port $PORT
```

---

## Monitoreo — UptimeRobot

Ambos servicios configurados en UptimeRobot con ping cada 5 min:

| Monitor | URL | Estado |
|---|---|---|
| MCP Maxi Estatus | `https://mcp-maxi-estatus.onrender.com/health` | Activo |
| Orbit API | `https://orbit-api-xnyd.onrender.com/health` | Activo |

---

## Columnas clave de la tabla `Base_completa` (Supabase)

| Columna | Descripción |
|---|---|
| `Codigo_de_envio` | Código único del envío (ej: CE17016886149) |
| `status` | Estado actual (PAGADO, DETENIDO, EN TRÁNSITO, etc.) |
| `message_to_user` | Mensaje personalizado para el cliente |
| `Nombre_Cliente` | Nombre del destinatario |
| `Numero_telefonico` | Teléfono del cliente |

---

## Estado de la integración (al 2026-03-17)

- [x] MCP Maxi Estatus desplegado en Render y funcional
- [x] Supabase REST API configurada (reemplazó psycopg2 por incompatibilidad de puertos)
- [x] RLS desactivado en tabla `Base_completa`
- [x] AI Agent creado en Respond.io con prompt e instrucciones
- [x] Acción HTTP `ConsultarEstatus` configurada
- [x] UptimeRobot monitoreando ambos servicios
- [ ] **PENDIENTE:** Verificar que variable `$codigo_envio` se sustituye correctamente en el cuerpo JSON de Respond.io
- [ ] **PENDIENTE:** Probar la acción HTTP con URL directa al MCP (`/query`) — sin pasar por orbit-api

---

## Problemas conocidos

### orbit-api con Redis en localhost
Al redesplegar, orbit-api a veces conecta a `redis://localhost:6379` en lugar de la URL de Redis real. Esto impide cargar el MCP_URL desde la configuración. **Solución:** Llamar directamente al MCP desde Respond.io, sin pasar por orbit-api.

### UptimeRobot 405 en /health (resuelto)
UptimeRobot enviaba peticiones HEAD al endpoint `/health` que solo aceptaba GET. **Solución:** Cambiado a `@app.api_route("/health", methods=["GET", "HEAD"])` en `m_cp.py` y `main.py`.

---

## Próximos pasos

1. Probar la acción HTTP directa al MCP con `$codigo_envio` en el body
2. Verificar la sintaxis de variables de Respond.io (`$variable` vs `{{variable}}`)
3. Conectar el agente a un canal de WhatsApp para prueba real
4. Decidir si se necesita orbit-api en el flujo o si el MCP directo es suficiente
