# Acta Constitutiva del Proyecto TEMIS (Project Charter Oficial)

**TEMIS PROCESS SUITE | FASE 2: INICIO DEL PROYECTO / PROJECT CHARTER**
- **Iniciativa:** Proyecto TEMIS (BPMN Suite & Governance) | **Código:** TEMIS-CHARTER-2026
- **Sponsor Ejecutivo:** Julio Estévez-Bretón / Dirección de Operaciones & TI
- **Project Lead / PM:** Ing. Mario Hurtado
- **Periodo Oficial:** 16 Enero 2026 – 04 Diciembre 2026 | **Estatus:** Línea Base Oficial Aprobada

---

## 1. Propósito y Justificación de Negocio (Business Case)
El Proyecto TEMIS tiene como propósito fundacional el diseño, desarrollo e institucionalización de una plataforma corporativa soberana e inteligente para el modelado de diagramas BPMN, la estandarización Six Sigma mediante Matrices SIPOC y la redacción automatizada de manuales de procedimientos oficiales.

1. **Erradicación del Gasto en Licenciamiento Externo:** Eliminación total del pago de suscripciones SaaS "per-seat" en dólares de herramientas de terceros (**Lucidchart de Lucid Software Inc.**), generando soberanía tecnológica.
2. **Supresión del Retrabajo Operativo (Diagrama ➔ Word):** Reducción de 20-40 horas a menos de 2 horas mediante el pipeline automatizado: **Matriz SIPOC ➔ Diagrama Bézier ➔ Manual con Gemini 2.5 Flash**.
3. **Gobernanza y Calidad Determinista:** Auditoría estructural en tiempo real (0 a 100) y respaldo automático en **Google Workspace Shared Drive** con Service Account corporativa.

---

## 2. Objetivos Estratégicos y Criterios de Éxito
- **Objetivo General:** Desarrollar y desplegar TEMIS como el estándar corporativo oficial, reduciendo en >= 80% los tiempos de documentación y ahorrando el 100% en licencias externas de diagramación.
- **KPIs:**
  - Reducción del ciclo documental de 30 h a < 2 h por proceso.
  - 100% de consistencia entre diagrama gráfico y manual escrito.
  - Puntuación del Auditor IA >= 90/100 en procesos productivos.
  - Cero costo recurrente en licencias de Lucidchart.

---

## 3. Delimitación del Alcance (Scope Baseline)

| Dimensión | Dentro del Alcance (In-Scope) | Fuera del Alcance (Out-of-Scope) |
| :--- | :--- | :--- |
| **Arquitectura y Despliegue** | Web SaaS Full-Stack (Reflex + FastAPI + PostgreSQL) en Render Cloud. | Soporte a instaladores monolíticos locales heredados de Windows. |
| **Simbología y Notación** | Simbología BPMN oficial, Canales (*WhatsApp, Bria*) y Sistemas (*Chronos, Freshdesk*). | Diagramas UML de clases o planos físicos de red. |
| **Módulos Funcionales** | 4 Vistas Modulares (Ficha Charter, Lienzo Bézier, Matriz SIPOC, Gobernanza 7 Fases). | Motor de ejecución en tiempo real (BPEL / orquestador microservicios). |
| **Almacenamiento** | PostgreSQL en la nube y respaldo en Google Shared Drive con Service Account. | Almacenamiento en cuentas personales de Google Drive o discos locales. |
| **Compatibilidad** | Parser nativo determinista para importar 8 pestañas y 640 líneas de Lucidchart. | Migración de archivos binarios propietarios cerrados. |

---

## 4. Estructura de Gobernanza & Matriz de Roles

| Rol en el Proyecto | Asignado a | Responsabilidad Principal en el Charter |
| :--- | :--- | :--- |
| **Sponsor Ejecutivo** | Julio Estévez-Bretón | Autorización del Charter, financiamiento y remoción de bloqueos organizacionales. |
| **Project Lead / PM** | Ing. Mario Hurtado | Liderazgo integral del proyecto, ejecución del Roadmap 2026 y gestión de calidad. |
| **Product Owner (PO)** | Líder de Procesos & Negocio | Priorización del backlog funcional y criterios de aceptación operativa. |
| **Tech & Architecture Lead** | Equipo de Arquitectura | Infraestructura Web Cloud, PostgreSQL, API REST FastAPI y rendimiento. |
| **AI & Innovation Lead** | Área de Innovación e IA | Integración y prompts de Gemini 2.5 Flash para narrativa y auditoría. |
| **Process & QA Auditor** | Comité de Calidad y Procesos | Auditoría metodológica, validación de manuales y certificación UAT. |

---

## 5. Cronograma Maestro de Hitos y Sprints (2026)

| Hito / Sprint | Periodo | Entregable Clave Comprometido | Estado |
| :--- | :--- | :--- | :--- |
| **Kickoff & Sprint 01** | 16 Ene – 28 Feb 2026 | Base de datos SQLite y sincronización Google Drive inicial. | Completado |
| **Gobernanza & Sprint 02** | 01 Mar – 30 Abr 2026 | Modelado de Gobernanza en 7 Fases, Daily Logs y Matriz RACI. | Completado |
| **Lienzo Base & Sprint 03** | 01 May – 30 Jun 2026 | Motor de diagramación inicial y primeros componentes vectoriales. | Completado |
| **API REST & Sprint 04** | 01 Jul – 26 Ago 2026 | Desacoplamiento arquitectónico con FastAPI y esquemas Pydantic. | Completado |
| **Hito Web SaaS & Sprint 05** | 27 Ago – 31 Ago 2026 | 🔥 Migración a Reflex Full-Stack, PostgreSQL 18 y Parser Lucidchart. | Completado |
| **Suite Pro & Sprint 06** | 01 Sep – 15 Sep 2026 | Header 50px, Dock de formas, Inspector contextual y Auditor Gemini IA. | Completado |
| **Persistencia & Sprint 07** | 16 Sep – 30 Sep 2026 | Exportador gráfico PNG/PDF y auto-guardado en PostgreSQL Cloud. | En Curso |
| **Swimlanes & Sprint 08** | 01 Oct – 31 Oct 2026 | Algoritmo de auto-layout por rol/sistema y sincronización web. | Programado |
| **Drive Backup & Sprint 09** | 01 Nov – 20 Nov 2026 | Respaldo en Unidad Compartida Google Drive con Service Account. | Programado |
| **Release Final & Sprint 10** | 21 Nov – 04 Dic 2026 | Pruebas de estrés (+2,000 nodos), manuales oficiales y Cierre Formal. | Programado |

---

## 6. Formalización y Firmas de Aceptación (Sign-off)

| SPONSOR EJECUTIVO | PROJECT LEAD (PM) | PRODUCT OWNER / QA |
| :---: | :---: | :---: |
| ___________________________________<br>**Julio Estévez-Bretón**<br>Sponsor Ejecutivo del Proyecto<br>Dirección de Operaciones & TI | ___________________________________<br>**Ing. Mario Hurtado**<br>Project Lead / PM Técnico<br>Área Técnica e Innovación | ___________________________________<br>**Líder de Procesos & Calidad**<br>Product Owner / QA Lead<br>Comité de Procesos Corporativos |
