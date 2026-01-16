#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Daily Log template for TEMIS
"""

from datetime import date


def get_daily_log_template(project_name: str, user_name: str, log_date: date = None) -> str:
    """Get daily log template"""
    if log_date is None:
        log_date = date.today()
    
    return f"""# Documento Diario TEMIS
**Proyecto**: {project_name}  
**Fecha**: {log_date.strftime('%Y-%m-%d')}  
**Autor**: {user_name}

---

## 📝 Resumen del Día
[Breve resumen de lo realizado hoy - 2-3 líneas]

---

## ✅ Tareas Completadas
<!-- entry_id: TASK-001 | type: task | status: done | owner: @{user_name.split()[0].lower()} -->
- [x] Descripción de la tarea completada
  - **Detalles**: [Información adicional]
  - **Links**: [URLs relevantes]

---

## 🔄 Tareas en Progreso
<!-- entry_id: TASK-002 | type: task | status: in_progress | owner: @{user_name.split()[0].lower()} | due: {log_date.strftime('%Y-%m-%d')} -->
- [ ] Tarea que sigue en progreso
  - **Progreso**: 60%
  - **Bloqueadores**: [Si hay alguno]

---

## 📋 Tareas Nuevas
<!-- entry_id: TASK-003 | type: task | status: todo | owner: @{user_name.split()[0].lower()} | due: {log_date.strftime('%Y-%m-%d')} | priority: high -->
- [ ] Nueva tarea identificada
  - **Descripción**: [Detalles]
  - **Estimación**: [Tiempo estimado]

---

## ⚠️ Riesgos Identificados
<!-- entry_id: RISK-001 | type: risk | impact: high | probability: medium -->
**Riesgo**: [Título del riesgo]
- **Descripción**: [Detalles del riesgo]
- **Impacto**: Alto/Medio/Bajo
- **Probabilidad**: Alta/Media/Baja
- **Mitigación**: [Plan de mitigación]

---

## 🎯 Decisiones Tomadas
<!-- entry_id: DEC-001 | type: decision | decided_by: @{user_name.split()[0].lower()} -->
**Decisión**: [Título de la decisión]
- **Contexto**: [Por qué se tomó]
- **Alternativas consideradas**: [Opciones descartadas]
- **Impacto**: [Consecuencias esperadas]

---

## 📌 Notas y Observaciones
<!-- entry_id: NOTE-001 | type: note -->
- [Observación o nota importante]
- [Otra nota]

---

## 🔗 Links y Referencias
- [Documento X](https://drive.google.com/...)
- [Jira Ticket](https://...)

---

## 📅 Próximos Pasos (Mañana)
1. [Acción 1]
2. [Acción 2]
3. [Acción 3]
"""
