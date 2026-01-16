#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Document templates for TEMIS - Aligned with Real Framework
Based on: Framework gestión de proyectos.pdf + Proyecto Max.docx
"""

from datetime import date

# Import master document generator
from desktop.core.master_document_template import generate_master_project_document


# ============================================================================
# FASE 1: PRIORIZACIÓN DEL PORTAFOLIO + DIAGNÓSTICO
# ============================================================================

PHASE_1_DELIVERABLES = {
    "📄 Documento Maestro del Proyecto": {
        "description": "Documento completo del proyecto (Formato Temis) - Se actualiza automáticamente",
        "type": "document",
        "required_inputs": [],
        "template_function": "generate_master_project_document",
        "auto_update": True
    },
    "Priorización del Portafolio": {
        "description": "Matriz de priorización de proyectos/iniciativas",
        "type": "spreadsheet",
        "required_inputs": ["criterios", "proyectos", "pesos", "scores"],
        "template_function": None  # Excel template
    },
    "Diagnóstico AS-IS": {
        "description": "Análisis de situación actual",
        "type": "document",
        "required_inputs": ["situacion_actual", "problemas", "oportunidades", "restricciones"],
        "template_function": "get_diagnostico_template"
    },
    "Mapa de Personas": {
        "description": "Identificación y análisis de stakeholders",
        "type": "document",
        "required_inputs": ["stakeholders", "interes", "influencia", "estrategia"],
        "template_function": "get_stakeholders_template"
    },
    "Journey Map": {
        "description": "Mapa de experiencia del usuario (si aplica UX)",
        "type": "document",
        "optional": True,
        "required_inputs": ["etapas", "puntos_dolor", "oportunidades", "emociones"],
        "template_function": "get_journey_map_template"
    }
}

# ============================================================================
# FASE 2: INICIO (CHARTER + VISIÓN)
# ============================================================================

PHASE_2_DELIVERABLES = {
    "Project Charter v2": {
        "description": "Documento de constitución del proyecto",
        "type": "document",
        "required_inputs": ["objetivos", "alcance", "sponsor", "pm", "presupuesto", "cronograma"],
        "template_function": "get_project_charter_v2_template"
    },
    "Visión del Producto": {
        "description": "Visión y objetivos del producto",
        "type": "document",
        "required_inputs": ["vision", "objetivos_negocio", "usuarios_objetivo", "propuesta_valor"],
        "template_function": "get_vision_template"
    },
    "Roles y Gobernanza": {
        "description": "Definición de roles y estructura de gobernanza",
        "type": "document",
        "required_inputs": ["sponsor", "project_lead", "po", "agile_lead", "team", "comite"],
        "template_function": "get_governance_template"
    },
    "Alcance Inicial": {
        "description": "Definición de alcance del proyecto",
        "type": "document",
        "required_inputs": ["incluido", "no_incluido", "supuestos", "restricciones"],
        "template_function": "get_scope_template"
    }
}

# ============================================================================
# FASE 3: PLANIFICACIÓN
# ============================================================================

PHASE_3_DELIVERABLES = {
    "Roadmap": {
        "description": "Roadmap del proyecto con hitos principales",
        "type": "document",
        "required_inputs": ["hitos", "timeline", "dependencias", "releases"],
        "template_function": "get_roadmap_template"
    },
    "Backlog Priorizado": {
        "description": "Product backlog priorizado",
        "type": "spreadsheet",
        "required_inputs": ["epicas", "user_stories", "prioridad", "estimacion", "valor"],
        "template_function": None  # Excel template
    },
    "Arquitectura de Experiencia": {
        "description": "Diseño de arquitectura de experiencia (UX)",
        "type": "presentation",
        "required_inputs": ["flujos", "wireframes", "componentes", "patrones"],
        "template_function": None  # PowerPoint template
    },
    "Product Goal": {
        "description": "Objetivo del producto y métricas de éxito",
        "type": "document",
        "required_inputs": ["objetivo_producto", "metricas_exito", "kpis"],
        "template_function": "get_product_goal_template"
    },
    "WBS": {
        "description": "Work Breakdown Structure",
        "type": "document",
        "required_inputs": ["paquetes_trabajo", "entregables", "responsables"],
        "template_function": "get_wbs_template"
    }
}

# ============================================================================
# FASE 4: EJECUCIÓN ITERATIVA (POR SPRINT)
# ============================================================================

PHASE_4_DELIVERABLES_PER_SPRINT = {
    "Sprint Planning": {
        "description": "Planificación del sprint",
        "type": "document",
        "required_inputs": ["sprint_goal", "user_stories", "capacidad", "compromisos"],
        "template_function": "get_sprint_planning_template"
    },
    "Incremento de Producto": {
        "description": "Código/funcionalidad entregada",
        "type": "code",
        "required_inputs": ["repo_link", "branch", "pr_link", "features"],
        "template_function": None
    },
    "QA Report": {
        "description": "Reporte de calidad y testing",
        "type": "document",
        "required_inputs": ["test_cases", "bugs", "coverage", "regression"],
        "template_function": "get_qa_report_template"
    },
    "UX Testing": {
        "description": "Pruebas de experiencia de usuario",
        "type": "document",
        "required_inputs": ["usuarios_testeados", "insights", "mejoras", "evidencias"],
        "template_function": "get_ux_testing_template"
    },
    "Sprint Review": {
        "description": "Revisión del sprint con stakeholders",
        "type": "presentation",
        "required_inputs": ["demo", "feedback", "next_steps", "impedimentos"],
        "template_function": None  # PowerPoint template
    },
    "Sprint Retrospective": {
        "description": "Retrospectiva del equipo",
        "type": "document",
        "required_inputs": ["que_salio_bien", "que_mejorar", "acciones", "compromisos"],
        "template_function": "get_retrospective_template"
    }
}

# ============================================================================
# FASE 5: MONITOREO Y CONTROL
# ============================================================================

PHASE_5_DELIVERABLES = {
    "Semáforo del Proyecto": {
        "description": "Indicadores de salud del proyecto (Alcance/Tiempo/Costo/Calidad)",
        "type": "dashboard",
        "auto_update": True,  # Se actualiza automáticamente desde daily logs
        "required_inputs": ["alcance_status", "tiempo_status", "costo_status", "calidad_status"],
        "template_function": "get_semaforo_template"
    },
    "Tabla de Hitos": {
        "description": "Seguimiento de hitos (planeado vs real)",
        "type": "spreadsheet",
        "auto_update": True,
        "required_inputs": ["hito", "fecha_planeada", "fecha_real", "status", "responsable"],
        "template_function": None
    },
    "UX Metrics": {
        "description": "Métricas de experiencia de usuario",
        "type": "document",
        "required_inputs": ["metricas", "resultados", "tendencias"],
        "template_function": "get_ux_metrics_template"
    },
    "Matriz de Riesgos": {
        "description": "Registro y seguimiento de riesgos",
        "type": "spreadsheet",
        "auto_update": True,  # Se actualiza desde daily logs
        "required_inputs": ["riesgo", "probabilidad", "impacto", "mitigacion", "owner", "status"],
        "template_function": None
    },
    "Control de Cambios": {
        "description": "Registro de cambios al proyecto",
        "type": "spreadsheet",
        "required_inputs": ["id", "descripcion", "impacto", "decision", "aprobador", "fecha"],
        "template_function": None
    },
    "Solicitudes al Comité": {
        "description": "Solicitudes formales al comité de stakeholders",
        "type": "document",
        "required_inputs": ["solicitud", "justificacion", "impacto", "decision"],
        "template_function": "get_committee_request_template"
    }
}

# ============================================================================
# FASE 6: MEJORA CONTINUA
# ============================================================================

PHASE_6_DELIVERABLES = {
    "Beneficios y Valor Entregado": {
        "description": "Análisis de beneficios y valor generado",
        "type": "document",
        "required_inputs": ["beneficios_esperados", "beneficios_reales", "roi", "valor_negocio"],
        "template_function": "get_benefits_template"
    },
    "Resultados UX": {
        "description": "Resultados de experiencia de usuario",
        "type": "document",
        "required_inputs": ["metricas_ux", "satisfaccion", "usabilidad", "mejoras"],
        "template_function": "get_ux_results_template"
    },
    "Plan de Transición": {
        "description": "Plan de transición a operación",
        "type": "document",
        "required_inputs": ["actividades", "responsables", "fechas", "criterios_exito"],
        "template_function": "get_transition_plan_template"
    },
    "Retrospectiva Final": {
        "description": "Retrospectiva final del proyecto",
        "type": "document",
        "required_inputs": ["logros", "desafios", "aprendizajes", "mejoras_futuras"],
        "template_function": "get_final_retro_template"
    }
}

# ============================================================================
# FASE 7: CIERRE
# ============================================================================

PHASE_7_DELIVERABLES = {
    "Lecciones Aprendidas": {
        "description": "Documentación de lecciones aprendidas",
        "type": "document",
        "required_inputs": ["procesos", "tecnologia", "ux", "equipo", "recomendaciones"],
        "template_function": "get_lessons_learned_template"
    },
    "Manual de Usuario": {
        "description": "Manual de usuario del sistema",
        "type": "manual",
        "auto_generate": True,  # Se genera con Gemini
        "required_inputs": ["funcionalidades", "pantallas", "flujos", "faqs"],
        "template_function": "get_user_manual_template"
    },
    "Guía Técnica": {
        "description": "Documentación técnica del sistema",
        "type": "manual",
        "auto_generate": True,  # Se genera con Gemini
        "required_inputs": ["arquitectura", "componentes", "apis", "deployment"],
        "template_function": "get_technical_guide_template"
    },
    "Innovación y Optimización": {
        "description": "Propuestas de innovación y optimización",
        "type": "document",
        "required_inputs": ["innovaciones", "optimizaciones", "roadmap_futuro"],
        "template_function": "get_innovation_template"
    },
    "Presentación de Cierre": {
        "description": "Presentación final del proyecto",
        "type": "presentation",
        "required_inputs": ["resumen", "logros", "metricas", "next_steps"],
        "template_function": None  # PowerPoint template
    },
    "Transferencia de Conocimiento": {
        "description": "Documento de transferencia de conocimiento",
        "type": "document",
        "required_inputs": ["conocimientos_clave", "contactos", "documentacion", "soporte"],
        "template_function": "get_knowledge_transfer_template"
    }
}

# ============================================================================
# CONSOLIDADO: TODAS LAS FASES
# ============================================================================

ALL_PHASE_DELIVERABLES = {
    1: PHASE_1_DELIVERABLES,
    2: PHASE_2_DELIVERABLES,
    3: PHASE_3_DELIVERABLES,
    4: PHASE_4_DELIVERABLES_PER_SPRINT,
    5: PHASE_5_DELIVERABLES,
    6: PHASE_6_DELIVERABLES,
    7: PHASE_7_DELIVERABLES
}


# ============================================================================
# TEMPLATE FUNCTIONS (Ejemplos - se expandirán)
# ============================================================================

def get_project_charter_v2_template(project_name: str, **kwargs) -> str:
    """Project Charter v2 - Aligned with Framework"""
    sponsor = kwargs.get('sponsor', '[Sponsor]')
    pm = kwargs.get('pm', '[Project Manager]')
    
    return f"""# PROJECT CHARTER v2.0
## {project_name}

### 1. INFORMACIÓN GENERAL
- **Proyecto**: {project_name}
- **Fecha**: {date.today().strftime('%Y-%m-%d')}
- **Sponsor**: {sponsor}
- **Project Lead**: {pm}
- **Versión**: 2.0

### 2. VISIÓN Y OBJETIVOS
**Visión**: [Descripción de la visión del proyecto]

**Objetivos**:
1. [Objetivo 1]
2. [Objetivo 2]
3. [Objetivo 3]

### 3. ALCANCE
**Incluido**:
- [Item 1]
- [Item 2]

**No Incluido**:
- [Item 1]
- [Item 2]

### 4. STAKEHOLDERS
| Nombre | Rol | Interés | Influencia | Estrategia |
|--------|-----|---------|------------|------------|
| {sponsor} | Sponsor | Alto | Alto | Mantener satisfecho |

### 5. CRONOGRAMA DE ALTO NIVEL
| Fase | Inicio | Fin | Duración |
|------|--------|-----|----------|
| 1. Diagnóstico | [Fecha] | [Fecha] | [X sem] |
| 2. Inicio | [Fecha] | [Fecha] | [X sem] |
| 3. Planificación | [Fecha] | [Fecha] | [X sem] |
| 4. Ejecución | [Fecha] | [Fecha] | [X sem] |
| 5. Monitoreo | [Fecha] | [Fecha] | [X sem] |
| 6. Mejora Continua | [Fecha] | [Fecha] | [X sem] |
| 7. Cierre | [Fecha] | [Fecha] | [X sem] |

### 6. PRESUPUESTO
- **Total**: $[Monto]
- **Recursos Humanos**: $[Monto]
- **Infraestructura**: $[Monto]
- **Contingencia (10%)**: $[Monto]

### 7. RIESGOS PRINCIPALES
| ID | Riesgo | Prob | Impacto | Mitigación |
|----|--------|------|---------|------------|
| R-001 | [Riesgo] | [A/M/B] | [A/M/B] | [Mitigación] |

### 8. CRITERIOS DE ÉXITO
1. [Criterio medible 1]
2. [Criterio medible 2]
3. [Criterio medible 3]

### 9. APROBACIONES
| Rol | Nombre | Firma | Fecha |
|-----|--------|-------|-------|
| Sponsor | {sponsor} | _______ | _____ |
| Project Lead | {pm} | _______ | _____ |

---
*Generado por TEMIS - {date.today().strftime('%Y-%m-%d')}*
"""

# Más templates se agregarán según se necesiten...

def get_stakeholders_template(project_name: str, **kwargs) -> str:
    """Mapa de Personas / Stakeholders Template"""
    return f"""# MAPA DE PERSONAS - STAKEHOLDERS
## {project_name}

**Fecha**: {date.today().strftime('%Y-%m-%d')}

### Identificación de Stakeholders

| Stakeholder | Rol | Interés | Influencia | Estrategia de Gestión |
|-------------|-----|---------|------------|----------------------|
| [Nombre] | [Rol] | Alto/Medio/Bajo | Alto/Medio/Bajo | [Estrategia] |
| [Nombre] | [Rol] | Alto/Medio/Bajo | Alto/Medio/Bajo | [Estrategia] |

### Matriz de Poder-Interés

**Alto Poder, Alto Interés (Gestionar de Cerca)**:
- [Stakeholder 1]
- [Stakeholder 2]

**Alto Poder, Bajo Interés (Mantener Satisfecho)**:
- [Stakeholder 1]

**Bajo Poder, Alto Interés (Mantener Informado)**:
- [Stakeholder 1]

**Bajo Poder, Bajo Interés (Monitorear)**:
- [Stakeholder 1]

### Arquetipos de Usuario

#### Arquetipo 1: [Nombre]
- **Descripción**: [Descripción del perfil]
- **Necesidades Principales**: 
  - [Necesidad 1]
  - [Necesidad 2]
- **Puntos de Dolor**:
  - [Pain point 1]
  - [Pain point 2]
- **Objetivos**:
  - [Objetivo 1]
  - [Objetivo 2]

---
*Generado por TEMIS - {date.today().strftime('%Y-%m-%d')}*
"""

def get_diagnostico_template(project_name: str, **kwargs) -> str:
    """Diagnóstico AS-IS Template"""
    return f"""# DIAGNÓSTICO AS-IS
## {project_name}

**Fecha**: {date.today().strftime('%Y-%m-%d')}

### 1. SITUACIÓN ACTUAL

**Problemática / Necesidad Detectada**:
[Describir la problemática o necesidad que motiva el proyecto]

**Contexto del Negocio**:
[Describir el contexto actual del negocio]

### 2. ANÁLISIS DE PROCESOS ACTUALES (AS-IS)

**Responsable**: Responsable de Procesos

**Descripción del Flujo Actual**:
[Describir cómo funcionan los procesos actualmente]

**Puntos de Dolor (Pain Points)**:
1. [Pain point 1]
2. [Pain point 2]
3. [Pain point 3]

**Ineficiencias Identificadas**:
- [Ineficiencia 1]
- [Ineficiencia 2]

### 3. OPORTUNIDADES DE MEJORA

1. **[Oportunidad 1]**
   - Descripción: [Detalles]
   - Impacto Estimado: [Alto/Medio/Bajo]

2. **[Oportunidad 2]**
   - Descripción: [Detalles]
   - Impacto Estimado: [Alto/Medio/Bajo]

### 4. RESTRICCIONES Y LIMITACIONES

**Restricciones Técnicas**:
- [Restricción 1]
- [Restricción 2]

**Restricciones de Negocio**:
- [Restricción 1]
- [Restricción 2]

**Restricciones de Recursos**:
- [Restricción 1]
- [Restricción 2]

### 5. CONCLUSIONES

[Resumen de hallazgos principales y recomendaciones]

---
*Generado por TEMIS - {date.today().strftime('%Y-%m-%d')}*
"""

def get_journey_map_template(project_name: str, **kwargs) -> str:
    """Customer Journey Map Template"""
    return f"""# CUSTOMER JOURNEY MAP
## {project_name}

**Fecha**: {date.today().strftime('%Y-%m-%d')}

### Mapa de Experiencia del Usuario

**Usuario/Persona**: [Nombre del arquetipo]

| Etapa | Acciones | Puntos de Contacto | Pensamientos | Emociones | Pain Points | Oportunidades |
|-------|----------|-------------------|--------------|-----------|-------------|---------------|
| **Descubrimiento** | [Acciones] | [Touchpoints] | [Pensamientos] | 😐 | [Dolores] | [Oportunidades] |
| **Consideración** | [Acciones] | [Touchpoints] | [Pensamientos] | 🤔 | [Dolores] | [Oportunidades] |
| **Decisión** | [Acciones] | [Touchpoints] | [Pensamientos] | 😊 | [Dolores] | [Oportunidades] |
| **Uso** | [Acciones] | [Touchpoints] | [Pensamientos] | 😃 | [Dolores] | [Oportunidades] |
| **Lealtad** | [Acciones] | [Touchpoints] | [Pensamientos] | 🎉 | [Dolores] | [Oportunidades] |

### Momentos de la Verdad

**Momento Crítico 1**: [Descripción]
- **Impacto**: [Alto/Medio/Bajo]
- **Acción Requerida**: [Qué hacer]

**Momento Crítico 2**: [Descripción]
- **Impacto**: [Alto/Medio/Bajo]
- **Acción Requerida**: [Qué hacer]

### Insights Clave

1. [Insight 1]
2. [Insight 2]
3. [Insight 3]

### Recomendaciones

1. [Recomendación 1]
2. [Recomendación 2]
3. [Recomendación 3]

---
*Generado por TEMIS - {date.today().strftime('%Y-%m-%d')}*
"""
