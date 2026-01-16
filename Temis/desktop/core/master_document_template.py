#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Master Project Document Generator - Based on Formato Temis
Generates and updates the complete project document
"""

from datetime import date
from typing import Dict, Any


def generate_master_project_document(project: Dict[str, Any]) -> str:
    """
    Generate the complete master project document
    Based on Formato Temis structure
    """
    
    project_name = project.get('name', '[Nombre del Proyecto]')
    start_date = project.get('start_date', date.today().strftime('%d/%m/%Y'))
    status = project.get('status', 'En Progreso')
    sponsor = project.get('sponsor_name', '[Sponsor]')
    project_lead = project.get('project_lead', '[Project Lead]')
    
    document = f"""# Plantilla maestra de gestión de proyecto
# {project_name}

**Proyecto:** {project_name}  
**Fecha de Inicio:** {start_date}  
**Estado:** {status}

---

## 1. Definición de roles y gobernanza

*Una persona puede asumir varios roles si cumple con las responsabilidades.*

| Rol | Asignado a (Nombre) | Responsabilidad Principal |
|-----|---------------------|---------------------------|
| **Sponsor del Proyecto** | {sponsor} | Asegurar alineación estratégica y patrocinio ejecutivo. |
| **Project Lead** | {project_lead} | Gestión integral del proyecto (plan operativo detallado). |
| **Product Owner (PO)** | [Nombre] | Maximizar valor del producto (dirección de producto). |
| **Project Manager/Agile Lead** | [Nombre] | Asegurar trabajo efectivo, adaptable y eliminar impedimentos. |
| **Developers (Tech + UX/UI)** | [Nombres] | Diseñar, construir y validar la solución. |
| **Resp. de Procesos** | [Nombre] | Asegurar coherencia y evolución de procesos (AS-IS / TO-BE). |
| **Resp. Calidad y Datos** | [Nombre] | Asegurar calidad y toma de decisiones basada en evidencia. |
| **Comité Stakeholders** | [Nombres] | Validar, retroalimentar y aceptar entregables clave. |

---

## 2. Ciclo de vida del proyecto

*Esta sección debe completarse progresivamente siguiendo las 7 fases del marco de trabajo.*

---

### Fase 1: Diagnóstico estratégico

**Objetivo:** Evaluar el panorama y definir objetivos.

**Entregables:**
- [ ] Priorización estratégica de portafolio de proyectos: Confirmar alineación con la estrategia.
- [ ] Informe diagnóstico general: Redactar situación actual.
- [ ] Análisis de procesos AS-IS: Mapeo de procesos actuales (Responsable de Procesos).
- [ ] Mapa de personas: Identificación de arquetipos de usuario.
- [ ] Mapa de experiencia actual (Customer journey map): Mapeo de la experiencia actual del usuario.

#### 1. Priorización Estratégica

Validación de que este proyecto se alinea con el portafolio de la organización.

- **Nombre de la Iniciativa:** {project_name}
- **Alineación Estratégica:** ¿A qué objetivo corporativo responde?
  - [ ] Incremento de ingresos.
  - [ ] Eficiencia Operativa / Reducción de costos.
  - [ ] Experiencia del Cliente / Usuario.
  - [ ] Cumplimiento normativo.
- **Nivel de Prioridad:** [Alto/Medio/Bajo]

#### 2. Informe Diagnóstico General y Procesos (AS-IS)

Comprensión del estado actual antes de proponer soluciones.

- **Problemática / Necesidad detectada:** {project.get('objective', '[Describir problemática]')}
- **Análisis de procesos actuales (AS-IS):**
  - **Responsable:** Responsable de Procesos.
  - **Descripción del flujo actual:** [Describir proceso actual]
  - **Puntos de dolor (Pain Points) en el proceso:**
    1. [Pain point 1]
    2. [Pain point 2]
    3. [Pain point 3]

#### 3. Entendimiento del usuario (UX Research)

Mapeo de necesidades reales para garantizar centricidad en el usuario.

- **Mapa de personas (Arquetipos):**
  - **Perfil A:** [Nombre] - Necesidad principal: [Necesidad]
  - **Perfil B:** [Nombre] - Necesidad principal: [Necesidad]
- **Mapa de experiencia actual (Customer journey map):**
  - **Enlace al diagrama visual del Journey:** [URL o ruta]
  - **Momentos de la verdad identificados:** [Describir]

---

### Fase 2: Inicio del proyecto

**Objetivo:** Establecer la base y roles.

**Entregables:**
- [ ] Acta de Constitución (Project Charter): Autorización formal por el Sponsor.
- [ ] Definición del producto / Visión: ¿Qué vamos a construir? (Product Owner).
- [ ] Gobernanza y roles: Confirmación de la tabla de la Sección 1.
- [ ] Modelo operativo: Definición clara del alcance del proyecto.

#### 1. Acta de Constitución (Project Charter)

Autorización formal del proyecto.

- **Justificación del proyecto:** {project.get('objective', '[Justificación]')}
- **Sponsor:** {sponsor}
- **Presupuesto asignado (CapEx/OpEx):** [Monto]
- **Restricciones y Supuestos:**
  - **Restricción:** [Describir restricción]
  - **Supuesto:** [Describir supuesto]

#### 2. Definición del producto y Visión

Dirección clara liderada por el Product Owner.

- **Visión del producto:** [Describir visión del producto]
- **Alcance del proyecto (Modelo operativo):**
  - **Dentro del Alcance (In-Scope):** [Listar elementos incluidos]
  - **Fuera del Alcance (Out-Scope):** [Listar elementos excluidos]

#### 3. Gobernanza y Matriz de roles

Identificación de quién es quién y cómo se toman decisiones. Confirmación de la tabla de la Sección 1, complementando con responsabilidades (documento de referencia Framework gestión de proyectos.pdf).

---

### Fase 3: Planificación híbrida

**Objetivo:** Desarrollar planes detallados y estrategias.

**Entregables:**
- [ ] Roadmap del proyecto: Línea de tiempo de alto nivel.
- [ ] Backlog inicial priorizado: Lista de requerimientos ordenada por valor (Product Owner).
- [ ] Arquitectura de experiencia: Definición de interacción entre sistemas, procesos y usuarios.
- [ ] Declaración de beneficios (Product Goal): ¿Cuál es el éxito medible?

#### 1. Estrategia de entrega (Roadmap)

Visión temporal de alto nivel (No es un Gantt rígido, es una hoja de ruta).

- **Hito 1 (Fecha):** [Descripción del hito]
- **Hito 2 (Fecha):** [Descripción del hito]
- **Hito 3 (Fecha):** [Descripción del hito]

#### 2. Backlog inicial priorizado

Lista de trabajo ordenada por valor, creada por el Product Owner.

1. **Historia/Requerimiento:** [Descripción]
2. **Historia/Requerimiento:** [Descripción]
3. **Historia/Requerimiento:** [Descripción]

#### 3. Arquitectura de experiencia

Diseño de la interacción entre sistemas, procesos y usuarios.

- **Diagrama de flujo TO-BE (Procesos futuros):** [Enlace o descripción]
- **Componentes Tecnológicos:** [Listar componentes]
- **Puntos de Contacto (Touchpoints):** [Listar touchpoints]

#### 4. Declaración de beneficios (Product Goal)

La meta única y medible que define el éxito.

**Product Goal:** "[Definir objetivo medible del producto]"

---

### Fase 4: Ejecución iterativa

**Objetivo:** Implementar planes a través de Sprints. *Repetir este bloque por cada Sprint.*

**Entregables por Sprint:**
- [ ] Incremento de producto: Entregable funcional al final del sprint.
- [ ] Prototipos UX/UI: Diseños validados antes de código.
- [ ] Historias de usuario refinadas: Listas para desarrollo.
- [ ] Pruebas de usabilidad: Validación con usuarios reales.
- [ ] Diseño y ajustes de proceso TO-BE: Cómo funcionará el nuevo proceso.
- [ ] Sign-off de incrementos: Aprobación formal.

*A diferencia de un Scrum tradicional, este framework exige integrar explícitamente UX (Experiencia de Usuario) y BPM (Gestión de Procesos - TO-BE) dentro del mismo ciclo de desarrollo.*

#### Sprint #[Número]:

**Fechas:** [Inicio] a [Fin]  
**Objetivo del Sprint:** [Describir objetivo]  
**Facilitador:** [Nombre del Agile Lead]

##### 1. Planeación y refinamiento (Sprint planning)

**Entradas:** Backlog priorizado por el Product Owner.

**Historias de usuario seleccionadas:**

**ID Historia:** [ID]  
**Título:** [Título de la historia]  
**Descripción:** Como [rol], quiero [funcionalidad], para [beneficio].

**Componentes del Framework Híbrido:**
- [ ] **Requerimientos UX/UI:** (Referencia a Prototipos UX/UI necesarios).
- [ ] **Impacto en Procesos (TO-BE):** (¿Qué parte del proceso operativo cambia? Responsabilidad de Developers/Resp. Procesos).
- [ ] **Criterios de Aceptación Funcional:** (Lista de validaciones técnicas).

##### 2. Ejecución y Diseño (Trabajo del sprint)

Actividades concurrentes de Developers, UX y Procesos.

**A. Diseño de Experiencia y Procesos (Pre-Desarrollo/Paralelo)**
- [ ] **Prototipos UX/UI:** ¿Se han creado y validado los wireframes/mockups?
- [ ] **Ajuste de Procesos TO-BE:** Documentación de cómo operará el nuevo flujo en la realidad.

**B. Construcción (Desarrollo)**
- [ ] **Desarrollo del Incremento:** Codificación y configuración de la solución.
- [ ] **Integración:** El incremento se conecta con sistemas existentes (Arquitectura de experiencia).

##### 3. Validación y Calidad (Quality Assurance & UX)

Garantizar cumplimiento de funcionalidad y experiencia antes del cierre.

- [ ] **Pruebas de usabilidad:** ¿Usuarios reales han interactuado con el incremento o prototipo?
- [ ] **Revisión de métricas UX:** ¿Cumple con los estándares de experiencia definidos?
- [ ] **Validación funcional:** Pruebas unitarias y de integración.

##### 4. Revisión y Cierre (Sprint Review & Sign-off)

Aprobación formal por parte del Comité y Stakeholders.

**Demo del Incremento:**
- **Fecha de presentación:** [Fecha]
- **Asistentes clave:** Product Owner, Stakeholders, Resp. Calidad.

**Sign-off de Incrementos (Aprobación):**

| Criterio | Estado | Comentarios del Product Owner / Stakeholders |
|----------|--------|---------------------------------------------|
| Funcionalidad | [✓/✗] | [Comentarios] |
| Experiencia (UX) | [✓/✗] | [Comentarios] |
| Procesos (TO-BE) | [✓/✗] | [Comentarios] |

**Decisión final:**
- [ ] Incremento aprobado (Pasa a transición/producción).
- [ ] Incremento rechazado (Vuelve al Backlog para ajustes).

##### 5. Retrospectiva (Mejora continua)

Liderado por el Agile Lead para ajustar estrategias.

- **¿Qué funcionó bien?** (Procesos, herramientas, colaboración): [Describir]
- **¿Qué debemos mejorar?** (Bloqueos, falta de claridad, deuda técnica): [Describir]
- **Plan de acción:** [Definir acciones]

---

### Fase 5: Monitoreo y Control

**Objetivo:** Rastrear progreso y ajustar estrategias (Transversal a la ejecución).

**Entregables:**
- [ ] Aseguramiento de hitos clave: Verificar fechas críticas.
- [ ] Métricas de experiencia del usuario (UX Metrics): Medición de satisfacción y uso.
- [ ] Informes de desempeño: Reportes de avance para el Comité.
- [ ] Gestión de riesgos actualizada: Matriz de riesgos actualizada.
- [ ] Control de cambios: Documentar cambios en tiempo, alcance, costo o calidad.

**Proyecto:** {project_name}  
**Fecha de Corte:** {date.today().strftime('%d/%m/%Y')}  
**Periodo Reportado:** [Periodo]  
**Preparado por:** [Nombre]

#### 1. Resumen Ejecutivo (Semáforo del Proyecto)

Visión general para el Comité de Stakeholders sobre la salud del proyecto.

| Dimensión | Estado | Comentarios Clave |
|-----------|--------|-------------------|
| **Alcance** | 🟢 / 🟡 / 🔴 | ¿Se mantiene el modelo operativo y visión? |
| **Tiempo** | 🟢 / 🟡 / 🔴 | Cumplimiento de hitos clave. |
| **Costo** | 🟢 / 🟡 / 🔴 | Presupuesto ejecutado vs planeado |
| **Calidad / UX** | 🟢 / 🟡 / 🔴 | Satisfacción usuaria y métricas de error. |

#### 2. Aseguramiento de Hitos Clave

Rastreo del progreso contra el Roadmap definido en la Fase 3.

| Hito Principal | Fecha Planeada | Fecha Real/Est. | Estado |
|----------------|----------------|-----------------|--------|
| Ej: Finalización Diagnóstico | 01/02/202X | 01/02/202X | Completado |
| Ej: Sign-off Sprint 1 | 15/02/202X | 16/02/202X | Retraso leve |
| Ej: Entrega a Producción | 30/03/202X | 30/03/202X | En curso |

#### 3. Métricas de experiencia y calidad (Evidence-Based Management)

Datos proporcionados por el Responsable de Calidad y Datos para asegurar decisiones basadas en evidencia.

**A. Métricas de experiencia del usuario (UX Metrics)**
- **Satisfacción (CSAT/NPS) de prototipos/incrementos:** [Valor]
- **Tasa de éxito en tareas (Pruebas de Usabilidad):** [Porcentaje]
- **Feedback cualitativo clave:**
  - [Feedback 1]
  - [Feedback 2]

**B. KPIs del Producto y Calidad técnica**
- **Defectos / Bugs encontrados:** [Número]
- **Deuda Técnica identificada:** [Descripción]
- **Datos de uso (si aplica):** [Métricas]

#### 4. Gestión de riesgos y bloqueos

Actualización de la matriz de riesgos y estado de impedimentos.

| Riesgo / Bloqueo | Probabilidad / Impacto | Estrategia de Mitigación | Dueño |
|------------------|------------------------|--------------------------|-------|
| Ej: Retraso en aprobación legal | Alta / Alto | Sesión extraordinaria con área legal agendada. | Project Lead |
| Ej: Baja disponibilidad de usuarios | Media / Medio | Reclutamiento externo para pruebas UX. | Agile Lead |

#### 5. Control de cambios

Registro formal de desviaciones aprobadas o solicitadas en tiempo, alcance, costo o calidad.

- **Solicitudes de Cambio en este periodo:**
  - **ID Cambio:** [ID] → **Decisión:** [Aprobado/Rechazado]
  - **Impacto:** [Describir impacto]

#### 6. Próximos pasos y Solicitudes al Comité

Acciones requeridas por parte de los Sponsors o Stakeholders para desbloquear el avance.

- [ ] Aprobar el incremento del Sprint actual.
- [ ] Validar cambio de alcance en [Funcionalidad X].
- [ ] Proveer recursos para [Actividad Y].

---

### Fase 6: Mejora continua

**Objetivo:** Refinar procesos post-proyecto.

**Entregables:**
- [ ] Lecciones aprendidas (Integración): Aplicar lo aprendido a futuros proyectos.
- [ ] Propuestas de innovación continua: Siguientes pasos evolutivos.
- [ ] Iteraciones de optimización: Mejoras menores al producto.
- [ ] Informe de retrospectiva global: Visión macro del ciclo.

**Proyecto:** {project_name}  
**Fecha de Cierre:** [Fecha]  
**Sponsor:** {sponsor}  
**Project Lead:** {project_lead}

#### 1. Captación del beneficio y valor entregado

Comparación final entre lo que prometimos (Product Goal) y lo que logramos.

- **Product Goal (Objetivo original):** [Objetivo definido en Fase 3]
- **Resultado Final:** ¿Se cumplió el objetivo?
  - [ ] Sí, totalmente.
  - [ ] Parcialmente.
  - [ ] No se cumplió.
- **Evidencia de Valor:**
  - [Evidencia 1]
  - [Evidencia 2]

#### 2. Revisión final de UX y resultados

Validación de la experiencia del usuario final.

- **Resultados UX:** [Describir resultados]
- **Entregables de Diseño:** Enlace al repositorio final de prototipos y assets.

#### 3. Transición y entrega formal

Paso del proyecto (temporal) a la operación (continuo).

- [ ] **Transferencia de conocimiento:** ¿Se capacitó al equipo de operaciones/soporte?
- [ ] **Documentación técnica:** Manuales, API docs, arquitectura final entregada.
- [ ] **Cierre administrativo:** Contratos cerrados y liberación de recursos del equipo.
- [ ] **Firma de aceptación:**
  - Firma Sponsor: __________________
  - Firma Product Owner: __________________

#### 4. Retrospectiva final (Scrum + Insights UX)

Análisis global del ciclo de vida del proyecto.

- **Lo mejor del proyecto (Highlights):**
  - [Highlight 1]
  - [Highlight 2]
- **Principales dolores (Pain points):**
  - [Pain point 1]
  - [Pain point 2]
- **Conclusiones del Equipo:**
  - [Conclusión 1]
  - [Conclusión 2]

---

### Fase 7: Cierre del Proyecto

**Objetivo:** Finalizar y documentar.

**Entregables:**
- [ ] Captación del Beneficio: Medición final contra el Product Goal.
- [ ] Revisión final de valor y UX: Resultados de experiencia.
- [ ] Entrega formal y transición: Pase a operaciones/producto.
- [ ] Documentación y Lecciones Aprendidas: Archivo del proyecto.
- [ ] Retrospectiva Final: Scrum + Insights de UX.

#### 1. Consolidación de Lecciones Aprendidas

Base de conocimiento para futuros proyectos.

| Categoría | Lección Aprendida | Acción Recomendada para Futuros Proyectos |
|-----------|-------------------|-------------------------------------------|
| Procesos | Ej: El proceso de aprobación legal tardó demasiado. | Involucrar a Legal desde la Fase 1. |
| Tecnología | Ej: La integración con la API X fue inestable. | Realizar PoC técnico antes del Sprint 1. |
| UX | Ej: Los usuarios no entendieron el menú Y. | Testear la navegación con Card Sorting antes de diseñar. |

#### 2. Propuestas de innovación continua

Ideas que quedaron fuera del alcance pero aportan valor.

- **Idea 1:** [Descripción]
  - **Impacto estimado:** [Alto/Medio/Bajo]
  - **Esfuerzo estimado:** [Alto/Medio/Bajo]

#### 3. Iteraciones de optimización del producto

Roadmap post-lanzamiento (Mantenimiento evolutivo).

- [ ] **Optimización 1:** [Mejora menor basada en feedback reciente]
- [ ] **Optimización 2:** [Ajuste de performance]

#### 4. Informe de retrospectiva global

Visión macro para la PMO o directivos.

- **Resumen de madurez del equipo:** ¿Cómo evolucionó la velocidad y calidad del equipo?
- **Recomendaciones al Framework:** Sugerencias para ajustar este estándar de gestión de proyectos.

---

## 3. Principios guía del equipo

*Recordatorio de nuestros valores de trabajo.*

1. **Gobernanza y colaboración:** Roles claros y comunicación abierta.
2. **Valor:** Maximizar el valor y flujo constante de entrega.
3. **Centricidad en el usuario:** Necesidades reales y validación constante.
4. **Diseño de procesos:** Evolución progresiva y habilitación tecnológica (AS-IS → TO-BE).
5. **Sostenibilidad:** Mejora continua y gestión anticipada de riesgos.
6. **Calidad:** Decisiones basadas en datos y adaptación por evidencia.

---

*Documento generado por TEMIS - {date.today().strftime('%d/%m/%Y')}*
"""
    
    return document


# Alias for compatibility
def get_master_document_template(project: Dict[str, Any]) -> str:
    """Alias for generate_master_project_document"""
    return generate_master_project_document(project)
