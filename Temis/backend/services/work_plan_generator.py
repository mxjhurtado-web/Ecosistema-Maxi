#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Work Plan & Capacity Generator Service for TEMIS
Calculates working days, capacity hours, and generates structured Sprints + Scrum Backlog
using Gemini 2.5 Flash AI with deterministic fallback and Google Sheets synchronization.
"""

import json
import logging
import datetime
from typing import Dict, Any, List, Optional, Tuple
import os

logger = logging.getLogger(__name__)


def calculate_working_days(start_date_str: str, end_date_str: str, mode: str = "mon_fri") -> int:
    """
    Calculate number of working days between two dates.
    mode:
      - 'mon_fri': Monday to Friday (5 days/week)
      - 'mon_sat': Monday to Saturday (6 days/week)
      - 'full_week': All 7 days/week
    """
    try:
        start = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
        if start > end:
            return 0
        
        cur = start
        days = 0
        while cur <= end:
            w = cur.weekday()  # 0: Monday, 6: Sunday
            if mode == "mon_fri":
                if w < 5:
                    days += 1
            elif mode == "mon_sat":
                if w < 6:
                    days += 1
            else:  # full_week
                days += 1
            cur += datetime.timedelta(days=1)
        return max(1, days)
    except Exception:
        return 230  # Default ~11 months standard


def generate_local_work_plan(
    project_name: str,
    project_purpose: str,
    activities_description: str,
    start_date_str: str,
    end_date_str: str,
    daily_hours: int = 8,
    work_days_mode: str = "mon_fri"
) -> Dict[str, Any]:
    """
    Deterministic generation of Sprints and Backlog items adjusted to available capacity.
    """
    working_days = calculate_working_days(start_date_str, end_date_str, work_days_mode)
    total_capacity = working_days * daily_hours
    
    # Standard 2-week sprints (10 working days per sprint in mon_fri)
    days_per_sprint = 10 if work_days_mode == "mon_fri" else 12
    num_sprints = max(2, min(10, working_days // days_per_sprint))
    
    try:
        start_dt = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_dt = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except Exception:
        start_dt = datetime.date(2026, 1, 16)
        end_dt = datetime.date(2026, 12, 4)

    total_duration_days = (end_dt - start_dt).days or 300
    sprint_duration_days = max(7, total_duration_days // num_sprints)

    default_modules = [
        ("Diagnóstico & Arquitectura", "Definición del modelo AS-IS, requerimientos y diseño de arquitectura base.", "Hito 1: Charter & AS-IS Aprobado"),
        ("Diseño BPMN & SIPOC", "Mapeo de actividades, compuertas de decisión y matriz SIPOC Six Sigma.", "Hito 2: SIPOC Validado"),
        ("Core & Integraciones", "Desarrollo de servicios de backend, APIs REST y sincronización de datos.", "Hito 3: Conexión de Datos Operativa"),
        ("UI/UX & Espacio de Trabajo", "Construcción de interfaz interactiva, lienzo vectorial y dashboards.", "Hito 4: Prototipo Funcional"),
        ("Gobernanza & Auditoría IA", "Motor de validación de reglas de calidad, daily logs y reportes automatizados.", "Hito 5: Auditoría IA Activa"),
        ("Pruebas & Control de Calidad", "Pruebas de estrés, homologación con usuarios clave y validación de SLA.", "Hito 6: Certificación QA"),
        ("Despliegue & Capacitación", "Puesta en producción, documentación oficial y entrega a operaciones.", "Hito 7: Cierre y Go-Live")
    ]

    sprints = []
    backlog_items = []
    item_counter = 1

    for s_idx in range(num_sprints):
        s_num = f"Sprint {s_idx + 1:02d}"
        s_start = start_dt + datetime.timedelta(days=s_idx * sprint_duration_days)
        s_end = start_dt + datetime.timedelta(days=(s_idx + 1) * sprint_duration_days - 1)
        if s_idx == num_sprints - 1 or s_end > end_dt:
            s_end = end_dt

        mod_info = default_modules[s_idx % len(default_modules)]
        mod_name = mod_info[0]
        mod_obj = mod_info[1]
        mod_milestone = mod_info[2]

        sprint_sp = 0
        sprint_hours = 0

        # Create 3-4 standard tasks for this sprint
        tasks = [
            (f"Especificación técnica y diseño de {mod_name.lower()}", 5, 20, "Tech Lead / PM", "Alta", "Documento de Especificación"),
            (f"Implementación funcional del módulo {mod_name.lower()}", 8, 35, "Full-Stack Dev", "Alta", "Código / Funcionalidad"),
            (f"Validación de reglas de negocio y gobernanza de {mod_name.lower()}", 3, 15, "QA / Analista", "Media", "Matriz de Pruebas"),
            (f"Documentación de entregables y sync con Google Workspace", 2, 10, "PM / Analista", "Media", "Acta de Entregable")
        ]

        for t_title, sp_val, hrs_val, role, prio, deliv in tasks:
            sprint_sp += sp_val
            sprint_hours += hrs_val
            backlog_items.append({
                "item_id": str(item_counter),
                "module": mod_name,
                "user_story": f"Como equipo, requerimos {t_title.lower()} para {project_name}.",
                "sprint": s_num,
                "story_points": sp_val,
                "hours_estimated": hrs_val,
                "start_date": s_start.strftime("%Y-%m-%d"),
                "end_date": s_end.strftime("%Y-%m-%d"),
                "role": role,
                "priority": prio,
                "deliverable": deliv,
                "status": "Planificado" if s_idx > 0 else "En Progreso"
            })
            item_counter += 1

        sprints.append({
            "sprint_id": s_num,
            "period": f"{s_start.strftime('%Y-%m-%d')} al {s_end.strftime('%Y-%m-%d')}",
            "objective": mod_obj,
            "modules": mod_name,
            "milestone": mod_milestone,
            "status": "In Progress" if s_idx == 0 else "Planned",
            "story_points": sprint_sp,
            "hours_estimated": sprint_hours
        })

    return {
        "project_name": project_name,
        "working_days": working_days,
        "total_capacity_hours": total_capacity,
        "daily_hours": daily_hours,
        "work_days_mode": work_days_mode,
        "sprints": sprints,
        "backlog_items": backlog_items
    }


def generate_work_plan_with_gemini(
    project_name: str,
    project_purpose: str,
    activities_description: str,
    start_date_str: str,
    end_date_str: str,
    daily_hours: int = 8,
    work_days_mode: str = "mon_fri",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate professional Work Plan & Sprints using Gemini 2.5 Flash with capacity awareness.
    """
    working_days = calculate_working_days(start_date_str, end_date_str, work_days_mode)
    total_capacity = working_days * daily_hours

    if not api_key:
        try:
            from config.config import get_gemini_api_key
            api_key = get_gemini_api_key()
        except Exception:
            api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return generate_local_work_plan(
            project_name, project_purpose, activities_description,
            start_date_str, end_date_str, daily_hours, work_days_mode
        )

    try:
        from backend.services.gemini_service import GeminiChatService
        gemini = GeminiChatService(api_key=api_key)

        prompt = f"""Eres un Project Manager y Agile Coach Senior certificado en Scrum y Six Sigma.
Tu tarea es generar la PLANEACIÓN Y PLAN DE TRABAJO TÉCNICO integral para el siguiente proyecto corporativo, respetando las fechas y la capacidad de horas disponibles.

DATOS DEL PROYECTO:
- Nombre del Proyecto: {project_name}
- Propósito: {project_purpose}
- Descripción del Alcance y Actividades: {activities_description or 'Implementación y estandarización integral del proceso operativo, digitalización, gobernanza y automatización.'}
- Fecha de Inicio: {start_date_str}
- Fecha de Término: {end_date_str}
- Días Hábiles Calculados: {working_days} días
- Horas Laborables por Día: {daily_hours} horas/día
- Régimen Semanal: {work_days_mode}
- Capacidad Total de Horas Disponibles: {total_capacity} horas

INSTRUCCIONES DE PLANIFICACIÓN:
1. Divide el horizonte en Sprints consecutivos (ej: Sprint 01 a Sprint 06 o hasta 10, según la duración de las fechas).
2. Para cada Sprint, define: sprint_id (Sprint 01..N), period (fechas YYYY-MM-DD al YYYY-MM-DD), objective, modules, milestone, status (Sprint 01 como 'In Progress', los demás 'Planned').
3. Para el Backlog Técnico, genera una lista detallada de tareas / Historias de Usuario (mínimo 15-30 tareas):
   - item_id: "1", "2", "3"...
   - module: Nombre del módulo/épica
   - user_story: Redacción clara ("Como [rol], quiero [funcionalidad] para [beneficio]")
   - sprint: Sprint asignado ("Sprint 01", "Sprint 02"...)
   - story_points: Escala Fibonacci (1, 2, 3, 5, 8, 13)
   - hours_estimated: Horas estimadas coherentes
   - start_date y end_date: Fechas dentro del periodo del sprint correspondiente
   - role: Rol sugerido (Tech Lead, Full-Stack Dev, QA Tester, Analista de Procesos, Project Manager)
   - priority: "Alta", "Media", "Baja"
   - deliverable: Entregable tangible (ej: "Mapeo SIPOC en Excel", "API REST en FastAPI", "Manual de Políticas", "Dashboard Reflex")
   - status: "Planificado"

OUTPUT REQUERIDO (JSON PURO):
{{
  "sprints": [
    {{
      "sprint_id": "Sprint 01",
      "period": "{start_date_str} al YYYY-MM-DD",
      "objective": "Objetivo principal del sprint",
      "modules": "Módulos involucrados",
      "milestone": "Hito de entrega",
      "status": "In Progress",
      "story_points": 25,
      "hours_estimated": 80
    }}
  ],
  "backlog_items": [
    {{
      "item_id": "1",
      "module": "Diagnóstico & Mapeo",
      "user_story": "Como Analista, quiero mapear el flujo AS-IS para identificar cuellos de botella.",
      "sprint": "Sprint 01",
      "story_points": 5,
      "hours_estimated": 20,
      "start_date": "{start_date_str}",
      "end_date": "YYYY-MM-DD",
      "role": "Analista de Procesos",
      "priority": "Alta",
      "deliverable": "Diagrama de Flujo AS-IS",
      "status": "Planificado"
    }}
  ]
}}

Responde ÚNICAMENTE con el objeto JSON válido sin bloques markdown extra."""

        response = gemini.get_structured_response(prompt, max_tokens=7000)
        
        # Clean response string
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        data = json.loads(cleaned)
        if "sprints" in data and "backlog_items" in data:
            data["project_name"] = project_name
            data["working_days"] = working_days
            data["total_capacity_hours"] = total_capacity
            data["daily_hours"] = daily_hours
            data["work_days_mode"] = work_days_mode
            return data
        else:
            return generate_local_work_plan(
                project_name, project_purpose, activities_description,
                start_date_str, end_date_str, daily_hours, work_days_mode
            )

    except Exception as e:
        logger.warning(f"Gemini work plan generation failed, using local engine: {e}")
        return generate_local_work_plan(
            project_name, project_purpose, activities_description,
            start_date_str, end_date_str, daily_hours, work_days_mode
        )


def sync_plan_to_google_sheet(
    sheet_id: str,
    sprints: List[Dict[str, Any]],
    backlog_items: List[Dict[str, Any]]
) -> Tuple[bool, str]:
    """
    Write sprints and backlog items to the project's Google Sheet using Service Account credentials.
    Updates 'Agenda Ejecutiva' and 'Backlog Scrum Técnico TEMIS' tabs.
    """
    try:
        import base64
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from config.config import SA_JSON_B64

        sa_info = json.loads(base64.b64decode(SA_JSON_B64).decode("utf-8"))
        creds = service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        service = build("sheets", "v4", credentials=creds)

        # 1. Update Agenda Ejecutiva
        agenda_rows = [
            ["ID Sprint", "Periodo Estimado", "Objetivo Principal del Sprint", "Módulos / Épicas Involucradas", "Hito de Entrega", "Estado", "Story Points Estimados", "Horas Estimadas"]
        ]
        for s in sprints:
            agenda_rows.append([
                s.get("sprint_id", ""),
                s.get("period", ""),
                s.get("objective", ""),
                s.get("modules", ""),
                s.get("milestone", ""),
                s.get("status", "Planned"),
                s.get("story_points", 0),
                s.get("hours_estimated", 0)
            ])

        # Get existing sheet tab titles
        meta = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheet_titles = [sheet["properties"]["title"] for sheet in meta.get("sheets", [])]
        
        agenda_tab = next((t for t in sheet_titles if "Agenda" in t), "Agenda Ejecutiva")
        backlog_tab = next((t for t in sheet_titles if "Backlog" in t), "Backlog Scrum Técnico TEMIS")

        # Write to Agenda tab
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"'{agenda_tab}'!A4:H" + str(len(agenda_rows) + 4),
            valueInputOption="USER_ENTERED",
            body={"values": agenda_rows}
        ).execute()

        # 2. Update Backlog Scrum Técnico TEMIS
        backlog_rows = [
            ["Item ID", "Módulo / Épica", "Historia de Usuario / Tarea Técnica", "Sprint", "Story Points", "Horas Estimadas", "Fecha Inicio", "Fecha Fin", "Responsable / Rol", "Prioridad", "Entregable", "Estado"]
        ]
        for b in backlog_items:
            backlog_rows.append([
                b.get("item_id", ""),
                b.get("module", ""),
                b.get("user_story", ""),
                b.get("sprint", ""),
                b.get("story_points", 0),
                b.get("hours_estimated", 0),
                b.get("start_date", ""),
                b.get("end_date", ""),
                b.get("role", ""),
                b.get("priority", "Media"),
                b.get("deliverable", ""),
                b.get("status", "Planificado")
            ])

        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range="'Backlog Scrum Técnico TEMIS'!A1:L" + str(len(backlog_rows) + 2),
            valueInputOption="USER_ENTERED",
            body={"values": backlog_rows}
        ).execute()

        return True, "Sincronización exitosa en Google Sheets"
    except Exception as e:
        logger.error(f"Error syncing to Google Sheet: {e}")
        return False, str(e)
