# Roadmap Estratégico y Técnico del Proyecto TEMIS 2026

**TEMIS PROCESS SUITE | PLANIFICACIÓN ESTRATÉGICA & BACKLOG SCRUM**
- **Iniciativa:** Proyecto TEMIS (BPMN Suite & Governance) | **Código:** TEMIS-GOV-2026-V1
- **Sponsor:** Dirección de Operaciones & Tecnología | **Project Lead:** Ing. Mario Hurtado
- **Periodo Oficial:** 16 Enero 2026 – 04 Diciembre 2026 | **Estatus:** Línea Base Oficial Aprobada

---

## 1. Resumen Ejecutivo y Visión Estratégica
El Proyecto TEMIS nace como una respuesta estratégica y corporativa ante la necesidad de **soberanía tecnológica, control de costos operativos y estandarización metodológica** en la gestión de procesos de negocio (BPMN).

La organización identificó una fuga presupuestal recurrente debido a las costosas licencias por usuario de **Lucidchart (Lucid Software Inc.)**, sumado a la desconexión operativa entre diagramas estáticos y la redacción manual de manuales de procedimientos en Word. TEMIS consolida una Suite Integral Web SaaS Cloud que fusiona la Matriz SIPOC Six Sigma, diagramación vectorial con curvas Bézier perimetrales, redacción automatizada de políticas con IA (Gemini 2.5 Flash) y gobierno corporativo en 7 fases.

El Roadmap comprende 10 Sprints de desarrollo ágil y 47 commits base de ingeniería entre el 16 de Enero de 2026 y el 04 de Diciembre de 2026.

---

## 2. Dashboard Ejecutivo de Sprints & Capacidad Técnica (2026)

| Sprint | Periodo | Objetivo Estratégico | Módulos Clave | Hito Principal | Estado | Story Points |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Sprint 01** | 16 Ene - 28 Feb 2026 | Arquitectura Base & Persistencia Windows Desktop | Core / DB / Sync | Base de datos compartida SQLite + Sync Google Drive | Completed | 34 |
| **Sprint 02** | 01 Mar - 30 Abr 2026 | Gobernanza de Proyectos & Metodología 7 Fases | Gobernanza / Actas | Modelado de Fases 1 a 7, Daily Logs, Roles y Entregables | Completed | 42 |
| **Sprint 03** | 01 May - 30 Jun 2026 | Motor de Diagramación Inicial Desktop & Pruebas | Canvas Desktop | Lienzo de dibujo de procesos y exportación inicial | Completed | 38 |
| **Sprint 04** | 01 Jul - 26 Ago 2026 | Desacoplamiento Arquitectónico & Preparación API | FastAPI / Backend | Diseño de API REST FastAPI y modelos Pydantic | Completed | 30 |
| **Sprint 05** | 27 Ago - 31 Ago 2026 | 🔥 **HITO CLAVE: Reestructuración Desktop ➔ Web SaaS Cloud** | Reflex / Render / Parser | Migración a Reflex Full-Stack, PostgreSQL 18, Parser Nativo Lucidchart | Completed | 65 |
| **Sprint 06** | 01 Sep - 15 Sep 2026 | Reingeniería UI/UX Pro & Auditoría IA de Procesos | UI/UX / Gemini AI | Header 50px, Dock izquierdo, Inspector derecho, Auditor Gemini AI | Completed | 45 |
| **Sprint 07** | 16 Sep - 30 Sep 2026 | Persistencia Híbrida & Exportador Gráfico Alta Resolución | Export PNG/PDF / DB | Exportador vectorial PNG/PDF 300 DPI y Auto-Guardado PostgreSQL | In Progress | 28 |
| **Sprint 08** | 01 Oct - 31 Oct 2026 | Mapeador Automático de Swimlanes & Multi-Usuario | Swimlanes / Colab | Auto-layout de carriles por rol/sistema y sincronización web | Planned | 35 |
| **Sprint 09** | 01 Nov - 20 Nov 2026 | Respaldo en Unidad Compartida Google Drive & Seguridad | Drive SA / Seguridad | Backup automático en Drive con Service Account y seguridad RBAC | Planned | 25 |
| **Sprint 10** | 21 Nov - 04 Dic 2026 | QA Integral, Pruebas de Carga & Entrega Final | QA / Producción / Docs | Pruebas de estrés (+2,000 nodos), manuales y Cierre de Proyecto | Planned | 20 |

---

## 3. Distribución de Esfuerzo por Módulo Arquitectónico

| Módulo Técnico | Total Items | Completados | En Progreso | Planificados | Horas Estimadas | % Avance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Reflex Web SaaS Cloud (Render Deployment)** | 4 | 4 | 0 | 0 | 85 h | 100% |
| **Parser Lucidchart Determinista (8 Pestañas)** | 3 | 3 | 0 | 0 | 70 h | 100% |
| **UI/UX Reingeniería Pro (Header 50px, Dock, Inspector)** | 3 | 3 | 0 | 0 | 65 h | 100% |
| **Conexión Interactiva & Curvas SVG Bézier** | 2 | 2 | 0 | 0 | 45 h | 100% |
| **Auditor de Calidad IA (Gemini 2.5 Flash)** | 2 | 2 | 0 | 0 | 40 h | 100% |
| **Gobernanza 7 Fases & Matriz SIPOC Six Sigma** | 2 | 2 | 0 | 0 | 50 h | 100% |
| **FastAPI Backend & PostgreSQL DB Persistence** | 2 | 1 | 1 | 0 | 45 h | 75% |
| **Exportación Gráfica (PNG/PDF) & Drive Backup SA** | 2 | 0 | 1 | 1 | 55 h | 30% |

---

## 4. Trazabilidad de Commits y Entregables Clave
1. **Commit `4c0e337` (16 Ene 2026):** Implementación de base de datos compartida SQLite y sincronización inicial con Google Drive.
2. **Commit `fe136da` (27 Ago 2026 - 🔥 HITO FUNDACIONAL):** Migración de cliente de escritorio Windows a Web SaaS Full-Stack con Reflex, FastAPI, PostgreSQL y Render.
3. **Commit `9f31c2f` (27 Ago 2026):** Parser nativo determinista para CSV/JSON de Lucidchart sin depender de IA.
4. **Commit `70a72ca` (27 Ago 2026):** Cálculo matemático de trazado SVG Bézier `M x1 y1 C cx1 cy1, cx2 cy2, x2 y2` con ruteo perimetral Este-Oeste.
5. **Commit `9805816` (10 Sep 2026):** Reingeniería UI/UX Pro (Header 50px, Dock lateral izquierdo de simbología BPMN/Sistemas/Canales, Inspector derecho contextual).
6. **Commit `592127e` (10 Sep 2026):** Conexión interactiva de casillas, auto-guardado reactivo y motor de auditoría de gobernanza con Gemini IA (0-100).
