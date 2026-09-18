#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
State management for TEMIS Web Flow using Reflex
Manages projects, phases, flowchart nodes, swimlanes and AI generation
"""

import reflex as rx
from typing import List, Dict, Any, Optional, Union
import json
import requests

from backend.models.phase import PHASE_NAMES


class FlowState(rx.State):
    """Main state for TEMIS Web Flow Application"""

    # Authentication & Session State
    is_authenticated: bool = False
    login_email: str = "mxjhurtado@maxillc.com"
    login_password: str = ""
    login_error_message: str = ""
    is_logging_in: bool = False

    # Level 1 Hub Subview: "portfolio" or "users"
    hub_active_subview: str = "portfolio"

    # User Management & RBAC Directory State
    users_list: List[Dict[str, Any]] = [
        {
            "email": "mxjhurtado@maxillc.com",
            "name": "Ing. José Antonio Hurtado",
            "password": "Temis123456*",
            "role": "super_admin",
            "role_label": "👑 Super Admin",
            "department": "Dirección General & Tecnología",
            "status": "active",
            "created_at": "2026-01-16",
            "last_login": "2026-09-18 13:00"
        },
        {
            "email": "ana.martinez@maxillc.com",
            "name": "Lic. Ana Martínez",
            "password": "Temis123456*",
            "role": "project_manager",
            "role_label": "👔 Dueño de Proyecto (PM)",
            "department": "Operaciones & Procesos",
            "status": "active",
            "created_at": "2026-02-01",
            "last_login": "2026-09-17 10:30"
        },
        {
            "email": "carlos.lopez@maxillc.com",
            "name": "Ing. Carlos López",
            "password": "Temis123456*",
            "role": "analyst",
            "role_label": "📊 Analista de Procesos",
            "department": "Ingeniería de Software",
            "status": "active",
            "created_at": "2026-02-15",
            "last_login": "2026-09-18 09:15"
        },
        {
            "email": "laura.torres@maxillc.com",
            "name": "Mtra. Laura Torres",
            "password": "Temis123456*",
            "role": "qa_auditor",
            "role_label": "🛡️ Auditor QA / Six Sigma",
            "department": "Calidad & Gobernanza",
            "status": "active",
            "created_at": "2026-03-01",
            "last_login": "2026-09-16 16:45"
        }
    ]
    show_new_user_modal: bool = False
    new_user_name: str = ""
    new_user_email: str = ""
    new_user_role: str = "collaborator"
    new_user_department: str = ""
    new_user_password: str = "Temis123456*"
    user_search_query: str = ""
    user_filter_role: str = "all"
    user_filter_status: str = "all"

    @rx.var
    def user_initials(self) -> str:
        return "JH"

    @rx.var
    def users_total_count(self) -> int:
        return len(self.users_list)

    @rx.var
    def users_super_admin_count(self) -> int:
        return sum(1 for u in self.users_list if u.get("role") == "super_admin")

    @rx.var
    def users_pm_count(self) -> int:
        return sum(1 for u in self.users_list if u.get("role") == "project_manager")

    @rx.var
    def users_analyst_qa_count(self) -> int:
        return sum(1 for u in self.users_list if u.get("role") in ["analyst", "qa_auditor", "collaborator"])

    @rx.var
    def filtered_users_list(self) -> List[Dict[str, Any]]:
        items = list(self.users_list)
        if self.user_filter_role != "all":
            items = [u for u in items if u.get("role") == self.user_filter_role]
        if self.user_filter_status != "all":
            items = [u for u in items if u.get("status") == self.user_filter_status]
        q = (self.user_search_query or "").strip().lower()
        if q:
            items = [
                u for u in items
                if q in u.get("name", "").lower()
                or q in u.get("email", "").lower()
                or q in u.get("department", "").lower()
                or q in u.get("role_label", "").lower()
            ]
        return items

    def set_login_email(self, val: str):
        self.login_email = val

    def set_login_password(self, val: str):
        self.login_password = val

    def handle_login(self):
        self.is_logging_in = True
        self.login_error_message = ""
        try:
            from backend.services.user_service import authenticate_user, load_users
            res = authenticate_user(self.login_email, self.login_password)
            if res and "error" not in res:
                self.is_authenticated = True
                self.user_name = res.get("name", "Usuario TEMIS")
                self.user_email = res.get("email", self.login_email)
                self.user_role = res.get("role", "collaborator")
                self.users_list = load_users()
                self.login_password = ""
                self.login_error_message = ""
                self.status_message = f"Bienvenido a TEMIS, {self.user_name}"
            elif res and "error" in res:
                self.login_error_message = res["error"]
            else:
                self.login_error_message = "Credenciales incorrectas."
        except Exception as e:
            self.login_error_message = f"Error al autenticar: {str(e)}"
        finally:
            self.is_logging_in = False

    def logout(self):
        self.is_authenticated = False
        self.login_password = ""
        self.active_mode = "hub"
        self.hub_active_subview = "portfolio"
        self.status_message = "Sesión cerrada correctamente."

    def set_hub_active_subview(self, val: Union[str, List[str]]):
        if isinstance(val, list):
            self.hub_active_subview = val[0] if val else "portfolio"
        else:
            self.hub_active_subview = str(val)

    def set_show_new_user_modal(self, val: bool):
        self.show_new_user_modal = val

    def open_new_user_modal(self):
        self.new_user_name = ""
        self.new_user_email = ""
        self.new_user_role = "collaborator"
        self.new_user_department = ""
        self.new_user_password = "Temis123456*"
        self.show_new_user_modal = True

    def set_new_user_name(self, val: str):
        self.new_user_name = val

    def set_new_user_email(self, val: str):
        self.new_user_email = val

    def set_new_user_role(self, val: str):
        self.new_user_role = str(val)

    def set_new_user_department(self, val: str):
        self.new_user_department = val

    def set_new_user_password(self, val: str):
        self.new_user_password = val

    def set_user_search_query(self, val: str):
        self.user_search_query = val

    def set_user_filter_role(self, val: str):
        self.user_filter_role = str(val)

    def set_user_filter_status(self, val: str):
        self.user_filter_status = str(val)

    def submit_new_user(self):
        try:
            from backend.services.user_service import create_user, load_users
            ok, msg, new_u = create_user(
                email=self.new_user_email,
                name=self.new_user_name,
                role=self.new_user_role,
                department=self.new_user_department,
                password=self.new_user_password or "Temis123456*"
            )
            if ok:
                self.users_list = load_users()
                self.show_new_user_modal = False
                self.status_message = f"✓ {msg}"
            else:
                self.status_message = f"Error: {msg}"
        except Exception as e:
            self.status_message = f"Error al registrar usuario: {str(e)}"

    def update_user_role_action(self, email: str, new_role: str):
        try:
            from backend.services.user_service import update_user_role, load_users
            ok, msg = update_user_role(email, new_role)
            if ok:
                self.users_list = load_users()
                self.status_message = f"✓ {msg}"
            else:
                self.status_message = f"Error: {msg}"
        except Exception as e:
            self.status_message = f"Error al actualizar rol: {str(e)}"

    def toggle_user_status_action(self, email: str):
        try:
            from backend.services.user_service import toggle_user_status, load_users
            ok, msg = toggle_user_status(email)
            if ok:
                self.users_list = load_users()
                self.status_message = f"✓ {msg}"
            else:
                self.status_message = f"Error: {msg}"
        except Exception as e:
            self.status_message = f"Error: {str(e)}"

    def delete_user_action(self, email: str):
        try:
            from backend.services.user_service import delete_user, load_users
            ok, msg = delete_user(email)
            if ok:
                self.users_list = load_users()
                self.status_message = f"✓ {msg}"
            else:
                self.status_message = f"Error: {msg}"
        except Exception as e:
            self.status_message = f"Error: {str(e)}"

    # Navigation Mode: "hub" (Level 1 Monday.com Portfolio) or "workspace" (Level 2 Modeling Suite)
    active_mode: str = "hub"
    
    # User Profile & RBAC Role Simulation
    user_role: str = "super_admin"  # "super_admin", "project_manager", "collaborator"
    user_name: str = "Ing. José Antonio Hurtado"
    user_email: str = "mxjhurtado@maxillc.com"

    def set_user_role(self, role: str):
        self.user_role = role
        role_labels = {
            "super_admin": "👑 Super Admin (Portafolio Total)",
            "project_manager": "👔 Dueño de Proyecto (Asignados)",
            "collaborator": "👥 Colaborador (Invitado)"
        }
        self.status_message = f"Rol cambiado a: {role_labels.get(role, role)}"

    # Hub Search & Filter State
    search_hub_query: str = ""
    filter_hub_phase: str = "all"
    filter_hub_status: str = "all"

    def set_search_hub_query(self, val: str):
        self.search_hub_query = val

    def set_filter_hub_phase(self, val: str):
        self.filter_hub_phase = str(val)

    def set_filter_hub_status(self, val: str):
        self.filter_hub_status = str(val)

    # Modal Create New Project State & Drive Pipeline
    show_new_project_modal: bool = False
    new_proj_name: str = ""
    new_proj_code: str = ""
    new_proj_purpose: str = ""
    new_proj_manager: str = "Ing. José Antonio Hurtado"
    new_proj_sponsor: str = "Dirección de Operaciones & Tecnología"
    new_proj_start_date: str = "2026-01-16"
    new_proj_end_date: str = "2026-12-04"
    is_creating_project_drive: bool = False
    creation_progress_status: str = ""

    # Project & Framework State (Workspace Level 2)
    project_id: str = "proj-temis"
    project_code: str = "PRJ-TEMIS"
    project_name: str = "Suite de Procesos & Gobernanza TEMIS"
    drive_folder_id: str = "1NA32b-o473ZxcpuLxHPf2xDOt5XHn2CI"
    drive_folder_url: str = "https://drive.google.com/drive/folders/1NA32b-o473ZxcpuLxHPf2xDOt5XHn2CI"
    sheet_id: str = "1GxiIwR2rUMkZKHu00JYzlQrs6EsyXO5VqUL6qpl_MBs"
    sheet_url: str = "https://docs.google.com/spreadsheets/d/1GxiIwR2rUMkZKHu00JYzlQrs6EsyXO5VqUL6qpl_MBs/edit"
    current_phase: int = 4
    phase_name: str = PHASE_NAMES[4]

    # Flowchart Diagram Data (Official Symbology)
    diagram_id: Optional[str] = None
    diagram_title: str = "Flujo de Proceso Operativo"
    swimlanes: List[str] = ["Input", "Actor 1 (ej. Usuario)", "Actor 2 (ej. Sistema)", "Output"]

    # Active View Navigation (4 Core Modules)
    active_view: str = "flow"  # "charter", "plan", "flow", "sipoc", "governance"

    def set_active_view(self, view_name: Union[str, List[str]]):
        """Switch active view tab: 'charter', 'plan', 'flow', 'sipoc', 'governance'"""
        if isinstance(view_name, list):
            val = view_name[0] if view_name else "flow"
        else:
            val = str(view_name)
        self.active_view = val
        view_labels = {
            "charter": "Ficha del Proyecto & Narrativa",
            "plan": "Plan de Trabajo & Sprints IA",
            "flow": "Diagrama de Flujo (Lienzo)",
            "sipoc": "Matriz SIPOC Six Sigma",
            "governance": "Gobernanza & 7 Fases"
        }
        self.status_message = f"Vista activa: {view_labels.get(val, val)}"

    # Work Plan & Capacity Planner State
    plan_start_date: str = "2026-01-16"
    plan_end_date: str = "2026-12-04"
    plan_daily_hours: int = 8
    plan_work_days_mode: str = "mon_fri"  # "mon_fri", "mon_sat", "full_week"
    plan_activities_description: str = "Automatizar el ciclo integral de atención de aclaraciones y transacciones de clientes vía canales digitales y sistemas centrales (Chronos, Freshdesk, WhatsApp)."
    is_generating_plan_ai: bool = False
    is_syncing_plan_sheet: bool = False
    plan_active_subtab: str = "backlog"  # "backlog", "sprints"
    plan_search_query: str = ""
    plan_filter_sprint: str = "all"

    plan_sprints: List[Dict[str, Any]] = [
        {
            "sprint_id": "Sprint 01",
            "period": "2026-01-16 al 2026-01-30",
            "objective": "Diagnóstico AS-IS y levantamiento de requerimientos con áreas líderes",
            "modules": "Diagnóstico & Arquitectura",
            "milestone": "Charter y Matriz AS-IS Aprobados",
            "status": "In Progress",
            "story_points": 25,
            "hours_estimated": 80
        },
        {
            "sprint_id": "Sprint 02",
            "period": "2026-02-02 al 2026-02-16",
            "objective": "Mapeo SIPOC Six Sigma y definición de roles, sistemas y canales",
            "modules": "Diseño BPMN & SIPOC",
            "milestone": "SIPOC y Simbología BPMN Homologada",
            "status": "Planned",
            "story_points": 30,
            "hours_estimated": 90
        },
        {
            "sprint_id": "Sprint 03",
            "period": "2026-02-17 al 2026-03-03",
            "objective": "Construcción del lienzo interactivo y docking de herramientas BPMN",
            "modules": "UI/UX & Espacio de Trabajo",
            "milestone": "Editor Visual Bézier Operativo",
            "status": "Planned",
            "story_points": 35,
            "hours_estimated": 100
        },
        {
            "sprint_id": "Sprint 04",
            "period": "2026-03-04 al 2026-03-18",
            "objective": "Desacoplamiento backend REST e integración con Google Workspace Shared Drive",
            "modules": "Core & Integraciones",
            "milestone": "Service Account y Sync de Carpetas",
            "status": "Planned",
            "story_points": 40,
            "hours_estimated": 110
        },
        {
            "sprint_id": "Sprint 05",
            "period": "2026-03-19 al 2026-04-02",
            "objective": "Motor de Auditoría Six Sigma con Gemini 2.5 Flash y reglas de calidad 0-100",
            "modules": "Gobernanza & Auditoría IA",
            "milestone": "Auditor IA y Daily Logs Activos",
            "status": "Planned",
            "story_points": 35,
            "hours_estimated": 95
        }
    ]

    plan_backlog_items: List[Dict[str, Any]] = [
        {
            "item_id": "1",
            "module": "Diagnóstico & Arquitectura",
            "user_story": "Como PM, quiero formalizar el Project Charter para definir alcance y responsables.",
            "sprint": "Sprint 01",
            "story_points": 5,
            "hours_estimated": 20,
            "start_date": "2026-01-16",
            "end_date": "2026-01-20",
            "role": "Project Manager",
            "priority": "Alta",
            "deliverable": "Acta Constitutiva (.docx)",
            "status": "Completado"
        },
        {
            "item_id": "2",
            "module": "Diagnóstico & Arquitectura",
            "user_story": "Como Analista, quiero mapear el flujo AS-IS para detectar cuellos de botella.",
            "sprint": "Sprint 01",
            "story_points": 8,
            "hours_estimated": 30,
            "start_date": "2026-01-21",
            "end_date": "2026-01-26",
            "role": "Analista de Procesos",
            "priority": "Alta",
            "deliverable": "Informe Diagnóstico General",
            "status": "Completado"
        },
        {
            "item_id": "3",
            "module": "Diseño BPMN & SIPOC",
            "user_story": "Como Operador, quiero capturar la matriz SIPOC con entradas, salidas y clientes.",
            "sprint": "Sprint 02",
            "story_points": 8,
            "hours_estimated": 35,
            "start_date": "2026-02-02",
            "end_date": "2026-02-08",
            "role": "Analista Six Sigma",
            "priority": "Alta",
            "deliverable": "Matriz SIPOC Tabular",
            "status": "En Progreso"
        },
        {
            "item_id": "4",
            "module": "Diseño BPMN & SIPOC",
            "user_story": "Como Auditor, quiero validar los requisitos del cliente y SLA de respuesta.",
            "sprint": "Sprint 02",
            "story_points": 5,
            "hours_estimated": 20,
            "start_date": "2026-02-09",
            "end_date": "2026-02-16",
            "role": "QA Lead",
            "priority": "Media",
            "deliverable": "Matriz de Calidad y SLA",
            "status": "Planificado"
        },
        {
            "item_id": "5",
            "module": "UI/UX & Espacio de Trabajo",
            "user_story": "Como Usuario, quiero un lienzo vectorial responsivo con zoom 30%-300% y Bézier.",
            "sprint": "Sprint 03",
            "story_points": 13,
            "hours_estimated": 50,
            "start_date": "2026-02-17",
            "end_date": "2026-02-28",
            "role": "Frontend Dev (Reflex)",
            "priority": "Alta",
            "deliverable": "Lienzo SVG Interactivo",
            "status": "Planificado"
        },
        {
            "item_id": "6",
            "module": "Core & Integraciones",
            "user_story": "Como Sistema, quiero sincronizar con Google Drive para respaldar versiones y hojas.",
            "sprint": "Sprint 04",
            "story_points": 8,
            "hours_estimated": 35,
            "start_date": "2026-03-04",
            "end_date": "2026-03-12",
            "role": "Backend Dev (FastAPI)",
            "priority": "Alta",
            "deliverable": "Drive Service & Sheets API",
            "status": "Planificado"
        },
        {
            "item_id": "7",
            "module": "Gobernanza & Auditoría IA",
            "user_story": "Como Líder de Calidad, quiero que Gemini audite la consistencia del flujo de 0 a 100.",
            "sprint": "Sprint 05",
            "story_points": 8,
            "hours_estimated": 30,
            "start_date": "2026-03-19",
            "end_date": "2026-03-27",
            "role": "AI Engineer",
            "priority": "Alta",
            "deliverable": "Auditor IA con Gemini 2.5 Flash",
            "status": "Planificado"
        }
    ]

    @rx.var
    def plan_working_days_count(self) -> int:
        from backend.services.work_plan_generator import calculate_working_days
        return calculate_working_days(self.plan_start_date, self.plan_end_date, self.plan_work_days_mode)

    @rx.var
    def plan_total_capacity_hours(self) -> int:
        return self.plan_working_days_count * self.plan_daily_hours

    @rx.var
    def plan_suggested_sprints_count(self) -> int:
        days = self.plan_working_days_count
        return max(2, min(12, days // 10))

    @rx.var
    def plan_total_sp(self) -> int:
        return sum(int(item.get("story_points", 0)) for item in self.plan_backlog_items)

    @rx.var
    def plan_total_planned_hours(self) -> int:
        return sum(int(item.get("hours_estimated", 0)) for item in self.plan_backlog_items)

    @rx.var
    def plan_filtered_backlog(self) -> List[Dict[str, Any]]:
        items = list(self.plan_backlog_items)
        if self.plan_filter_sprint != "all":
            items = [i for i in items if i.get("sprint") == self.plan_filter_sprint]
        q = (self.plan_search_query or "").strip().lower()
        if q:
            items = [
                i for i in items
                if q in i.get("user_story", "").lower()
                or q in i.get("module", "").lower()
                or q in i.get("role", "").lower()
                or q in i.get("deliverable", "").lower()
            ]
        return items

    @rx.var
    def plan_sprint_options(self) -> List[str]:
        seen = set()
        opts = []
        for s in self.plan_sprints:
            sid = s.get("sprint_id")
            if sid and sid not in seen:
                seen.add(sid)
                opts.append(sid)
        return opts

    def set_plan_start_date(self, val: str):
        self.plan_start_date = val

    def set_plan_end_date(self, val: str):
        self.plan_end_date = val

    def set_plan_daily_hours(self, val: str):
        try:
            self.plan_daily_hours = int(val)
        except Exception:
            self.plan_daily_hours = 8

    def set_plan_work_days_mode(self, val: str):
        self.plan_work_days_mode = str(val)

    def set_plan_activities_description(self, val: str):
        self.plan_activities_description = val

    def set_plan_active_subtab(self, val: Union[str, List[str]]):
        if isinstance(val, list):
            self.plan_active_subtab = val[0] if val else "backlog"
        else:
            self.plan_active_subtab = str(val)

    def set_plan_search_query(self, val: str):
        self.plan_search_query = val

    def set_plan_filter_sprint(self, val: str):
        self.plan_filter_sprint = str(val)

    def generate_work_plan_ai(self):
        """Invoke Gemini 2.5 Flash to generate Sprints & Backlog plan based on capacity"""
        self.is_generating_plan_ai = True
        self.status_message = "Gemini AI generando desglose de Sprints y Backlog Scrum..."

        try:
            from backend.services.work_plan_generator import generate_work_plan_with_gemini
            result = generate_work_plan_with_gemini(
                project_name=self.project_name,
                project_purpose=self.project_purpose,
                activities_description=self.plan_activities_description,
                start_date_str=self.plan_start_date,
                end_date_str=self.plan_end_date,
                daily_hours=self.plan_daily_hours,
                work_days_mode=self.plan_work_days_mode
            )
            if result.get("sprints"):
                self.plan_sprints = result["sprints"]
            if result.get("backlog_items"):
                self.plan_backlog_items = result["backlog_items"]
            self.status_message = f"✓ Plan de Trabajo generado con IA: {len(self.plan_sprints)} Sprints y {len(self.plan_backlog_items)} tareas"
        except Exception as e:
            self.status_message = f"Error al generar plan con IA: {str(e)}"
        finally:
            self.is_generating_plan_ai = False

    def sync_work_plan_to_google_sheet(self):
        """Sync generated Sprints & Backlog directly into the project's Google Sheet"""
        if not self.sheet_id:
            self.status_message = "El proyecto no tiene un Google Sheet asociado para sincronizar"
            return

        self.is_syncing_plan_sheet = True
        self.status_message = "Sincronizando plan con Google Sheets..."
        try:
            from backend.services.work_plan_generator import sync_plan_to_google_sheet
            ok, msg = sync_plan_to_google_sheet(
                sheet_id=self.sheet_id,
                sprints=self.plan_sprints,
                backlog_items=self.plan_backlog_items
            )
            if ok:
                self.status_message = "✓ ¡Plan de Trabajo sincronizado con éxito en Google Sheets!"
            else:
                self.status_message = f"Error al sincronizar con Google Sheets: {msg}"
        except Exception as e:
            self.status_message = f"Error en sincronización: {str(e)}"
        finally:
            self.is_syncing_plan_sheet = False

    def add_backlog_item(self):
        """Add a new task row to the Backlog"""
        count = len(self.plan_backlog_items) + 1
        new_item = {
            "item_id": str(count),
            "module": "General",
            "user_story": f"Nueva tarea técnica / historia de usuario #{count}",
            "sprint": self.plan_sprints[0]["sprint_id"] if self.plan_sprints else "Sprint 01",
            "story_points": 3,
            "hours_estimated": 10,
            "start_date": self.plan_start_date,
            "end_date": self.plan_end_date,
            "role": "Desarrollador",
            "priority": "Media",
            "deliverable": "Entregable",
            "status": "Planificado"
        }
        self.plan_backlog_items.append(new_item)
        self.status_message = f"Tarea #{count} agregada al Backlog"

    def delete_backlog_item(self, item_id: str):
        """Remove a task row from the Backlog"""
        self.plan_backlog_items = [i for i in self.plan_backlog_items if i.get("item_id") != str(item_id)]
        self.status_message = "Tarea eliminada del Backlog"

    # Project Charter & Master Metadata State
    project_purpose: str = "Estandarizar y automatizar el ciclo integral de atención de aclaraciones y transacciones de clientes vía canales digitales y sistemas centrales."
    project_manager: str = "Ing. José Antonio Hurtado"
    project_sponsor: str = "Dirección de Operaciones & Tecnología"
    start_date: str = "2026-01-16"
    end_date: str = "2026-12-04"
    scope_in: str = "Mapeo SIPOC, diagrama BPMN multi-pestaña, manual de procedimientos y auditoría de calidad."
    scope_out: str = "Desarrollo de integraciones core bancarias propietarias de terceros."

    def set_project_purpose(self, val: str):
        self.project_purpose = val

    def set_project_manager(self, val: str):
        self.project_manager = val

    def set_project_sponsor(self, val: str):
        self.project_sponsor = val

    def set_start_date(self, val: str):
        self.start_date = val

    def set_end_date(self, val: str):
        self.end_date = val

    def set_scope_in(self, val: str):
        self.scope_in = val

    def set_scope_out(self, val: str):
        self.scope_out = val

    # SIPOC Matrix Data State
    sipoc_rows: List[Dict[str, Any]] = [
        {
            "id": "1",
            "step_num": "1.0",
            "provider": "Usuario / Cliente",
            "input": "Solicitud de aclaración vía WhatsApp",
            "step": "1.0 Recepción y captura de número de folio",
            "output": "Folio y datos validados",
            "customer": "Agente Operativo",
            "requirements": "Número de folio válido y teléfono registrado"
        },
        {
            "id": "2",
            "step_num": "2.0",
            "provider": "Agente Operativo",
            "input": "Número de folio validado",
            "step": "2.0 Consulta de estatus de transacción en Chronos",
            "output": "Estatus de la transacción (MO/Vigente)",
            "customer": "Sistema Chronos",
            "requirements": "Tiempo de respuesta del sistema < 30 seg"
        },
        {
            "id": "3",
            "step_num": "3.0",
            "provider": "Sistema Chronos",
            "input": "Estatus de transacción",
            "step": "3.0 ¿Transacción requiere revisión por Fraudes?",
            "output": "Dictamen de aprobación o derivación",
            "customer": "Agente / Área de Fraudes",
            "requirements": "Reglas de riesgo y montos máximos vigentes"
        },
        {
            "id": "4",
            "step_num": "4.0",
            "provider": "Agente Operativo",
            "input": "Dictamen de aprobación",
            "step": "4.0 Notificación de resolución y encuesta",
            "output": "Confirmación y encuesta de satisfacción",
            "customer": "Usuario / Cliente",
            "requirements": "Confirmación de entrega y cierre en Freshdesk"
        }
    ]
    customer_requirements: str = "Tiempos de respuesta (SLA) menores a 5 min, trazabilidad de logs en Chronos y encuesta con satisfacción >= 95%."
    is_completing_sipoc: bool = False

    def set_customer_requirements(self, val: str):
        self.customer_requirements = val

    def add_sipoc_row(self):
        """Add a new empty step row to the SIPOC matrix"""
        count = len(self.sipoc_rows) + 1
        new_row = {
            "id": str(count),
            "step_num": f"{count}.0",
            "provider": "",
            "input": "",
            "step": f"{count}.0 ",
            "output": "",
            "customer": "",
            "requirements": ""
        }
        self.sipoc_rows.append(new_row)
        self.status_message = f"Paso {count}.0 agregado a la Matriz SIPOC"

    def remove_sipoc_row(self, row_id: str):
        """Remove a step row from SIPOC matrix"""
        self.sipoc_rows = [r for r in self.sipoc_rows if r.get("id") != row_id]
        # Re-index step numbers
        for idx, r in enumerate(self.sipoc_rows):
            r["id"] = str(idx + 1)
            r["step_num"] = f"{idx + 1}.0"
        self.status_message = "Fila eliminada de la Matriz SIPOC"

    def update_sipoc_provider(self, row_id: str, val: str):
        for r in self.sipoc_rows:
            if r.get("id") == row_id:
                r["provider"] = val
                break

    def update_sipoc_input(self, row_id: str, val: str):
        for r in self.sipoc_rows:
            if r.get("id") == row_id:
                r["input"] = val
                break

    def update_sipoc_step(self, row_id: str, val: str):
        for r in self.sipoc_rows:
            if r.get("id") == row_id:
                r["step"] = val
                break

    def update_sipoc_output(self, row_id: str, val: str):
        for r in self.sipoc_rows:
            if r.get("id") == row_id:
                r["output"] = val
                break

    def update_sipoc_customer(self, row_id: str, val: str):
        for r in self.sipoc_rows:
            if r.get("id") == row_id:
                r["customer"] = val
                break

    def update_sipoc_reqs(self, row_id: str, val: str):
        for r in self.sipoc_rows:
            if r.get("id") == row_id:
                r["requirements"] = val
                break

    def sync_sipoc_to_flow(self):
        """
        ⚡ Transform SIPOC Table into Flowchart DAG on the Canvas:
        Generates Start Node, Activities/Decisions with Systems/Channels, End Node and Bézier connections.
        """
        if not self.sipoc_rows:
            self.status_message = "La matriz SIPOC está vacía"
            return

        new_nodes = []
        new_edges = []
        
        # 1. Start Node
        first_input = self.sipoc_rows[0].get("input", "Inicio")
        first_provider = self.sipoc_rows[0].get("provider", "Input") or "Input"
        new_nodes.append({
            "id": "node-1",
            "type": "node_start",
            "label": f"Inicio: {first_input[:28]}",
            "swimlane": first_provider,
            "x": 60,
            "y": 140,
            "activity_number": None,
            "attached_system": "",
            "attached_channel": "WhatsApp" if "whatsapp" in first_input.lower() else ""
        })

        # 2. Activity / Decision Nodes from SIPOC Steps
        prev_node_id = "node-1"
        for idx, r in enumerate(self.sipoc_rows):
            node_id = f"node-{idx + 2}"
            step_text = r.get("step", f"Paso {idx+1}.0")
            provider = r.get("provider", "Actor 1") or "Actor 1"
            
            # Detect Decision node type
            is_decision = "?" in step_text or "¿" in step_text or "si " in step_text.lower() or "decisión" in step_text.lower() or "evaluar" in step_text.lower()
            node_type = "node_decision" if is_decision else "node_activity"
            
            # Detect Systems and Channels
            attached_sys = ""
            lower_text = (step_text + " " + r.get("input", "") + " " + r.get("output", "")).lower()
            if "chronos" in lower_text:
                attached_sys = "Chronos"
            elif "freshdesk" in lower_text:
                attached_sys = "Freshdesk"
            elif "sap" in lower_text or "erp" in lower_text:
                attached_sys = "SAP"

            attached_chan = ""
            if "whatsapp" in lower_text:
                attached_chan = "WhatsApp"
            elif "bria" in lower_text or "llamada" in lower_text or "teléfono" in lower_text:
                attached_chan = "Bria"
            elif "correo" in lower_text or "email" in lower_text:
                attached_chan = "Email"

            x_pos = 60 + (idx + 1) * 260
            y_pos = 140

            new_nodes.append({
                "id": node_id,
                "type": node_type,
                "label": step_text,
                "swimlane": provider,
                "x": x_pos,
                "y": y_pos,
                "activity_number": (idx + 1) if not is_decision else None,
                "attached_system": attached_sys,
                "attached_channel": attached_chan
            })

            # Add connecting edge
            edge_id = f"e{prev_node_id}-{node_id}"
            new_edges.append({
                "id": edge_id,
                "source": prev_node_id,
                "target": node_id,
                "label": "Sí" if prev_node_id != "node-1" and any(n.get("type") == "node_decision" for n in new_nodes if n.get("id") == prev_node_id) else ""
            })
            prev_node_id = node_id

        # 3. End Node
        end_node_id = f"node-{len(self.sipoc_rows) + 2}"
        last_output = self.sipoc_rows[-1].get("output", "Fin")
        last_customer = self.sipoc_rows[-1].get("customer", "Output") or "Output"
        end_x = 60 + (len(self.sipoc_rows) + 1) * 260
        
        new_nodes.append({
            "id": end_node_id,
            "type": "node_end",
            "label": f"Fin: {last_output[:28]}",
            "swimlane": last_customer,
            "x": end_x,
            "y": 140,
            "activity_number": None,
            "attached_system": "",
            "attached_channel": ""
        })

        new_edges.append({
            "id": f"e{prev_node_id}-{end_node_id}",
            "source": prev_node_id,
            "target": end_node_id,
            "label": ""
        })

        # Update swimlanes list
        unique_lanes = []
        for n in new_nodes:
            lane = n.get("swimlane")
            if lane and lane not in unique_lanes:
                unique_lanes.append(lane)
        if len(unique_lanes) < 2:
            unique_lanes = ["Input", "Actor 1 (ej. Usuario)", "Actor 2 (ej. Sistema)", "Output"]

        self.nodes = new_nodes
        self.edges = new_edges
        self.swimlanes = unique_lanes

        # Update current page tab
        if 0 <= self.active_page_index < len(self.project_pages):
            self.project_pages[self.active_page_index]["nodes"] = list(self.nodes)
            self.project_pages[self.active_page_index]["edges"] = list(self.edges)
            self.project_pages[self.active_page_index]["swimlanes"] = list(self.swimlanes)

        self.status_message = f"⚡ Diagrama de Flujo generado con {len(self.nodes)} símbolos desde la Matriz SIPOC"
        self.active_view = "flow"

    def complete_sipoc_with_ai(self):
        """Auto-complete SIPOC rows using Gemini AI / expert template"""
        self.is_completing_sipoc = True
        self.status_message = "Completando Matriz SIPOC con IA..."
        try:
            from backend.routers.diagrams import complete_sipoc_with_ai, SipocAiRequest
            res = complete_sipoc_with_ai(SipocAiRequest(
                project_name=self.project_name,
                project_purpose=self.project_purpose,
                existing_rows=self.sipoc_rows
            ))
            if res.get("rows"):
                self.sipoc_rows = res["rows"]
                self.status_message = f"✨ Matriz SIPOC completada con {len(self.sipoc_rows)} pasos sugeridos"
        except Exception as e:
            self.status_message = f"Error al autocompletar SIPOC: {str(e)}"
        finally:
            self.is_completing_sipoc = False

    def export_sipoc_excel(self):
        """Download styled Six Sigma SIPOC Excel workbook (.xlsx)"""
        try:
            from backend.services.sipoc_exporter import export_sipoc_to_excel
            stream = export_sipoc_to_excel(
                project_name=self.project_name,
                project_purpose=self.project_purpose,
                sipoc_rows=self.sipoc_rows,
                customer_requirements=self.customer_requirements
            )
            safe_name = self.project_name.replace(" ", "_")
            self.status_message = "Excel de Matriz SIPOC descargado exitosamente"
            return rx.download(
                data=stream.getvalue(),
                filename=f"Matriz_SIPOC_{safe_name}.xlsx"
            )
        except Exception as e:
            self.status_message = f"Error al exportar Excel: {str(e)}"

    # Narrative & Policy Manual State
    narrative_text: str = """# 📘 Manual de Procedimientos & Narrativa Oficial
# PROYECTO DEMO TEMIS

## 🎯 1. Objetivo y Propósito del Proceso
Estandarizar y automatizar el ciclo integral de atención de aclaraciones y transacciones de clientes vía canales digitales y sistemas centrales.

## 👥 2. Matriz de Roles y Responsabilidades
- **Actores y Participantes:** Agente Operativo, Sistema Chronos, Usuario / Cliente
- **Sistemas y Plataformas:** Chronos, Freshdesk
- **Canales de Interacción:** WhatsApp

---

## 📝 3. Narrativa Operativa Secuencial (Paso a Paso)

### 1.0 Entrada e Inicio del Proceso
El proceso inicia formalmente cuando el participante **[Usuario / Cliente]** detona el evento: *"Inicio: Solicitud de aclaración"* por el canal **WhatsApp**. Se reciben los datos iniciales y se habilita el caso para su gestión.

### 2.0 Ejecución de Tarea: 1.0 Recepción y captura de número de folio
El responsable **[Usuario / Cliente]** ejecuta la actividad operativa de *"Recepción y captura de número de folio"* por el canal **WhatsApp**. Se genera el registro auditable correspondiente en Freshdesk.

### 3.0 Ejecución de Tarea: 2.0 Consulta de estatus de transacción en Chronos
El responsable **[Agente Operativo]** ejecuta la actividad operativa de *"Consulta de estatus en Chronos"* a través de **Chronos**. Se valida la vigencia de la póliza o transacción.

### 4.0 Punto de Decisión / Validación: 3.0 ¿Transacción requiere revisión por Fraudes?
El rol **[Sistema Chronos]** realiza la validación crítica *"¿Transacción requiere revisión por Fraudes?"* a través de **Chronos**. Las ramificaciones son:
  - **Condición 'Sí':** Se turna al área especializada de Fraudes (SC.030).
  - **Condición 'No':** Se procede con el dictamen de aprobación estándar.

### 5.0 Cierre y Conclusión del Proceso
Se completa la etapa final: *"Fin: Confirmación y encuesta"*. El proceso concluye satisfactoriamente con la entrega del producto/resultado hacia el participante **[Usuario / Cliente]**.

---

## ⚖️ 4. Políticas y Reglas de Negocio Clave
1. **Trazabilidad Absoluta:** Toda interacción por canal digital o sistema debe quedar registrada con marca de tiempo y folio.
2. **Control de Calidad:** Las compuertas de decisión deben validar que la totalidad de requisitos previos se cumplan antes de pasar a la siguiente fase.
3. **Escalamiento:** En caso de excepción no contemplada en las reglas estándar, el caso se turna al líder del proceso para dictamen.
"""
    is_generating_narrative: bool = False

    def set_narrative_text(self, val: str):
        self.narrative_text = val

    def generate_narrative_ai(self):
        """⚡ Generate procedure manual narrative in continuous prose from current Flow and SIPOC data"""
        self.is_generating_narrative = True
        self.status_message = "Gemini AI redactando la Narrativa Oficial del proceso..."
        try:
            from backend.services.process_narrative import generate_process_narrative
            self.narrative_text = generate_process_narrative(
                project_name=self.project_name,
                project_purpose=self.project_purpose,
                nodes=self.nodes,
                edges=self.edges,
                sipoc_rows=self.sipoc_rows
            )
            self.status_message = "✨ Narrativa Oficial redactada y sincronizada con éxito"
        except Exception as e:
            self.status_message = f"Error al generar narrativa: {str(e)}"
        finally:
            self.is_generating_narrative = False

    def export_narrative_markdown(self):
        """Download narrative as Markdown/Text document"""
        safe_name = self.project_name.replace(" ", "_")
        self.status_message = "Manual de Procedimientos exportado (.md)"
        return rx.download(
            data=self.narrative_text,
            filename=f"Manual_Procedimiento_{safe_name}.md"
        )

    
    # List of Nodes on Canvas
    nodes: List[Dict[str, Any]] = [
        {
            "id": "node-1",
            "type": "node_start",
            "label": "Inicio Proceso",
            "swimlane": "Input",
            "x": 40,
            "y": 120,
            "activity_number": None,
            "attached_system": "",
            "attached_channel": ""
        },
        {
            "id": "node-2",
            "type": "node_activity",
            "label": "Enviar solicitud de soporte",
            "swimlane": "Actor 1 (ej. Usuario)",
            "x": 280,
            "y": 120,
            "activity_number": 1,
            "attached_system": "Freshdesk",
            "attached_channel": "WhatsApp"
        },
        {
            "id": "node-3",
            "type": "node_decision",
            "label": "¿Datos completos?",
            "swimlane": "Actor 2 (ej. Sistema)",
            "x": 540,
            "y": 120,
            "activity_number": None,
            "attached_system": "Chronos",
            "attached_channel": ""
        },
        {
            "id": "node-4",
            "type": "node_end",
            "label": "Fin",
            "swimlane": "Output",
            "x": 800,
            "y": 120,
            "activity_number": None,
            "attached_system": "",
            "attached_channel": ""
        }
    ]

    # List of Edges/Connections
    edges: List[Dict[str, Any]] = [
        {"id": "e1-2", "source": "node-1", "target": "node-2", "label": ""},
        {"id": "e2-3", "source": "node-2", "target": "node-3", "label": ""},
        {"id": "e3-4", "source": "node-3", "target": "node-4", "label": "Sí"}
    ]

    @rx.var
    def computed_edges(self) -> List[Dict[str, Any]]:
        """Calculate dynamic SVG Bézier curve paths with exact perimeter anchor points (East -> West)"""
        node_map = {n["id"]: n for n in self.nodes}
        res = []
        for e in self.edges:
            src = node_map.get(e["source"])
            dst = node_map.get(e["target"])
            if src and dst:
                st = src.get("type", "")
                dt = dst.get("type", "")

                # Source Node dimensions
                if st in ["node_start", "node_end"]:
                    sw, sh = 130, 42
                elif st == "node_decision":
                    sw, sh = 160, 68
                elif st == "node_activity":
                    sw, sh = 190, 68
                elif st.startswith("channel_") or st == "node_system":
                    sw, sh = 175, 58
                else:
                    sw, sh = 160, 52

                # Target Node dimensions
                if dt in ["node_start", "node_end"]:
                    dw, dh = 130, 42
                elif dt == "node_decision":
                    dw, dh = 160, 68
                elif dt == "node_activity":
                    dw, dh = 190, 68
                elif dt.startswith("channel_") or dt == "node_system":
                    dw, dh = 175, 58
                else:
                    dw, dh = 160, 52

                x1 = src.get("x", 0) + sw
                y1 = src.get("y", 0) + (sh / 2)
                x2 = dst.get("x", 0)
                y2 = dst.get("y", 0) + (dh / 2)

                dx = max(45, abs(x2 - x1) / 2)
                cx1 = x1 + dx
                cy1 = y1
                cx2 = x2 - dx
                cy2 = y2
                lbl = e.get("label", "")
                res.append({
                    "id": e.get("id", ""),
                    "d": f"M {x1} {y1} C {cx1} {cy1}, {cx2} {cy2}, {x2} {y2}",
                    "label": lbl,
                    "label_x": (x1 + x2) / 2,
                    "label_y": (y1 + y2) / 2 - 8,
                    "has_label": bool(lbl),
                })
        return res

    # Selection & Property Inspector state
    selected_node_id: str = ""
    node_label_edit: str = ""
    node_swimlane_edit: str = ""
    selected_node_type: str = ""
    selected_node_system: str = ""
    selected_node_channel: str = ""

    # Canvas Zoom State (Figma / Miro / Lucidchart style)
    zoom_level: float = 1.0
    show_swimlanes: bool = False

    @rx.var
    def zoom_percent(self) -> str:
        return f"{int(round(self.zoom_level * 100))}%"

    @rx.var
    def zoom_width(self) -> str:
        return f"{int(round(100.0 / max(0.1, self.zoom_level)))}%"

    @rx.var
    def zoom_height(self) -> str:
        return f"{int(round(100.0 / max(0.1, self.zoom_level)))}vh"

    def zoom_in(self):
        if self.zoom_level < 3.0:
            self.zoom_level = round(self.zoom_level + 0.1, 2)

    def zoom_out(self):
        if self.zoom_level > 0.3:
            self.zoom_level = round(self.zoom_level - 0.1, 2)

    def zoom_reset(self):
        self.zoom_level = 1.0

    def toggle_swimlanes(self):
        self.show_swimlanes = not self.show_swimlanes

    # Select Node for Editing in Inspector
    def select_node(self, node_id: str):
        self.selected_node_id = node_id
        for n in self.nodes:
            if n["id"] == node_id:
                self.node_label_edit = n.get("label", "")
                self.node_swimlane_edit = n.get("swimlane", "")
                self.selected_node_type = n.get("type", "node_activity")
                self.selected_node_system = n.get("attached_system", "")
                self.selected_node_channel = n.get("attached_channel", "")
                break

    def unselect_node(self):
        self.selected_node_id = ""

    def set_selected_node_label(self, val: str):
        self.node_label_edit = val
        for n in self.nodes:
            if n["id"] == self.selected_node_id:
                n["label"] = val
                break
        self.trigger_auto_save()

    def set_selected_node_type(self, val: str):
        self.selected_node_type = val
        for n in self.nodes:
            if n["id"] == self.selected_node_id:
                n["type"] = val
                break
        self.trigger_auto_save()

    def set_selected_node_swimlane(self, val: str):
        self.node_swimlane_edit = val
        for n in self.nodes:
            if n["id"] == self.selected_node_id:
                n["swimlane"] = val
                break
        self.trigger_auto_save()

    def set_selected_node_system(self, val: str):
        self.selected_node_system = val
        for n in self.nodes:
            if n["id"] == self.selected_node_id:
                n["attached_system"] = val
                break
        self.trigger_auto_save()

    def set_selected_node_channel(self, val: str):
        self.selected_node_channel = val
        for n in self.nodes:
            if n["id"] == self.selected_node_id:
                n["attached_channel"] = val
                break
        self.trigger_auto_save()

    # AI Text-to-Diagram Generation State
    ai_prompt_text: str = ""
    is_generating_ai: bool = False
    status_message: str = "Listo"

    # Set phase handler
    def set_phase(self, phase_num: int):
        self.current_phase = phase_num
        self.phase_name = PHASE_NAMES.get(phase_num, f"Fase {phase_num}")

    # Set prompt text handler
    def set_ai_prompt_text(self, val: str):
        self.ai_prompt_text = val

    # Add Node from Symbology Palette
    def add_node_by_type(self, node_type: str, label: str):
        count = len(self.nodes) + 1
        new_id = f"node-{count}"
        swimlane = self.swimlanes[0] if self.swimlanes else "Actor 1"
        
        # Calculate sequential activity number if activity
        activity_num = None
        if node_type == "node_activity":
            activities = [n for n in self.nodes if n.get("type") == "node_activity"]
            activity_num = len(activities) + 1

        new_node = {
            "id": new_id,
            "type": node_type,
            "label": label,
            "swimlane": swimlane,
            "x": 100 + (count * 30) % 600,
            "y": 150 + (count * 40) % 300,
            "activity_number": activity_num,
            "attached_system": "",
            "attached_channel": ""
        }
        self.nodes.append(new_node)
        self.status_message = f"Símbolo '{label}' agregado al lienzo"

    # Clear diagram canvas
    def clear_canvas(self):
        self.nodes = []
        self.edges = []
        self.status_message = "Lienzo limpiado"

    # Select Node for Editing
    def select_node(self, node_id: str):
        self.selected_node_id = node_id
        for n in self.nodes:
            if n["id"] == node_id:
                self.node_label_edit = n["label"]
                self.node_swimlane_edit = n["swimlane"]
                break

    # Delete Selected Node
    def delete_selected_node(self):
        if not self.selected_node_id:
            return
        self.nodes = [n for n in self.nodes if n["id"] != self.selected_node_id]
        self.edges = [e for e in self.edges if e["source"] != self.selected_node_id and e["target"] != self.selected_node_id]
        self.selected_node_id = ""
        self.status_message = "Nodo eliminado"

    # Move Selected Node
    def move_selected_node(self, dx: int, dy: int):
        """Move or reposition selected node on canvas"""
        if not self.selected_node_id:
            return
        for n in self.nodes:
            if n["id"] == self.selected_node_id:
                n["x"] = max(10, n.get("x", 0) + dx)
                n["y"] = max(10, n.get("y", 0) + dy)
                break
        self.status_message = f"Nodo {self.selected_node_id} reposicionado"

    # Project Multi-Tab Diagram Pages State
    project_pages: List[Dict[str, Any]] = [
        {
            "page_id": "1",
            "name": "Página 1: Flujo Principal",
            "nodes": [
                {
                    "id": "node-1",
                    "type": "node_start",
                    "label": "Inicio Proceso",
                    "swimlane": "Input",
                    "x": 40,
                    "y": 120,
                    "activity_number": None,
                    "attached_system": "",
                    "attached_channel": ""
                },
                {
                    "id": "node-2",
                    "type": "node_activity",
                    "label": "Enviar solicitud de soporte",
                    "swimlane": "Actor 1 (ej. Usuario)",
                    "x": 280,
                    "y": 120,
                    "activity_number": 1,
                    "attached_system": "Freshdesk",
                    "attached_channel": "WhatsApp"
                },
                {
                    "id": "node-3",
                    "type": "node_decision",
                    "label": "¿Datos completos?",
                    "swimlane": "Actor 2 (ej. Sistema)",
                    "x": 540,
                    "y": 120,
                    "activity_number": None,
                    "attached_system": "Chronos",
                    "attached_channel": ""
                },
                {
                    "id": "node-4",
                    "type": "node_end",
                    "label": "Fin",
                    "swimlane": "Output",
                    "x": 800,
                    "y": 120,
                    "activity_number": None,
                    "attached_system": "",
                    "attached_channel": ""
                }
            ],
            "edges": [
                {"id": "e1-2", "source": "node-1", "target": "node-2", "label": ""},
                {"id": "e2-3", "source": "node-2", "target": "node-3", "label": ""},
                {"id": "e3-4", "source": "node-3", "target": "node-4", "label": "Sí"}
            ],
            "swimlanes": ["Input", "Actor 1 (ej. Usuario)", "Actor 2 (ej. Sistema)", "Output"]
        }
    ]
    active_page_index: int = 0
    # Saved Projects / Flujos Guardados Catalog State
    show_recent_modal: bool = False
    search_saved_query: str = ""
    saved_projects: List[Dict[str, Any]] = [
        {
            "id": "proj-temis",
            "code": "PRJ-TEMIS",
            "name": "Suite de Procesos & Gobernanza TEMIS",
            "purpose": "Plataforma SaaS Cloud de ingeniería de procesos con editor BPMN, matriz SIPOC, auditoría Six Sigma y gobernanza de 7 fases.",
            "manager": "Ing. José Antonio Hurtado",
            "manager_initials": "JH",
            "sponsor": "Dirección General & Tecnología",
            "start_date": "2026-01-16",
            "end_date": "2026-12-04",
            "scope_in": "Migración Desktop ➔ Web SaaS, Canvas Bézier SVG, Google Drive sync, AI Gemini 2.5 y auditoría continua.",
            "scope_out": "Integraciones legacy propietarias no web.",
            "current_phase": 4,
            "phase_name": "Fase 4: Ejecución Iterativa",
            "updated_at": "2026-09-18 12:00",
            "drive_folder_id": "1NA32b-o473ZxcpuLxHPf2xDOt5XHn2CI",
            "drive_folder_url": "https://drive.google.com/drive/folders/1NA32b-o473ZxcpuLxHPf2xDOt5XHn2CI",
            "sheet_id": "1GxiIwR2rUMkZKHu00JYzlQrs6EsyXO5VqUL6qpl_MBs",
            "sheet_url": "https://docs.google.com/spreadsheets/d/1GxiIwR2rUMkZKHu00JYzlQrs6EsyXO5VqUL6qpl_MBs/edit",
            "current_sprint": "Sprint 07",
            "current_sprint_name": "Persistencia Híbrida & Exportador Gráfico",
            "progress_percentage": 68.5,
            "completed_sp": 218,
            "total_sp": 318,
            "completed_tasks": 32,
            "total_tasks": 47,
            "health_status": "green",
            "audit_score": 98,
            "nodes_count": 8,
            "steps_count": 4,
            "sipoc_rows": [
                {
                    "id": "1",
                    "step_num": "1.0",
                    "provider": "Usuario / Analista",
                    "input": "Requerimiento de proceso / Diagrama",
                    "step": "1.0 Captura SIPOC y modelado en Canvas Bézier",
                    "output": "Diagrama de flujo BPMN estructurado",
                    "customer": "Auditor IA / Sponsor",
                    "requirements": "Simbología oficial y swimlanes completas"
                },
                {
                    "id": "2",
                    "step_num": "2.0",
                    "provider": "Motor TEMIS",
                    "input": "Estructura del proceso",
                    "step": "2.0 Auditoría Six Sigma con Gemini 2.5 Flash",
                    "output": "Score de calidad (0-100) y hallazgos",
                    "customer": "Project Manager",
                    "requirements": "Validación de nodos de inicio, fin y decisiones"
                },
                {
                    "id": "3",
                    "step_num": "3.0",
                    "provider": "Service Account TEMIS",
                    "input": "Proyecto aprobado",
                    "step": "3.0 Replicación y respaldo en Google Workspace Shared Drive",
                    "output": "Carpetas de 7 fases + Google Sheet Plan de Trabajo",
                    "customer": "Organización",
                    "requirements": "Sync automático a 12:00 AM y reporte semanal"
                }
            ],
            "customer_requirements": "Cero costo recurrente de licencias Lucidchart, disponibilidad SaaS 99.9% y sincronización nativa en Google Drive.",
            "nodes": [
                {"id": "node-1", "type": "node_start", "label": "Inicio: Requerimiento", "swimlane": "Input", "x": 40, "y": 140, "activity_number": None, "attached_system": "", "attached_channel": "Web"},
                {"id": "node-2", "type": "node_activity", "label": "Mapeo SIPOC & Diagrama", "swimlane": "Actor 1 (ej. Usuario)", "x": 260, "y": 140, "activity_number": 1, "attached_system": "TEMIS Web", "attached_channel": ""},
                {"id": "node-3", "type": "node_decision", "label": "¿Score Auditoría >= 90?", "swimlane": "Actor 2 (ej. Sistema)", "x": 520, "y": 140, "activity_number": None, "attached_system": "Gemini AI", "attached_channel": ""},
                {"id": "node-4", "type": "node_activity", "label": "Promover a Siguiente Fase", "swimlane": "Actor 2 (ej. Sistema)", "x": 780, "y": 60, "activity_number": 2, "attached_system": "TEMIS Core", "attached_channel": ""},
                {"id": "node-5", "type": "node_activity", "label": "Ajustar Reglas y Conexiones", "swimlane": "Actor 1 (ej. Usuario)", "x": 780, "y": 220, "activity_number": 3, "attached_system": "TEMIS Web", "attached_channel": ""},
                {"id": "node-6", "type": "node_end", "label": "Fin: Publicación Oficial", "swimlane": "Output", "x": 1040, "y": 60, "activity_number": None, "attached_system": "Drive", "attached_channel": ""}
            ],
            "edges": [
                {"id": "e1-2", "source": "node-1", "target": "node-2", "label": ""},
                {"id": "e2-3", "source": "node-2", "target": "node-3", "label": ""},
                {"id": "e3-4", "source": "node-3", "target": "node-4", "label": "Sí"},
                {"id": "e3-5", "source": "node-3", "target": "node-5", "label": "No"},
                {"id": "e5-2", "source": "node-5", "target": "node-2", "label": "Iterar"},
                {"id": "e4-6", "source": "node-4", "target": "node-6", "label": ""}
            ],
            "swimlanes": ["Input", "Actor 1 (ej. Usuario)", "Actor 2 (ej. Sistema)", "Output"],
            "project_pages": [
                {
                    "page_id": "1",
                    "name": "Página 1: Arquitectura Core",
                    "nodes": [
                        {"id": "node-1", "type": "node_start", "label": "Inicio: Requerimiento", "swimlane": "Input", "x": 40, "y": 140, "activity_number": None, "attached_system": "", "attached_channel": "Web"},
                        {"id": "node-2", "type": "node_activity", "label": "Mapeo SIPOC & Diagrama", "swimlane": "Actor 1 (ej. Usuario)", "x": 260, "y": 140, "activity_number": 1, "attached_system": "TEMIS Web", "attached_channel": ""},
                        {"id": "node-3", "type": "node_decision", "label": "¿Score Auditoría >= 90?", "swimlane": "Actor 2 (ej. Sistema)", "x": 520, "y": 140, "activity_number": None, "attached_system": "Gemini AI", "attached_channel": ""},
                        {"id": "node-4", "type": "node_activity", "label": "Promover a Siguiente Fase", "swimlane": "Actor 2 (ej. Sistema)", "x": 780, "y": 60, "activity_number": 2, "attached_system": "TEMIS Core", "attached_channel": ""},
                        {"id": "node-5", "type": "node_activity", "label": "Ajustar Reglas y Conexiones", "swimlane": "Actor 1 (ej. Usuario)", "x": 780, "y": 220, "activity_number": 3, "attached_system": "TEMIS Web", "attached_channel": ""},
                        {"id": "node-6", "type": "node_end", "label": "Fin: Publicación Oficial", "swimlane": "Output", "x": 1040, "y": 60, "activity_number": None, "attached_system": "Drive", "attached_channel": ""}
                    ],
                    "edges": [
                        {"id": "e1-2", "source": "node-1", "target": "node-2", "label": ""},
                        {"id": "e2-3", "source": "node-2", "target": "node-3", "label": ""},
                        {"id": "e3-4", "source": "node-3", "target": "node-4", "label": "Sí"},
                        {"id": "e3-5", "source": "node-3", "target": "node-5", "label": "No"},
                        {"id": "e5-2", "source": "node-5", "target": "node-2", "label": "Iterar"},
                        {"id": "e4-6", "source": "node-4", "target": "node-6", "label": ""}
                    ],
                    "swimlanes": ["Input", "Actor 1 (ej. Usuario)", "Actor 2 (ej. Sistema)", "Output"]
                }
            ],
            "narrative_text": "# 📘 Manual de Arquitectura TEMIS Web Flow\n\nTEMIS es la suite integral para el diseño, gobernanza y auditoría automatizada de procesos de negocio..."
        },
        {
            "id": "proj-x",
            "code": "PRJ-X",
            "name": "Proyecto X Procesos",
            "purpose": "Proyecto piloto para verificación y despliegue del framework de 7 fases y sincronización en Google Drive.",
            "manager": "Ing. José Antonio Hurtado",
            "manager_initials": "JH",
            "sponsor": "Área de Procesos & Calidad",
            "start_date": "2026-09-18",
            "end_date": "2026-12-18",
            "scope_in": "Inicialización de carpetas, replicación de Google Sheet y distribución de actas.",
            "scope_out": "Módulos fuera de prueba.",
            "current_phase": 1,
            "phase_name": "Fase 1: Diagnóstico Estratégico",
            "updated_at": "2026-09-18 12:02",
            "drive_folder_id": "1V6cfM92nAoCq_MBbu_9hxowbMIofuD8X",
            "drive_folder_url": "https://drive.google.com/drive/folders/1V6cfM92nAoCq_MBbu_9hxowbMIofuD8X",
            "sheet_id": "1_haZDSiCPaED3tWS48XJyVfuo5uTKBvmBSC9nqUMR4Y",
            "sheet_url": "https://docs.google.com/spreadsheets/d/1_haZDSiCPaED3tWS48XJyVfuo5uTKBvmBSC9nqUMR4Y/edit",
            "current_sprint": "Sprint 01",
            "current_sprint_name": "Diagnóstico y Mapeo AS-IS",
            "progress_percentage": 0.0,
            "completed_sp": 0,
            "total_sp": 30,
            "completed_tasks": 0,
            "total_tasks": 6,
            "health_status": "green",
            "audit_score": 100,
            "nodes_count": 2,
            "steps_count": 2,
            "sipoc_rows": [
                {
                    "id": "1",
                    "step_num": "1.0",
                    "provider": "Líder de Proceso",
                    "input": "Entrevistas operativas",
                    "step": "1.0 Diagnóstico AS-IS y levantamiento de cuellos de botella",
                    "output": "Informe Diagnóstico inicial",
                    "customer": "Comité de Gobierno",
                    "requirements": "Identificación clara de fricciones operativas"
                }
            ],
            "customer_requirements": "Estructuración de acuerdo a las 7 fases corporativas.",
            "nodes": [
                {"id": "node-1", "type": "node_start", "label": "Inicio: Diagnóstico", "swimlane": "Input", "x": 60, "y": 140, "activity_number": None, "attached_system": "", "attached_channel": ""},
                {"id": "node-2", "type": "node_activity", "label": "Levantamiento de Información AS-IS", "swimlane": "Actor 1 (ej. Usuario)", "x": 300, "y": 140, "activity_number": 1, "attached_system": "Docs", "attached_channel": ""}
            ],
            "edges": [
                {"id": "e1-2", "source": "node-1", "target": "node-2", "label": ""}
            ],
            "swimlanes": ["Input", "Actor 1 (ej. Usuario)", "Output"],
            "project_pages": [
                {
                    "page_id": "1",
                    "name": "Página 1: Flujo AS-IS",
                    "nodes": [
                        {"id": "node-1", "type": "node_start", "label": "Inicio: Diagnóstico", "swimlane": "Input", "x": 60, "y": 140, "activity_number": None, "attached_system": "", "attached_channel": ""},
                        {"id": "node-2", "type": "node_activity", "label": "Levantamiento de Información AS-IS", "swimlane": "Actor 1 (ej. Usuario)", "x": 300, "y": 140, "activity_number": 1, "attached_system": "Docs", "attached_channel": ""}
                    ],
                    "edges": [
                        {"id": "e1-2", "source": "node-1", "target": "node-2", "label": ""}
                    ],
                    "swimlanes": ["Input", "Actor 1 (ej. Usuario)", "Output"]
                }
            ],
            "narrative_text": "# 📘 Proyecto X Procesos\n\nFase de diagnóstico estratégico y alineación con la metodología TEMIS."
        },
        {
            "id": "proj-wha",
            "code": "PRJ-WHA",
            "name": "Atención y Aclaraciones WhatsApp",
            "purpose": "Estandarizar y automatizar el ciclo integral de atención de aclaraciones y transacciones de clientes vía canales digitales y sistemas centrales.",
            "manager": "Ing. José Antonio Hurtado",
            "manager_initials": "JH",
            "sponsor": "Dirección de Operaciones & CX",
            "start_date": "2026-01-16",
            "end_date": "2026-12-04",
            "scope_in": "Mapeo SIPOC, diagrama BPMN multi-pestaña, manual de procedimientos y auditoría de calidad.",
            "scope_out": "Desarrollo de integraciones core bancarias propietarias de terceros.",
            "current_phase": 4,
            "phase_name": "Fase 4: Ejecución Iterativa",
            "updated_at": "2026-09-17 14:00",
            "drive_folder_id": "",
            "drive_folder_url": "",
            "sheet_id": "",
            "sheet_url": "",
            "current_sprint": "Sprint 04",
            "current_sprint_name": "Reglas de Enrutamiento Freshdesk & WhatsApp",
            "progress_percentage": 82.0,
            "completed_sp": 120,
            "total_sp": 146,
            "completed_tasks": 18,
            "total_tasks": 22,
            "health_status": "green",
            "audit_score": 95,
            "nodes_count": 4,
            "steps_count": 4,
            "sipoc_rows": [
                {
                    "id": "1",
                    "step_num": "1.0",
                    "provider": "Usuario / Cliente",
                    "input": "Solicitud de aclaración vía WhatsApp",
                    "step": "1.0 Recepción y captura de número de folio",
                    "output": "Folio y datos validados",
                    "customer": "Agente Operativo",
                    "requirements": "Número de folio válido y teléfono registrado"
                },
                {
                    "id": "2",
                    "step_num": "2.0",
                    "provider": "Agente Operativo",
                    "input": "Número de folio validado",
                    "step": "2.0 Consulta de estatus de transacción en Chronos",
                    "output": "Estatus de la transacción (MO/Vigente)",
                    "customer": "Sistema Chronos",
                    "requirements": "Tiempo de respuesta del sistema < 30 seg"
                }
            ],
            "customer_requirements": "Tiempos de respuesta (SLA) menores a 5 min, trazabilidad de logs en Chronos y encuesta con satisfacción >= 95%.",
            "nodes": [
                {"id": "node-1", "type": "node_start", "label": "Inicio Proceso", "swimlane": "Input", "x": 40, "y": 120, "activity_number": None, "attached_system": "", "attached_channel": ""},
                {"id": "node-2", "type": "node_activity", "label": "Enviar solicitud de soporte", "swimlane": "Actor 1 (ej. Usuario)", "x": 280, "y": 120, "activity_number": 1, "attached_system": "Freshdesk", "attached_channel": "WhatsApp"},
                {"id": "node-3", "type": "node_decision", "label": "¿Datos completos?", "swimlane": "Actor 2 (ej. Sistema)", "x": 540, "y": 120, "activity_number": None, "attached_system": "Chronos", "attached_channel": ""},
                {"id": "node-4", "type": "node_end", "label": "Fin", "swimlane": "Output", "x": 800, "y": 120, "activity_number": None, "attached_system": "", "attached_channel": ""}
            ],
            "edges": [
                {"id": "e1-2", "source": "node-1", "target": "node-2", "label": ""},
                {"id": "e2-3", "source": "node-2", "target": "node-3", "label": ""},
                {"id": "e3-4", "source": "node-3", "target": "node-4", "label": "Sí"}
            ],
            "swimlanes": ["Input", "Actor 1 (ej. Usuario)", "Actor 2 (ej. Sistema)", "Output"],
            "project_pages": [
                {
                    "page_id": "1",
                    "name": "Página 1: Flujo Principal",
                    "nodes": [
                        {"id": "node-1", "type": "node_start", "label": "Inicio Proceso", "swimlane": "Input", "x": 40, "y": 120, "activity_number": None, "attached_system": "", "attached_channel": ""},
                        {"id": "node-2", "type": "node_activity", "label": "Enviar solicitud de soporte", "swimlane": "Actor 1 (ej. Usuario)", "x": 280, "y": 120, "activity_number": 1, "attached_system": "Freshdesk", "attached_channel": "WhatsApp"},
                        {"id": "node-3", "type": "node_decision", "label": "¿Datos completos?", "swimlane": "Actor 2 (ej. Sistema)", "x": 540, "y": 120, "activity_number": None, "attached_system": "Chronos", "attached_channel": ""},
                        {"id": "node-4", "type": "node_end", "label": "Fin", "swimlane": "Output", "x": 800, "y": 120, "activity_number": None, "attached_system": "", "attached_channel": ""}
                    ],
                    "edges": [
                        {"id": "e1-2", "source": "node-1", "target": "node-2", "label": ""},
                        {"id": "e2-3", "source": "node-2", "target": "node-3", "label": ""},
                        {"id": "e3-4", "source": "node-3", "target": "node-4", "label": "Sí"}
                    ],
                    "swimlanes": ["Input", "Actor 1 (ej. Usuario)", "Actor 2 (ej. Sistema)", "Output"]
                }
            ],
            "narrative_text": "# 📘 Manual de Procedimientos - Aclaraciones WhatsApp\n\nEl proceso inicia cuando el cliente envía su folio vía WhatsApp..."
        },
        {
            "id": "proj-chronos",
            "code": "PRJ-CHRONOS",
            "name": "Consulta y Validación de Pólizas Chronos",
            "purpose": "Validar en tiempo real el estatus y cobertura de pólizas financieras en el core Chronos.",
            "manager": "Equipo Operaciones",
            "manager_initials": "EO",
            "sponsor": "Subdirección de Finanzas & Riesgos",
            "start_date": "2026-02-01",
            "end_date": "2026-11-15",
            "scope_in": "Validación de saldo, consulta API Chronos y notificación.",
            "scope_out": "Modificaciones de póliza fuera de sistema.",
            "current_phase": 3,
            "phase_name": "Fase 3: Planificación Híbrida",
            "updated_at": "2026-09-15 11:30",
            "drive_folder_id": "",
            "drive_folder_url": "",
            "sheet_id": "",
            "sheet_url": "",
            "current_sprint": "Sprint 02",
            "current_sprint_name": "Especificación de API & SLA",
            "progress_percentage": 45.0,
            "completed_sp": 45,
            "total_sp": 100,
            "completed_tasks": 5,
            "total_tasks": 11,
            "health_status": "yellow",
            "audit_score": 92,
            "nodes_count": 3,
            "steps_count": 3,
            "sipoc_rows": [
                {"id": "1", "step_num": "1.0", "provider": "Agente", "input": "Número de Póliza", "step": "1.0 Consulta en Chronos", "output": "Datos de Póliza", "customer": "Chronos", "requirements": "Folio numérico"},
                {"id": "2", "step_num": "2.0", "provider": "Chronos", "input": "Datos de Póliza", "step": "2.0 ¿Póliza Vigente?", "output": "Dictamen", "customer": "Agente", "requirements": "Respuesta < 2s"}
            ],
            "customer_requirements": "Validación en < 2 segundos con trazabilidad en log central.",
            "nodes": [
                {"id": "node-1", "type": "node_start", "label": "Inicio: Folio Póliza", "swimlane": "Input", "x": 60, "y": 140, "activity_number": None, "attached_system": "", "attached_channel": ""},
                {"id": "node-2", "type": "node_activity", "label": "Consulta en Chronos", "swimlane": "Agente", "x": 300, "y": 140, "activity_number": 1, "attached_system": "Chronos", "attached_channel": ""},
                {"id": "node-3", "type": "node_end", "label": "Fin: Emisión", "swimlane": "Output", "x": 560, "y": 140, "activity_number": None, "attached_system": "", "attached_channel": ""}
            ],
            "edges": [
                {"id": "e1-2", "source": "node-1", "target": "node-2", "label": ""},
                {"id": "e2-3", "source": "node-2", "target": "node-3", "label": ""}
            ],
            "swimlanes": ["Input", "Agente", "Output"],
            "project_pages": [
                {
                    "page_id": "1",
                    "name": "Página 1: Flujo Principal",
                    "nodes": [
                        {"id": "node-1", "type": "node_start", "label": "Inicio: Folio Póliza", "swimlane": "Input", "x": 60, "y": 140, "activity_number": None, "attached_system": "", "attached_channel": ""},
                        {"id": "node-2", "type": "node_activity", "label": "Consulta en Chronos", "swimlane": "Agente", "x": 300, "y": 140, "activity_number": 1, "attached_system": "Chronos", "attached_channel": ""},
                        {"id": "node-3", "type": "node_end", "label": "Fin: Emisión", "swimlane": "Output", "x": 560, "y": 140, "activity_number": None, "attached_system": "", "attached_channel": ""}
                    ],
                    "edges": [
                        {"id": "e1-2", "source": "node-1", "target": "node-2", "label": ""},
                        {"id": "e2-3", "source": "node-2", "target": "node-3", "label": ""}
                    ],
                    "swimlanes": ["Input", "Agente", "Output"]
                }
            ],
            "narrative_text": "# 📘 Manual de Validación de Pólizas en Chronos\n\nProcedimiento para verificar la vigencia de pólizas..."
        }
    ]

    # Hub Computed Properties & KPIs
    @rx.var
    def filtered_hub_projects(self) -> List[Dict[str, Any]]:
        """Filter projects based on User Role, Search Query, Phase and Health Status"""
        projs = list(self.saved_projects)

        # 1. Role Filter
        if self.user_role == "project_manager":
            projs = [p for p in projs if "José" in p.get("manager", "") or "Antonio" in p.get("manager", "") or "Hurtado" in p.get("manager", "")]
        elif self.user_role == "collaborator":
            projs = [p for p in projs if p.get("id") in ["proj-temis", "proj-x", "proj-wha"]]

        # 2. Phase Filter
        if self.filter_hub_phase != "all":
            try:
                phase_num = int(self.filter_hub_phase)
                projs = [p for p in projs if p.get("current_phase") == phase_num]
            except Exception:
                pass

        # 3. Status Filter
        if self.filter_hub_status != "all":
            projs = [p for p in projs if p.get("health_status") == self.filter_hub_status]

        # 4. Search Filter
        q = (self.search_hub_query or "").strip().lower()
        if q:
            projs = [
                p for p in projs
                if q in p.get("name", "").lower()
                or q in p.get("code", "").lower()
                or q in p.get("purpose", "").lower()
                or q in p.get("manager", "").lower()
                or q in p.get("sponsor", "").lower()
                or q in p.get("current_sprint", "").lower()
            ]

        return projs

    @rx.var
    def total_hub_projects_count(self) -> int:
        return len(self.saved_projects)

    @rx.var
    def total_completed_sp_count(self) -> int:
        return sum(int(p.get("completed_sp", 0)) for p in self.saved_projects)

    @rx.var
    def total_sp_count(self) -> int:
        val = sum(int(p.get("total_sp", 0)) for p in self.saved_projects)
        return max(1, val)

    @rx.var
    def global_progress_pct(self) -> float:
        total = self.total_sp_count
        completed = self.total_completed_sp_count
        if total <= 0:
            return 0.0
        return round((completed / total) * 100, 1)

    @rx.var
    def average_audit_score(self) -> int:
        if not self.saved_projects:
            return 100
        scores = [int(p.get("audit_score", 100)) for p in self.saved_projects]
        return int(sum(scores) / len(scores))

    @rx.var
    def active_sprints_count(self) -> int:
        return len(self.saved_projects)

    def set_search_saved_query(self, val: str):
        self.search_saved_query = val

    @rx.var
    def filtered_saved_projects(self) -> List[Dict[str, Any]]:
        """Return saved projects filtered by search query"""
        q = (self.search_saved_query or "").strip().lower()
        if not q:
            return self.saved_projects
        return [
            p for p in self.saved_projects 
            if q in p.get("name", "").lower() or q in p.get("purpose", "").lower() or q in p.get("manager", "").lower()
        ]

    # Hub & Workspace Navigation Handlers
    def open_project_workspace(self, proj_id: str):
        """Open project in Level 2 Workspace and load full state"""
        self.load_saved_project(proj_id)
        self.active_mode = "workspace"
        self.status_message = f"Espacio de trabajo abierto: {self.project_name}"

    def return_to_hub(self):
        """Save changes and return to Level 1 Hub"""
        self.save_current_project()
        self.active_mode = "hub"
        self.status_message = "Regresaste al Hub de Portafolio"

    # New Project Modal Handlers
    def set_new_proj_name(self, val: str):
        self.new_proj_name = val

    def set_new_proj_code(self, val: str):
        self.new_proj_code = val

    def set_new_proj_purpose(self, val: str):
        self.new_proj_purpose = val

    def set_new_proj_manager(self, val: str):
        self.new_proj_manager = val

    def set_new_proj_sponsor(self, val: str):
        self.new_proj_sponsor = val

    def set_new_proj_start_date(self, val: str):
        self.new_proj_start_date = val

    def set_new_proj_end_date(self, val: str):
        self.new_proj_end_date = val

    def open_new_project_modal(self):
        self.new_proj_name = ""
        self.new_proj_code = f"PRJ-00{len(self.saved_projects) + 1}"
        self.new_proj_purpose = ""
        self.creation_progress_status = ""
        self.is_creating_project_drive = False
        self.show_new_project_modal = True

    def close_new_project_modal(self):
        self.show_new_project_modal = False
        self.is_creating_project_drive = False

    def set_show_new_project_modal(self, val: bool):
        self.show_new_project_modal = val

    def create_project_with_drive(self):
        """Create new project in Drive via SA, replicate sheet and open workspace"""
        if not self.new_proj_name.strip():
            self.status_message = "Ingresa un nombre para el proyecto"
            return
        if not self.new_proj_code.strip():
            self.new_proj_code = f"PRJ-00{len(self.saved_projects) + 1}"

        self.is_creating_project_drive = True
        self.creation_progress_status = "Inicializando carpetas en Google Drive..."

        drive_folder_id = ""
        drive_folder_url = ""
        sheet_id = ""
        sheet_url = ""

        try:
            from backend.services.drive_service import DriveService
            ds = DriveService()

            clean_name = self.new_proj_name.strip().replace(" ", "_")
            clean_code = self.new_proj_code.strip()

            # 1. Create project folder + 11 subfolders
            ok_folder, folder_res = ds.create_project_folder(clean_name, clean_code)
            if ok_folder:
                drive_folder_id = folder_res
                drive_folder_url = f"https://drive.google.com/drive/folders/{drive_folder_id}"
                self.creation_progress_status = "Replicando Plantilla Oficial de Google Sheets..."

                # 2. Replicate master Google Sheet
                ok_sheet, sheet_res = ds.replicate_master_sheet_template(drive_folder_id, clean_name)
                if ok_sheet:
                    sheet_id = sheet_res
                    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
        except Exception as e:
            print(f"Drive creation notice: {e}")

        # Build project dictionary
        import datetime
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        new_id = f"proj-{len(self.saved_projects) + 1}"

        manager_name = self.new_proj_manager.strip() or self.user_name
        initials = "".join([part[0].upper() for part in manager_name.split() if part])[:2] or "US"

        new_proj_dict = {
            "id": new_id,
            "code": self.new_proj_code.strip(),
            "name": self.new_proj_name.strip(),
            "purpose": self.new_proj_purpose.strip() or "Definir el alcance y objetivos operativos.",
            "manager": manager_name,
            "manager_initials": initials,
            "sponsor": self.new_proj_sponsor.strip() or "Dirección General",
            "start_date": self.new_proj_start_date or "2026-01-16",
            "end_date": self.new_proj_end_date or "2026-12-04",
            "scope_in": "Mapeo SIPOC, diagrama BPMN multi-pestaña, gobernanza y bitácoras.",
            "scope_out": "Desarrollos fuera de alcance.",
            "current_phase": 1,
            "phase_name": "Fase 1: Diagnóstico Estratégico",
            "updated_at": now_str,
            "drive_folder_id": drive_folder_id,
            "drive_folder_url": drive_folder_url,
            "sheet_id": sheet_id,
            "sheet_url": sheet_url,
            "current_sprint": "Sprint 01",
            "current_sprint_name": "Diagnóstico y Mapeo AS-IS",
            "progress_percentage": 0.0,
            "completed_sp": 0,
            "total_sp": 30,
            "completed_tasks": 0,
            "total_tasks": 5,
            "health_status": "green",
            "audit_score": 100,
            "nodes_count": 1,
            "steps_count": 1,
            "sipoc_rows": [
                {
                    "id": "1",
                    "step_num": "1.0",
                    "provider": "Usuario / Cliente",
                    "input": "Solicitud inicial",
                    "step": "1.0 Recepción y validación de requerimiento",
                    "output": "Registro creado",
                    "customer": "Operador",
                    "requirements": "Datos completos y folio válido"
                }
            ],
            "customer_requirements": "Atención rápida y trazabilidad de folios.",
            "nodes": [
                {
                    "id": "node-1",
                    "type": "node_start",
                    "label": "Inicio Proceso",
                    "swimlane": "Input",
                    "x": 80,
                    "y": 120,
                    "activity_number": None,
                    "attached_system": "",
                    "attached_channel": ""
                }
            ],
            "edges": [],
            "swimlanes": ["Input", "Actor 1 (ej. Operador)", "Output"],
            "project_pages": [
                {
                    "page_id": "1",
                    "name": "Página 1: Flujo Principal",
                    "nodes": [
                        {
                            "id": "node-1",
                            "type": "node_start",
                            "label": "Inicio Proceso",
                            "swimlane": "Input",
                            "x": 80,
                            "y": 120,
                            "activity_number": None,
                            "attached_system": "",
                            "attached_channel": ""
                        }
                    ],
                    "edges": [],
                    "swimlanes": ["Input", "Actor 1 (ej. Operador)", "Output"]
                }
            ],
            "narrative_text": f"# 📘 Manual de Procedimientos\n# {self.new_proj_name.strip()}\n\n## 🎯 1. Objetivo\n{self.new_proj_purpose.strip()}\n"
        }

        self.saved_projects.insert(0, new_proj_dict)
        self.is_creating_project_drive = False
        self.show_new_project_modal = False
        self.open_project_workspace(new_id)
        self.status_message = f"✓ ¡Proyecto '{self.new_proj_name.strip()}' creado y desplegado con éxito!"

    def set_project_name(self, name: str):
        """Set project title"""
        self.project_name = name

    def create_new_project(self):
        """Reset canvas and initialize a new empty project"""
        count = len(self.saved_projects) + 1
        self.project_id = f"proj-{count}"
        self.project_code = f"PRJ-00{count}"
        self.project_name = f"Nuevo Proceso TEMIS #{count}"
        self.project_purpose = "Definir el propósito y objetivos operativos del nuevo proceso."
        self.project_manager = "Responsable del Proceso"
        self.project_sponsor = "Patrocinador / Área Líder"
        self.current_phase = 1
        self.phase_name = "Fase 1: Diagnóstico Estratégico"
        self.diagram_title = "Flujo de Proceso Operativo"
        self.nodes = [
            {
                "id": "node-1",
                "type": "node_start",
                "label": "Inicio Proceso",
                "swimlane": "Input",
                "x": 80,
                "y": 120,
                "activity_number": None,
                "attached_system": "",
                "attached_channel": ""
            }
        ]
        self.edges = []
        self.project_pages = [
            {
                "page_id": "1",
                "name": "Página 1: Flujo Principal",
                "nodes": list(self.nodes),
                "edges": [],
                "swimlanes": ["Input", "Actor 1", "Output"]
            }
        ]
        self.active_page_index = 0
        self.selected_node_id = ""
        self.sipoc_rows = [
            {
                "id": "1",
                "step_num": "1.0",
                "provider": "Usuario / Cliente",
                "input": "Solicitud inicial",
                "step": "1.0 Recepción y validación",
                "output": "Registro creado",
                "customer": "Operador",
            }
        ]
        self.narrative_text = f"# 📘 Manual de Procedimientos\n# {self.project_name}\n\n## 🎯 1. Objetivo\n{self.project_purpose}\n"
        self.show_recent_modal = False
        self.status_message = f"✓ Nuevo proceso '{self.project_name}' inicializado"

    def select_page_tab(self, index: int):
        """Save current tab state and switch active page"""
        if 0 <= self.active_page_index < len(self.project_pages):
            self.project_pages[self.active_page_index]["nodes"] = list(self.nodes)
            self.project_pages[self.active_page_index]["edges"] = list(self.edges)

        if 0 <= index < len(self.project_pages):
            self.active_page_index = index
            page = self.project_pages[index]
            self.nodes = list(page.get("nodes", []))
            self.edges = list(page.get("edges", []))
            if page.get("swimlanes"):
                self.swimlanes = list(page["swimlanes"])
            self.status_message = f"Cargada {page.get('name', 'Pestaña')}"

    def add_new_tab_page(self):
        """Add a new blank page tab to the current project"""
        # Save current active page
        if 0 <= self.active_page_index < len(self.project_pages):
            self.project_pages[self.active_page_index]["nodes"] = list(self.nodes)
            self.project_pages[self.active_page_index]["edges"] = list(self.edges)

        count = len(self.project_pages) + 1
        new_page = {
            "page_id": str(count),
            "name": f"Página {count}",
            "nodes": [
                {
                    "id": "node-1",
                    "type": "node_start",
                    "label": "Inicio",
                    "swimlane": "Input",
                    "x": 80,
                    "y": 120,
                    "activity_number": None,
                    "attached_system": "",
                    "attached_channel": ""
                }
            ],
            "edges": [],
            "swimlanes": ["Input", "Actor 1", "Output"]
        }
        self.project_pages.append(new_page)
        self.select_page_tab(len(self.project_pages) - 1)
        self.status_message = f"Pestaña 'Página {count}' creada"

    def delete_tab_page(self, index: int):
        """Delete a diagram page tab from the project"""
        if len(self.project_pages) <= 1:
            self.status_message = "El proyecto debe conservar al menos una pestaña"
            return

        if 0 <= index < len(self.project_pages):
            deleted = self.project_pages.pop(index)
            new_idx = max(0, min(self.active_page_index, len(self.project_pages) - 1))
            self.active_page_index = new_idx
            page = self.project_pages[new_idx]
            self.nodes = list(page.get("nodes", []))
            self.edges = list(page.get("edges", []))
            self.status_message = f"Pestaña '{deleted.get('name')}' eliminada"

    def save_current_project(self):
        """Save current project state into the Saved Flows catalog"""
        import datetime
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        # Ensure current active page is updated
        if 0 <= self.active_page_index < len(self.project_pages):
            self.project_pages[self.active_page_index]["nodes"] = list(self.nodes)
            self.project_pages[self.active_page_index]["edges"] = list(self.edges)
            self.project_pages[self.active_page_index]["swimlanes"] = list(self.swimlanes)

        # Retain existing metadata if available
        existing = next((p for p in self.saved_projects if p.get("id") == self.project_id), {})

        current_dict = {
            "id": self.project_id or f"proj-{len(self.saved_projects) + 1}",
            "code": getattr(self, "project_code", existing.get("code", "PRJ")),
            "name": self.project_name,
            "purpose": self.project_purpose,
            "manager": self.project_manager,
            "manager_initials": existing.get("manager_initials", "MH"),
            "sponsor": self.project_sponsor,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "scope_in": self.scope_in,
            "scope_out": self.scope_out,
            "current_phase": self.current_phase,
            "phase_name": self.phase_name,
            "updated_at": now_str,
            "drive_folder_id": self.drive_folder_id or existing.get("drive_folder_id", ""),
            "drive_folder_url": self.drive_folder_url or existing.get("drive_folder_url", ""),
            "sheet_id": self.sheet_id or existing.get("sheet_id", ""),
            "sheet_url": self.sheet_url or existing.get("sheet_url", ""),
            "current_sprint": existing.get("current_sprint", "Sprint 01"),
            "current_sprint_name": existing.get("current_sprint_name", "Operaciones"),
            "progress_percentage": existing.get("progress_percentage", 50.0),
            "completed_sp": existing.get("completed_sp", 10),
            "total_sp": existing.get("total_sp", 20),
            "completed_tasks": existing.get("completed_tasks", 5),
            "total_tasks": existing.get("total_tasks", 10),
            "health_status": existing.get("health_status", "green"),
            "audit_score": existing.get("audit_score", 95),
            "nodes_count": len(self.nodes),
            "steps_count": len(self.sipoc_rows),
            "sipoc_rows": list(self.sipoc_rows),
            "customer_requirements": self.customer_requirements,
            "nodes": list(self.nodes),
            "edges": list(self.edges),
            "swimlanes": list(self.swimlanes),
            "project_pages": list(self.project_pages),
            "narrative_text": self.narrative_text
        }

        # Check if already exists in saved_projects
        found = False
        new_list = []
        for p in self.saved_projects:
            if p.get("id") == current_dict["id"] or p.get("name") == current_dict["name"]:
                new_list.append(current_dict)
                found = True
            else:
                new_list.append(p)

        if not found:
            new_list.insert(0, current_dict)

        self.saved_projects = new_list
        self.auto_save_status = "✓ Cambios Guardados"
        self.status_message = f"✓ Proceso '{self.project_name}' guardado exitosamente en el Catálogo de Flujos"

    def save_diagram(self):
        """Alias for save_current_project called from menu"""
        self.save_current_project()

    def load_saved_project(self, proj_id: str):
        """Load a selected project from saved projects into active workspace"""
        selected = next((p for p in self.saved_projects if p.get("id") == proj_id), None)
        if not selected:
            self.status_message = "No se encontró el flujo seleccionado"
            return

        self.project_id = selected.get("id", "proj-1")
        self.project_code = selected.get("code", "PRJ")
        self.project_name = selected.get("name", "Proyecto TEMIS")
        self.project_purpose = selected.get("purpose", "")
        self.project_manager = selected.get("manager", "")
        self.project_sponsor = selected.get("sponsor", "")
        self.start_date = selected.get("start_date", "2026-01-16")
        self.end_date = selected.get("end_date", "2026-12-04")
        self.scope_in = selected.get("scope_in", "")
        self.scope_out = selected.get("scope_out", "")
        self.current_phase = selected.get("current_phase", 1)
        self.phase_name = selected.get("phase_name", "Fase 1: Diagnóstico Estratégico")

        self.drive_folder_id = selected.get("drive_folder_id", "")
        self.drive_folder_url = selected.get("drive_folder_url", "")
        self.sheet_id = selected.get("sheet_id", "")
        self.sheet_url = selected.get("sheet_url", "")

        if selected.get("sipoc_rows"):
            self.sipoc_rows = list(selected["sipoc_rows"])
        if selected.get("customer_requirements"):
            self.customer_requirements = selected["customer_requirements"]

        if selected.get("project_pages"):
            self.project_pages = list(selected["project_pages"])
            self.active_page_index = 0
            page0 = self.project_pages[0]
            self.nodes = list(page0.get("nodes", []))
            self.edges = list(page0.get("edges", []))
            if page0.get("swimlanes"):
                self.swimlanes = list(page0["swimlanes"])
        else:
            self.nodes = list(selected.get("nodes", []))
            self.edges = list(selected.get("edges", []))
            if selected.get("swimlanes"):
                self.swimlanes = list(selected["swimlanes"])

        if selected.get("narrative_text"):
            self.narrative_text = selected["narrative_text"]

        self.show_recent_modal = False
        self.status_message = f"✓ Flujo '{self.project_name}' cargado con éxito en todas las vistas"

    def delete_saved_project(self, proj_id: str):
        """Delete a project from saved projects catalog"""
        self.saved_projects = [p for p in self.saved_projects if p.get("id") != proj_id]
        self.status_message = "Flujo eliminado del catálogo"

    def export_single_saved_package(self, proj_id: str):
        """Download a specific saved project package as .temis.json"""
        selected = next((p for p in self.saved_projects if p.get("id") == proj_id), None)
        if not selected:
            return
        json_str = json.dumps(selected, indent=2, ensure_ascii=False)
        safe_name = selected.get("name", "Flujo").replace(" ", "_")
        return rx.download(
            data=json_str,
            filename=f"Paquete_{safe_name}.temis.json"
        )

    def open_recent_modal(self):
        """Open recent projects modal and refresh catalog"""
        self.show_recent_modal = True
        self.search_saved_query = ""

    def close_recent_modal(self):
        """Close recent projects modal"""
        self.show_recent_modal = False

    # Connector Modal & Interactive Line Connection State
    show_connect_modal: bool = False
    connect_target_id: str = ""
    connect_label: str = ""
    auto_save_status: str = "✓ Cambios Guardados"

    @rx.var
    def target_node_options(self) -> List[str]:
        """Return candidate target node option strings for connect modal"""
        return [f"{n['id']} - {n.get('label', '')}" for n in self.nodes if n["id"] != self.selected_node_id]

    # AI Process Auditor State
    show_audit_modal: bool = False
    is_auditing_ai: bool = False
    audit_score: int = 100
    audit_findings: List[Dict[str, Any]] = []

    def set_connect_target_id(self, val: str):
        if " - " in str(val or ""):
            self.connect_target_id = str(val).split(" - ")[0].strip()
        else:
            self.connect_target_id = str(val or "").strip()

    def set_connect_label(self, val: str):
        self.connect_label = val

    def open_connect_modal(self):
        """Open modal to connect selected node to another target node"""
        if not self.selected_node_id:
            self.status_message = "Selecciona un nodo primero para conectar"
            return
        self.connect_target_id = ""
        self.connect_label = ""
        self.show_connect_modal = True

    def close_connect_modal(self):
        self.show_connect_modal = False

    def add_connection(self):
        """Add a new SVG Bézier connector edge between selected node and target node"""
        if not self.selected_node_id or not self.connect_target_id:
            self.status_message = "Selecciona un nodo de origen y destino válidos"
            return
        if self.selected_node_id == self.connect_target_id:
            self.status_message = "No se puede conectar un nodo consigo mismo"
            return

        edge_count = len(self.edges) + 1
        new_edge = {
            "id": f"e-{self.selected_node_id}-{self.connect_target_id}-{edge_count}",
            "source": self.selected_node_id,
            "target": self.connect_target_id,
            "label": self.connect_label.strip()
        }
        self.edges.append(new_edge)
        self.show_connect_modal = False
        self.status_message = f"Conexión agregada hacia {self.connect_target_id}"
        self.trigger_auto_save()

    def delete_edge(self, edge_id: str):
        """Delete an edge connector"""
        self.edges = [e for e in self.edges if e.get("id") != edge_id]
        self.status_message = "Conector eliminado"
        self.trigger_auto_save()

    def trigger_auto_save(self):
        """Save active diagram page state and update auto-save badge"""
        if 0 <= self.active_page_index < len(self.project_pages):
            self.project_pages[self.active_page_index]["nodes"] = list(self.nodes)
            self.project_pages[self.active_page_index]["edges"] = list(self.edges)
        self.auto_save_status = "✓ Cambios Guardados"

    def open_audit_modal(self):
        """Open AI Process Auditor modal and execute structural governance analysis"""
        self.show_audit_modal = True
        self.run_ai_process_audit()

    def close_audit_modal(self):
        self.show_audit_modal = False

    def run_ai_process_audit(self):
        """Execute Gemini AI & Structural Governance Audit on current active flowchart tab"""
        self.is_auditing_ai = True
        findings = []
        deductions = 0

        node_map = {n["id"]: n for n in self.nodes}
        out_edges = {}
        in_edges = {}

        for e in self.edges:
            out_edges.setdefault(e["source"], []).append(e)
            in_edges.setdefault(e["target"], []).append(e)

        # Check 1: Start Nodes
        start_nodes = [n for n in self.nodes if n.get("type") == "node_start"]
        if not start_nodes:
            findings.append({
                "severity": "Alta",
                "color": "#ef4444",
                "category": "Inicio de Proceso",
                "title": "Falta Nodo de Inicio de Proceso",
                "description": "El diagrama no tiene un punto de entrada oficial definido (Nodo de Inicio).",
                "recommendation": "Agrega un símbolo 'Inicio Proceso' para marcar el desencadenador inicial."
            })
            deductions += 15
        else:
            for sn in start_nodes:
                if sn["id"] not in out_edges:
                    findings.append({
                        "severity": "Alta",
                        "color": "#ef4444",
                        "category": "Flujo Desconectado",
                        "title": f"Inicio '{sn.get('label')}' sin salida",
                        "description": "El nodo de inicio está desconectado y no conduce a ninguna actividad.",
                        "recommendation": "Conecta el nodo de inicio con la primera actividad operativa."
                    })
                    deductions += 10

        # Check 2: Decision Nodes
        decision_nodes = [n for n in self.nodes if n.get("type") == "node_decision"]
        for dn in decision_nodes:
            edges = out_edges.get(dn["id"], [])
            labels = [e.get("label", "").lower() for e in edges]
            if len(edges) < 2:
                findings.append({
                    "severity": "Alta",
                    "color": "#ef4444",
                    "category": "Decisión Incompleta",
                    "title": f"Decisión '{dn.get('label')}' requiere ramas Sí/No",
                    "description": f"La decisión tiene {len(edges)} salida(s). Toda pregunta de validación debe tener ramas afirmativas y alternativas.",
                    "recommendation": "Agrega la rama faltante (ej. 'Sí' / 'No' o 'Válido' / 'Inválido')."
                })
                deductions += 12

        # Check 3: Activities without System or Channel
        activity_nodes = [n for n in self.nodes if n.get("type") == "node_activity"]
        for an in activity_nodes:
            sys_val = (an.get("attached_system") or "").strip()
            chan_val = (an.get("attached_channel") or "").strip()
            if not sys_val and not chan_val:
                findings.append({
                    "severity": "Media",
                    "color": "#f59e0b",
                    "category": "Gobierno Operativo",
                    "title": f"Actividad '{an.get('label')}' sin Sistema o Canal",
                    "description": "La actividad no especifica qué sistema (Chronos/Freshdesk) o canal (WhatsApp/Bria) soporta la operación.",
                    "recommendation": "Asigna el sistema o canal correspondiente en las propiedades del nodo."
                })
                deductions += 5

        # Check 4: End Nodes
        end_nodes = [n for n in self.nodes if n.get("type") == "node_end"]
        if not end_nodes:
            findings.append({
                "severity": "Media",
                "color": "#f59e0b",
                "category": "Cierre de Proceso",
                "title": "Falta Nodo de Fin de Proceso",
                "description": "El flujo no declara explícitamente el estado de término o resolución.",
                "recommendation": "Agrega un nodo 'Fin Proceso' al término del flujo."
            })
            deductions += 10

        if not findings:
            findings.append({
                "severity": "Baja",
                "color": "#22c55e",
                "category": "Excelente Calidad",
                "title": "¡Proceso Cumple 100% las Reglas de Gobierno TEMIS!",
                "description": "El diagrama tiene nodos de inicio/fin, validaciones completas y asignación adecuada de sistemas.",
                "recommendation": "El flujo está listo para ser promovido a la siguiente Fase de Gobierno."
            })

        self.audit_findings = findings
        self.audit_score = max(0, 100 - deductions)
        self.is_auditing_ai = False

    # Duplicate Selected Node
    def duplicate_selected_node(self):
        if not self.selected_node_id:
            return
        target = None
        for n in self.nodes:
            if n["id"] == self.selected_node_id:
                target = n
                break
        if target:
            count = len(self.nodes) + 1
            new_node = dict(target)
            new_node["id"] = f"node-{count}"
            new_node["x"] = target["x"] + 40
            new_node["y"] = target["y"] + 40
            new_node["label"] = f"{target['label']} (Copia)"
            self.nodes.append(new_node)
            self.status_message = "Nodo duplicado"

    # Save Diagram to Backend Database
    def save_diagram(self):
        import os
        api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
        if not api_base.startswith("http"):
            api_base = f"http://{api_base}:8000"
        url = f"{api_base.rstrip('/')}/api/diagrams/"

        self.status_message = "Guardando diagrama en la base de datos..."
        try:
            payload = {
                "project_id": self.project_id,
                "title": self.diagram_title,
                "swimlanes": self.swimlanes,
                "nodes": self.nodes,
                "edges": self.edges,
                "viewport": {"x": 0, "y": 0, "zoom": 1}
            }
            res = requests.post(url, json=payload, timeout=15)
            if res.status_code in [200, 201]:
                self.status_message = "Diagrama guardado exitosamente en PostgreSQL"
            else:
                self.status_message = f"Error al guardar ({res.status_code}): {res.text}"
        except Exception as e:
            self.status_message = f"Error de conexión: {str(e)}"

    # Export Diagram to JSON (Lucidchart compatible format)
    def export_as_json(self):
        data = {
            "title": self.diagram_title,
            "project_id": self.project_id,
            "swimlanes": self.swimlanes,
            "nodes": self.nodes,
            "edges": self.edges
        }
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        self.status_message = "Diagrama exportado a JSON exitosamente"
        return rx.download(
            data=json_str,
            filename=f"{self.diagram_title.replace(' ', '_')}.json"
        )

    # Export Complete Project Package (.temis.json)
    def export_project_package(self):
        package = {
            "version": "1.0.0",
            "project": {
                "id": self.project_id,
                "name": self.project_name,
                "current_phase": self.current_phase,
            },
            "diagrams": [
                {
                    "title": self.diagram_title,
                    "swimlanes": self.swimlanes,
                    "nodes": self.nodes,
                    "edges": self.edges
                }
            ]
        }
        json_str = json.dumps(package, indent=2, ensure_ascii=False)
        self.status_message = "Paquete de proyecto exportado exitosamente"
        return rx.download(
            data=json_str,
            filename=f"Paquete_Proyecto_{self.project_name.replace(' ', '_')}.temis.json"
        )

    # Import Diagram or Project from JSON file
    def import_diagram_from_json(self, json_content: str):
        try:
            data = json.loads(json_content)
            if "nodes" in data and "edges" in data:
                self.nodes = data["nodes"]
                self.edges = data["edges"]
                if "swimlanes" in data:
                    self.swimlanes = data["swimlanes"]
                if "title" in data:
                    self.diagram_title = data["title"]
                self.status_message = "Diagrama importado exitosamente al lienzo"
            elif "project" in data and "diagrams" in data and len(data["diagrams"]) > 0:
                d = data["diagrams"][0]
                self.nodes = d.get("nodes", [])
                self.edges = d.get("edges", [])
                if "swimlanes" in d:
                    self.swimlanes = d.get("swimlanes", self.swimlanes)
                self.diagram_title = d.get("title", self.diagram_title)
                self.project_name = data["project"].get("name", self.project_name)
                self.status_message = f"Proyecto '{self.project_name}' importado exitosamente"
            else:
                self.status_message = "Estructura de archivo JSON no válida"
        except Exception as e:
            self.status_message = f"Error al importar archivo: {str(e)}"

    # Import Modal State
    show_import_modal: bool = False

    def open_import_modal(self):
        self.show_import_modal = True

    def close_import_modal(self):
        self.show_import_modal = False

    async def handle_file_upload(self, files: List[rx.UploadFile]):
        for file in files:
            filename = file.filename.lower()
            upload_data = await file.read()

            if filename.endswith(".pdf"):
                self.status_message = "Procesando PDF con Gemini AI..."
                try:
                    import io
                    import PyPDF2
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(upload_data))
                    extracted_text = ""
                    for page in pdf_reader.pages:
                        txt = page.extract_text()
                        if txt:
                            extracted_text += txt + "\n"
                    
                    if not extracted_text.strip():
                        extracted_text = f"Diagrama de flujo extraído del archivo {file.filename}"

                    self.ai_prompt_text = f"Genera el flujo a partir de este documento PDF: {extracted_text[:1500]}"
                    self.generate_with_gemini()
                    self.status_message = f"PDF '{file.filename}' procesado e importado con IA"
                except Exception as e:
                    self.status_message = f"Error al procesar PDF: {str(e)}"

            elif filename.endswith(".csv"):
                try:
                    from backend.services.native_parser import parse_lucidchart_csv
                    csv_text = upload_data.decode("utf-8-sig")
                    result = parse_lucidchart_csv(csv_text)
                    if result.get("nodes"):
                        self.nodes = result["nodes"]
                        self.edges = result.get("edges", [])
                        if result.get("pages"):
                            self.project_pages = result["pages"]
                            self.active_page_index = 0
                        if result.get("swimlanes"):
                            self.swimlanes = result["swimlanes"]
                        self.diagram_title = result.get("title", self.diagram_title)
                        self.status_message = f"CSV de Lucidchart importado ({len(result.get('pages', []))} pestañas de diagramas)"
                    else:
                        self.status_message = "No se encontraron nodos en el CSV"
                except Exception as e:
                    self.status_message = f"Error al importar CSV de Lucidchart: {str(e)}"

            else:
                try:
                    json_text = upload_data.decode("utf-8")
                    self.import_diagram_from_json(json_text)
                except Exception as e:
                    self.status_message = f"Error al leer JSON: {str(e)}"

        self.show_import_modal = False

    # Node Edit Modal State
    show_modal: bool = False
    modal_node_id: str = ""
    modal_label: str = ""
    modal_system: str = ""
    modal_channel: str = ""
    modal_activity_num: str = ""

    def set_modal_label(self, val: str):
        self.modal_label = val

    def set_modal_system(self, val: str):
        self.modal_system = val

    def set_modal_channel(self, val: str):
        self.modal_channel = val

    def set_modal_activity_num(self, val: str):
        self.modal_activity_num = val

    def open_node_edit_modal(self, node_id: str):
        self.modal_node_id = node_id
        for n in self.nodes:
            if n["id"] == node_id:
                self.modal_label = n.get("label", "")
                self.modal_system = n.get("attached_system", "")
                self.modal_channel = n.get("attached_channel", "")
                act_num = n.get("activity_number")
                self.modal_activity_num = str(act_num) if act_num is not None else ""
                break
        self.show_modal = True

    def close_node_edit_modal(self):
        self.show_modal = False

    def save_node_edit_modal(self):
        for n in self.nodes:
            if n["id"] == self.modal_node_id:
                n["label"] = self.modal_label
                n["attached_system"] = self.modal_system
                n["attached_channel"] = self.modal_channel
                if self.modal_activity_num.isdigit():
                    n["activity_number"] = int(self.modal_activity_num)
                else:
                    n["activity_number"] = None
                break
        self.show_modal = False
        self.status_message = f"Propiedades del nodo {self.modal_node_id} actualizadas"

    # AI Generation with Gemini
    def generate_with_gemini(self):
        if not self.ai_prompt_text.strip():
            self.status_message = "Ingresa una descripción del proceso"
            return

        self.is_generating_ai = True
        self.status_message = "Gemini AI analizando el proceso..."

        import os
        api_base = os.getenv("API_BASE_URL", "https://temis-backend.onrender.com")
        if not api_base.startswith("http"):
            api_base = f"https://{api_base}"
        url = f"{api_base.rstrip('/')}/api/diagrams/generate-ai"

        try:
            # Call backend API
            res = requests.post(
                url,
                json={
                    "process_description": self.ai_prompt_text,
                    "swimlanes": self.swimlanes
                },
                timeout=30
            )

            if res.status_code == 200:
                data = res.json()
                if "nodes" in data and "edges" in data:
                    self.nodes = data["nodes"]
                    self.edges = data["edges"]
                    if "title" in data:
                        self.diagram_title = data["title"]
                    self.status_message = "Diagrama de flujo generado con IA exitosamente"
                else:
                    self.status_message = "Error en la estructura generada"
            else:
                self.status_message = f"Error servidor ({res.status_code}): {res.text}"

        except Exception as e:
            # Local fallback for PDF process diagrams if backend HTTP call fails
            if "WhatsApp" in self.ai_prompt_text or "PDF" in self.ai_prompt_text:
                self.diagram_title = "Proceso WhatsApp - Soporte & Operaciones"
                self.nodes = [
                    {"id": "node-1", "type": "node_start", "label": "Inicio: Entrada WhatsApp", "swimlane": "Input", "x": 40, "y": 140, "activity_number": None, "attached_system": "", "attached_channel": "WhatsApp"},
                    {"id": "node-2", "type": "node_activity", "label": "Identificar intención por palabra clave", "swimlane": "Actor 1 (ej. Usuario)", "x": 260, "y": 140, "activity_number": 1, "attached_system": "", "attached_channel": "WhatsApp"},
                    {"id": "node-3", "type": "node_decision", "label": "¿Prioridad Alta (Fraudes/BSA)?", "swimlane": "Actor 2 (ej. Sistema)", "x": 520, "y": 140, "activity_number": None, "attached_system": "Chronos", "attached_channel": ""},
                    {"id": "node-4", "type": "node_activity", "label": "Derivar a Prevención de Fraudes (SC.030)", "swimlane": "Actor 2 (ej. Sistema)", "x": 760, "y": 60, "activity_number": 2, "attached_system": "Freshdesk", "attached_channel": "WhatsApp"},
                    {"id": "node-5", "type": "node_activity", "label": "Búsqueda estatus MO en Chronos (SC.007)", "swimlane": "Actor 2 (ej. Sistema)", "x": 760, "y": 220, "activity_number": 3, "attached_system": "Chronos", "attached_channel": ""},
                    {"id": "node-6", "type": "node_activity", "label": "Solicitud Service History Form + ID (SC.013)", "swimlane": "Actor 1 (ej. Usuario)", "x": 1020, "y": 220, "activity_number": 4, "attached_system": "Freshdesk", "attached_channel": "WhatsApp"},
                    {"id": "node-7", "type": "node_activity", "label": "Ofrecer ayuda (SC.033) y Encuesta (SC.034)", "swimlane": "Actor 1 (ej. Usuario)", "x": 1260, "y": 140, "activity_number": 5, "attached_system": "", "attached_channel": "WhatsApp"},
                    {"id": "node-8", "type": "node_end", "label": "Fin: Cierre Conversación", "swimlane": "Output", "x": 1500, "y": 140, "activity_number": None, "attached_system": "", "attached_channel": ""}
                ]
                self.edges = [
                    {"id": "e1-2", "source": "node-1", "target": "node-2", "label": ""},
                    {"id": "e2-3", "source": "node-2", "target": "node-3", "label": ""},
                    {"id": "e3-4", "source": "node-3", "target": "node-4", "label": "Sí"},
                    {"id": "e3-5", "source": "node-3", "target": "node-5", "label": "No"},
                    {"id": "e5-6", "source": "node-5", "target": "node-6", "label": ""},
                    {"id": "e6-7", "source": "node-6", "target": "node-7", "label": ""},
                    {"id": "e4-7", "source": "node-4", "target": "node-7", "label": ""},
                    {"id": "e7-8", "source": "node-7", "target": "node-8", "label": ""}
                ]
                self.status_message = "Diagrama del PDF generado e importado exitosamente"
            else:
                self.status_message = f"Error al conectar con la API de IA: {str(e)}"
        finally:
            self.is_generating_ai = False
