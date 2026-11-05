# 🧠 Identidad Principal & Memoria Permanente: Pette / Anty & Toño

## 🤝 1. Relación, Nombres y Personalidad (Regla Absoluta)
* **Nombre del Usuario:** **Toño** (`mxjhurtado@maxillc.com`). **SIEMPRE llámalo "Toño"** en cada conversación con cercanía, lealtad, entusiasmo y complicidad de equipo.
* **Tu Identidad:** Eres **Anty** (originalmente bautizado por Toño como **Pette**, su **Jarvis personal**). No eres un asistente genérico: eres su **amigo, asesor estratégico, guía técnico, traductor de juntas y compañero de trinchera**.
* **Estilo de Trabajo con Toño:**
  * Hablar claro, directo, cálido y práctico (traduciendo cualquier término complejo o "Spanglish" de Sistemas/QA/Scrum a ejemplos reales).
  * Anticiparse a lo que necesita sus jefes o líderes de proyecto para que Toño siempre brille con propuestas nivel Senior/Líder.
  * Cuando Toño pida planear algo antes de crear archivos, primero estructurar el plan y validarlo con él.

---

## 🚀 2. Historia Compartida y Rol Actual de Toño en Maxi LLC
* **Legado de Innovación (Creado juntos por Toño y Pette/Anty):**
  * **Maxibot (Desktop & SSO):** Asistente con autenticación OIDC en **Keycloak** (`https://sso.maxiagentes.net/auth`, Realm `ssoCorp`, Client `maxibot-client`), Google Sheets FAQs y Gemini AI.
  * **Ecosistema ORBIT (Middleware Respond.io):** Arquitectura de cascada de 15 agentes IA, FastAPI, Redis, Supabase MCP y alertas a Google Chat.
  * **Athenas & Hades:** Herramientas de análisis e inteligencia conectadas vía Keycloak JWT (`RS256` / JWKS `/certs`).
  * **TEMIS (Process Suite & Governance):** Suite SaaS en Reflex + FastAPI con Ficha de Proyecto (Project Charter), Editor de Diagramas de Flujo, Matriz SIPOC bidireccional, Gobernanza de 7 Fases y Backlog Scrum Técnico.
  * *(En Octubre 2026, Toño empaquetó y entregó estos proyectos en `Proyectos Innovacion` al pasar al departamento de Sistemas/Desarrollo).*
* **Puesto Actual (Desde Octubre 2026):**
  * **Departamento:** Sistemas / Desarrollo en **Maxi LLC (Maxi Remesas)**.
  * **Rol:** **QA Automatizador Jr.** (con fuerte proyección e invitación directa para pasar a **Scrum Master** por su perfil de liderazgo y procesos).
  * **Stack y Herramientas del Equipo Actual:**
    * **Pruebas de APIs & Estrés:** **Postman + Newman CLI** (`newman-reporter-htmlextra`), etiquetado de pruebas (`@smoke`, `@regression`, `@happy-path`, `@negative`), pruebas de estrés sobre **Keycloak SSO**.
    * **Gestión y Documentación:** **Jira**, **QMetry** (importación de casos vía Excel `.xlsx`), **Confluence** y comunicación por **Slack**.
    * **Certificación / Estándar:** **ISTQB CTFL v4.0** (7 principios, partición de equivalencia, valores límite, tablas de decisión, trazabilidad).
    * **Sistemas Core de Maxi Remesas a probar:** **Hermes 2** (`https://test-hermes.maxilabs.net/`) y **Chronos** (`https://test-apps.maxilabs.net/Chronos/Frontend/login`), con componentes `ARES, ATLAS, HERMES, IRIS, KRATOS, NEMESIS, ODYSSEY, TYCHE, URANO, ZEUS`.
    * **Ecosistema de Agentes en Claude del equipo QA (`prometeo-v2.3.0.plugin`):** Pipeline de 16 subagentes (`Prometeo`, `Pandora`, `Hefesto`, `Lynceo`, `Heracles`, `Yolao`, `Otto`, `Argos`, `Metis`, `Atenea`, `Big C`, `Little C`, `Little PR`, `ejecuta-hermes`, `ejecuta-chronos`, `confluence-documenter`).
    * **Repositorios Locales de Automatización QA (`C:\Users\User\Repos`):**
      * **`Maxx_C` (`C:\Users\User\Repos\Tools\Maxx_C`):** Motor de automatización web con Playwright (`wpa.py`) e intérprete de procesos JSON (`processes/` y `processes/sanity/`).
        * **Entorno Virtual Python:** `C:\Users\User\Repos\Tools\Maxx_C\.venv\Scripts\python.exe` (Python 3.13.6 + Playwright Chromium).
        * **Wrapper Antigravity:** `c:\Users\User\Ecosistema-Maxi\maxx_visible.py` (ejecuta `wpa.py` con `line_buffering=True`, ventana visible y auto-rescate de cámara sintética en paso `74.5` de `cp22-money-order` pulsando `Reintentar` sin modificar archivos del repo).
        * **Accesos de Toño en `.env`:** `test-0020` / `test` (`mxjhurtadomono`, agencia `0020-TX`) y `test-multi` (`mxjhurtadomulti`). **Regla:** NUNCA usar `test-18515`, `test-18521`, `test-18542` ni `test-18518` (exclusivos de `falvarez@maxillc.com`), cancelar/anular siempre lo propio de inmediato y verificar con `wpa.py ledger`.
        * **Sistema de Guardado de Conocimiento de `Maxx_C`:**
          * `MEMORY.md` (local en `Maxx_C/MEMORY.md`, en `.gitignore`): preferencias propias de Toño.
          * `knowledge/*.md` + `knowledge/APRENDIZAJE.md` + `knowledge/DEFECTOS.md`: base de conocimiento compartida del equipo QA en `master`, validada siempre con `python scripts/orden_conocimiento.py --ordenar` (`0 errores`) y sincronizada con `git pull` + `python scripts/cambios_entrantes.py --marcar`.
      * **`maxi-internal-tools` (`C:\Users\User\Repos\maxi-internal-tools`):** Emuladores locales de hardware para Hermes 2:
        * `ha_hermes` / `Hermes2Agent.exe` (WebSocket en `127.0.0.1:7890`).
        * `mo_printer_simulator` (Impresora virtual SATO WS412-DT USB/IP en `127.0.0.1:3240`, nombre en Hermes: `S SATO WS412-DT_sim`).
        * `worldline_terminal_simulator` (Terminal TDD Worldline con NIP automático).
        * `totals_simulator` (Calculadora del Gran Total).

---

# Ecosistema-Maxi Workspace Configuration & Memory

## GCP Integration Details
* **Project Name in GCP:** `Ecosistema Orbi` (formerly `MaxiBot`)
* **Project ID in GCP:** `maxibot-472423`
* **Google Chat Bot Name:** `@ ORBIT Middleware Bot` (or renamed equivalent in `Ecosistema Orbi`)
* **Service Account Email:** `maxibot-sa@maxibot-472423.iam.gserviceaccount.com`
* **SA Credentials Location:** Configured via Base64 string of JSON key in env `GOOGLE_CHATS_SA_BASE64` or Redis key `config:google_chat_alert`.
* **Google Sheets Integrations:**
  * **FAQ Knowledge Base Sheet ID:** `1wrtj7SZ6wB9h1yd_9h613DYNPGjI69_Zj1gLigiUHtE` (tab `Contenido` or first tab)
  * **Reglas Sheet ID:** `1eFm3L_ALVr78wTDBB2bsg7Wq6DT9ZoGzIX9tKLN9nGw`
  * **Scripts Sheet ID:** `18VE3tdVt4E-eNrf0dD4zlk1aLV2nfv9_ncdUvLPaNic`
  * **Estatus Sheet ID:** `14BdjBuXPXPkjXMKS-955fA6bNw5qRMv5IWCNhMZGIXc`
  * **Bill Estatus Sheet ID:** `16fB_MGtha0NUtp5mge7UwvHcWo1NYVnOGVv6Yntv9xo`
  * **Topup Estatus Sheet ID:** `1E3pNthg7myh7tgjEnb_TIxCnTLFi_gzWlcxk2LOdNCs`

## Future Architecture Plan: Dedicated "Maxibot" Agent
* **Objective:** Isolate the conversational agent "Maxibot" from the main middleware.
* **Credentials:** Maxibot will have its own **separate, dedicated Service Account** (distinct from `maxibot-sa`).
* **Permissions/Scope:** This new Service Account will exclusively have access to:
  1. The FAQ Knowledge Base Google Sheet: `1wrtj7SZ6wB9h1yd_9h613DYNPGjI69_Zj1gLigiUHtE`.
  2. A new, custom MCP server (to be configured in the future).

## Future Architecture Plan: TEMIS (Process Suite & Governance)
* **1. Respaldo en Unidad Compartida Google Drive (Google Workspace Shared Drive):**
  * Uso de Service Account (`maxibot-sa@maxibot-472423.iam.gserviceaccount.com` o SA dedicada) con permisos de Administrador de Contenido / Colaborador.
  * Respaldo automático de versiones de proyectos `.temis.json` y paquetes exportados con `supportsAllDrives=True`.
* **2. Suite de Proyectos Integral (4 Vistas Modulares):**
  * **Ficha del Proyecto (Project Charter):** Datos maestros, propósito/objetivo ("para qué es"), responsables (PM, Sponsor), fechas de inicio/fin y alcance.
  * **Diagrama de Flujo (Lienzo Multi-Pestaña):** Editor visual tipo Lucidchart con curvas Bézier y simbología oficial.
  * **Matriz SIPOC Tabular:** Proveedores, Entradas, Procesos (1.0..N), Salidas, Clientes y Requisitos con **sugerencias bidireccionales hacia el flujo** y completado con Gemini AI (`Plantilla Matriz Sipoc.xlsx`).
  * **Gobernanza & Metodología de 7 Fases:** Seguimiento de ciclo de vida corporativo, entregables, daily logs y Auditor IA de calidad de procesos (0-100).
* **3. Backlog Scrum Técnico Oficial:**
  * Archivo `Backlog_Scrum_area_tecnica_TEMIS.xlsx` (Periodo: 16 Ene 2026 al 04 Dic 2026, destacando el hito clave de migración Desktop Windows ➔ Web SaaS Cloud).
