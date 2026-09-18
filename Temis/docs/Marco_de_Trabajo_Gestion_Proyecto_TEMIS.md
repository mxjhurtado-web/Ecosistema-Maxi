# Marco de Trabajo para la Gestión y Gobernanza del Proyecto TEMIS

**TEMIS PROCESS SUITE | MARCO METODOLÓGICO & GOBERNANZA CORPORATIVA**
- **Iniciativa:** Proyecto TEMIS (BPMN Suite & Governance) | **Código:** TEMIS-GOV-2026-V1
- **Sponsor:** Dirección de Operaciones & Tecnología | **Project Lead:** Ing. Mario Hurtado
- **Periodo Oficial:** 16 Enero 2026 – 04 Diciembre 2026 | **Estatus:** Línea Base Oficial Aprobada

---

## 1. Propósito y Principios Rectores
El presente Marco de Trabajo establece la metodología oficial para la gobernanza, diseño, estandarización y ciclo de vida de procesos operativos en la organización utilizando la Suite TEMIS.

1. **Soberanía Tecnológica y Cero Licenciamiento Externo:** Erradicación absoluta de la dependencia de herramientas de terceros sujetas a costosas rentas mensuales por usuario (Lucidchart, Miro, Visio), asegurando que el activo intelectual de procesos resida en infraestructura propia y segura.
2. **El Pipeline Automatizado de 3 Pasos:** Toda iniciativa de procesos debe construirse bajo el flujo unidireccional y sin fricción:
   - **(a) Captura Estructurada en Matriz SIPOC Six Sigma**
   - **(b) Generación Instantánea del Diagrama de Flujo Bézier**
   - **(c) Redacción Automática del Manual de Políticas y Procedimientos en Texto Corrido con Gemini 2.5 Flash**
3. **Auditoría de Calidad Determinista (Score 0-100):** Implementación obligatoria de validaciones estructurales en tiempo real para impedir que procesos con compuertas de decisión huérfanas, actividades sin sistema asignado o rutas truncadas pasen a producción.
4. **Gestión Basada en Evidencias (Evidence-Based Management):** Monitoreo transparente del avance del proyecto a través de Daily Logs, control de desviaciones y trazabilidad de entregables por fase.

---

## 2. Estructura de Roles y Matriz RACI de Gobernanza

| Rol en el Proyecto | Responsable / Área | Responsabilidad Principal |
| :--- | :--- | :--- |
| **Sponsor Ejecutivo** | Dirección de Operaciones & Tecnología | Aprobación estratégica, validación del Project Charter, financiamiento y remoción de bloqueos organizacionales. |
| **Project Lead / PM** | Ing. Mario Hurtado (Área Técnica) | Gestión integral del proyecto, aseguramiento del Roadmap 2026, control de calidad y cumplimiento de hitos. |
| **Product Owner (PO)** | Líder de Procesos & Negocio | Definición y priorización del Backlog funcional, validación de plantillas SIPOC y criterios de aceptación. |
| **Tech & Architecture Lead** | Equipo de Arquitectura de Software | Diseño e implementación de la arquitectura full-stack (Reflex, FastAPI, PostgreSQL, Render Cloud). |
| **AI & Automation Specialist** | Área de Innovación e IA | Ingeniería de prompts, integración de Gemini 2.5 Flash para generación de narrativa y motor de auditoría. |
| **Process & QA Auditor** | Comité de Calidad y Procesos | Auditoría de manuales de procedimientos, verificación Six Sigma de diagramas y certificación UAT. |

### Matriz RACI por Fase del Proyecto
| Fase de Gobernanza | Sponsor | Project Lead | Product Owner | Tech Lead | Process QA |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **F1: Diagnóstico Estratégico** | A | R | C | C | I |
| **F2: Inicio del Proyecto (Charter)** | A | R | R | C | I |
| **F3: Planificación Híbrida & Backlog** | I | R | R | R | C |
| **F4: Ejecución Iterativa (Sprints)** | I | R | C | R | C |
| **F5: Monitoreo y Auditoría IA** | C | R | C | C | R |
| **F6: Mejora Continua (Kaizen)** | I | R | R | C | R |
| **F7: Cierre del Proyecto & Traspaso** | A | R | R | I | R |

*(R = Responsable, A = Aprobador, C = Consultado, I = Informado)*

---

## 3. El Ciclo de Vida Metodológico en 7 Fases Corporativas
- **Fase 1: Diagnóstico Estratégico:** Análisis del dolor de Lucidchart/Word, mapeo AS-IS, delimitación de requerimientos, justificación de ROI.
- **Fase 2: Inicio del Proyecto:** Project Charter oficial, asignación de roles, matriz SIPOC inicial de alcance.
- **Fase 3: Planificación Híbrida:** Backlog Scrum Técnico 2026, arquitectura técnica (Reflex/FastAPI/Postgres), matriz de riesgos.
- **Fase 4: Ejecución Iterativa:** Sprints de desarrollo, Daily Logs, releases continuos, generación de manuales con IA.
- **Fase 5: Monitoreo y Control:** Semáforo del proyecto (Alcance, Tiempo, Costo, Calidad), auditoría con IA (0-100), pruebas UAT y gestión de bloqueos.
- **Fase 6: Mejora Continua:** Plan Kaizen post-sprint, optimización de algoritmos de ruteo SVG Bézier, feedback de analistas de procesos.
- **Fase 7: Cierre del Proyecto:** Acta de aceptación y entrega formal, traspaso a operaciones, paquete `.temis.json`, lecciones aprendidas.

---

## 4. Matriz de Riesgos y Mitigaciones Clave

| ID | Riesgo Identificado | Prob. / Impacto | Estrategia de Mitigación | Responsable |
| :--- | :--- | :---: | :--- | :--- |
| **R-01** | Resistencia de usuarios al cambio desde Lucidchart. | Media / Alto | Capacitaciones prácticas, interfaz gemela (Dock + Inspector) e importador 1-clic de Lucidchart. | PO / PM |
| **R-02** | Inconsistencias en generación de texto con IA (alucinación). | Baja / Medio | Implementación de Gemini 2.5 Flash con prompts rígidos basados estrictamente en la matriz SIPOC. | AI Specialist |
| **R-03** | Cuellos de botella en renderizado de diagramas gigantes (+500 nodos). | Baja / Alto | Virtualización de canvas SVG, optimización de árboles DOM y ruteo perimetral compilado. | Tech Lead |
| **R-04** | Pérdida de datos por desconexión en clientes web. | Media / Alto | Mecanismo de auto-guardado reactivo (debounced 2s) en PostgreSQL y exportación .temis.json local. | Tech Lead |
| **R-05** | Falta de estandarización en nombres de sistemas (ej. Chronos/ERP). | Media / Medio | Catálogo cerrado de sistemas y canales en el Dock izquierdo y validación automática del Auditor IA. | Process QA |

---

## 5. Auditoría de Calidad Six Sigma (Score 0-100)
El motor de TEMIS evalúa automáticamente el diagrama contra 8 reglas cardinales:
1. **Inicio Obligatorio (-25 pts):** Debe existir exactamente 1 nodo de inicio (`circle-play`).
2. **Fin Obligatorio (-20 pts):** Debe existir al menos 1 nodo de fin (`circle-stop`).
3. **Decisiones Conclusas (-15 pts c/u):** Rombos con menos de 2 salidas (ej. falta rama 'No').
4. **Asignación de Sistema (-5 pts c/u):** Actividades sin software corporativo asignado (ej. Chronos).
5. **Asignación de Canal (-5 pts c/u):** Actividades sin canal definido (ej. WhatsApp, Bria).
6. **Secuencia SIPOC (-10 pts):** Desalineación de numeración 1.0..N.
7. **Ruteo Bézier Limpio (-5 pts):** Trazados sin cruces ni superposiciones de texto.
8. **Ficha de Proyecto (-10 pts):** Datos maestros y sponsor incompletos en el Charter.
