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
    users_list: List[Dict[str, Any]] = []
    show_new_user_modal: bool = False
    new_user_name: str = ""
    new_user_email: str = ""
    new_user_role: str = "collaborator"
    new_user_department: str = ""
    new_user_password: str = ""
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

    def handle_login(self, form_data: dict = None):
        self.is_logging_in = True
        self.login_error_message = ""
        try:
            from backend.services.user_service import authenticate_user, load_users
            if form_data and isinstance(form_data, dict):
                email = form_data.get("email")
                password = form_data.get("password")
                if email:
                    self.login_email = email
                if password:
                    self.login_password = password
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

    # User Project Assignment & Deletion Modals State
    show_assign_projects_modal: bool = False
    assign_user_email: str = ""
    assign_user_name: str = ""
    assign_user_role: str = ""
    assign_user_projects: List[str] = []
    new_user_assigned_projects: List[str] = ["all"]

    show_delete_user_modal: bool = False
    user_to_delete_email: str = ""
    user_to_delete_name: str = ""
    user_to_delete_role: str = ""
    user_to_delete_department: str = ""
    user_to_delete_projects: str = ""

    show_delete_project_modal: bool = False
    project_to_delete_id: str = ""
    project_to_delete_name: str = ""
    project_to_delete_code: str = ""
    is_workspace_dirty: bool = False

    @rx.var
    def available_project_options(self) -> List[Dict[str, str]]:
        """List of available projects in portfolio for assignment"""
        return [{"code": str(p.get("code", "PRJ")), "name": str(p.get("name", "Proyecto"))} for p in self.saved_projects]

    @rx.var
    def assign_user_is_global(self) -> bool:
        return "all" in self.assign_user_projects

    @rx.var
    def new_user_is_global(self) -> bool:
        return "all" in self.new_user_assigned_projects

    def set_show_assign_projects_modal(self, val: bool):
        self.show_assign_projects_modal = val

    def open_assign_projects_modal(self, email: str):
        """Open modal to configure project access for a user"""
        user = next((u for u in self.users_list if u.get("email", "").strip().lower() == email.strip().lower()), None)
        if not user:
            self.status_message = f"No se encontró el usuario '{email}'"
            return
        self.assign_user_email = user.get("email", "")
        self.assign_user_name = user.get("name", "")
        self.assign_user_role = user.get("role", "collaborator")
        assigned = user.get("assigned_projects", [])
        if not assigned:
            if user.get("role") == "super_admin":
                assigned = ["all"]
            else:
                assigned = ["PRJ-TEMIS"]
        self.assign_user_projects = list(assigned)
        self.show_assign_projects_modal = True

    def close_assign_projects_modal(self):
        self.show_assign_projects_modal = False

    def toggle_assign_project(self, project_code: str):
        """Toggle project assignment in modal"""
        if project_code == "all":
            if "all" in self.assign_user_projects:
                self.assign_user_projects = []
            else:
                self.assign_user_projects = ["all"]
        else:
            current = [p for p in self.assign_user_projects if p != "all"]
            if project_code in current:
                current.remove(project_code)
            else:
                current.append(project_code)
            self.assign_user_projects = current

    def toggle_new_user_project(self, project_code: str):
        """Toggle project assignment in new user registration modal"""
        if project_code == "all":
            if "all" in self.new_user_assigned_projects:
                self.new_user_assigned_projects = []
            else:
                self.new_user_assigned_projects = ["all"]
        else:
            current = [p for p in self.new_user_assigned_projects if p != "all"]
            if project_code in current:
                current.remove(project_code)
            else:
                current.append(project_code)
            self.new_user_assigned_projects = current

    def save_user_projects_assignment(self):
        """Save project assignments for user"""
        try:
            from backend.services.user_service import update_user_projects, load_users
            ok, msg = update_user_projects(self.assign_user_email, self.assign_user_projects)
            if ok:
                self.users_list = load_users()
                self.show_assign_projects_modal = False
                self.status_message = f"{msg}"
                self.trigger_toast("Asignación de proyectos actualizada", "success")
            else:
                self.status_message = f"Error: {msg}"
                self.trigger_toast(f"Error: {msg}", "error")
        except Exception as e:
            self.status_message = f"Error al guardar asignación: {str(e)}"

    def prompt_delete_project(self, proj_id: str, proj_name: str, proj_code: str):
        """Open confirmation dialog to delete a project"""
        self.project_to_delete_id = proj_id
        self.project_to_delete_name = proj_name
        self.project_to_delete_code = proj_code
        self.show_delete_project_modal = True

    def close_delete_project_modal(self):
        self.show_delete_project_modal = False
        self.project_to_delete_id = ""
        self.project_to_delete_name = ""
        self.project_to_delete_code = ""

    def set_show_delete_project_modal(self, val: bool):
        self.show_delete_project_modal = val

    def confirm_delete_project(self):
        """Confirm and permanently remove project from catalog"""
        if not self.project_to_delete_id:
            return
        name = self.project_to_delete_name
        code = self.project_to_delete_code
        self.saved_projects = [p for p in self.saved_projects if p.get("id") != self.project_to_delete_id]
        self.show_delete_project_modal = False
        self.project_to_delete_id = ""
        self.project_to_delete_name = ""
        self.project_to_delete_code = ""
        self.status_message = f"Proyecto '{name}' ({code}) eliminado correctamente del portafolio"

    def open_new_user_modal(self):
        self.new_user_name = ""
        self.new_user_email = ""
        self.new_user_role = "collaborator"
        self.new_user_department = ""
        self.new_user_password = ""
        self.new_user_assigned_projects = ["all"] if self.new_user_role == "super_admin" else ["PRJ-TEMIS"]
        self.show_new_user_modal = True

    def set_new_user_name(self, val: str):
        self.new_user_name = val

    def set_new_user_email(self, val: str):
        self.new_user_email = val

    def set_new_user_role(self, val: str):
        self.new_user_role = str(val)
        if str(val) == "super_admin":
            self.new_user_assigned_projects = ["all"]

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
                password=self.new_user_password or "Temis123456*",
                assigned_projects=self.new_user_assigned_projects or ["all"]
            )
            if ok:
                self.users_list = load_users()
                self.show_new_user_modal = False
                self.new_user_password = ""
                self.status_message = f"{msg}"
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
                self.status_message = f"{msg}"
            else:
                self.status_message = f"Error: {msg}"
        except Exception as e:
            self.status_message = f"Error al actualizar rol: {str(e)}"

    def toggle_user_status_action(self, email: str):
        if email.strip().lower() == self.user_email.strip().lower():
            self.status_message = "No es posible desactivar tu propia cuenta Super Admin en sesión."
            return
        try:
            from backend.services.user_service import toggle_user_status, load_users
            ok, msg = toggle_user_status(email)
            if ok:
                self.users_list = load_users()
                self.status_message = f"{msg}"
            else:
                self.status_message = f"Error: {msg}"
        except Exception as e:
            self.status_message = f"Error: {str(e)}"

    def open_delete_user_modal(self, email: str):
        if email.strip().lower() == self.user_email.strip().lower():
            self.status_message = "No es posible eliminar tu propia cuenta Super Admin en sesión activa."
            self.trigger_toast("No puedes eliminar tu propia cuenta en sesión", "warning")
            return
        user = next((u for u in self.users_list if u.get("email", "").strip().lower() == email.strip().lower()), None)
        if not user:
            self.status_message = f"No se encontró el usuario '{email}'"
            return
        self.user_to_delete_email = user.get("email", "")
        self.user_to_delete_name = user.get("name", "")
        self.user_to_delete_role = user.get("role_label", user.get("role", "Colaborador"))
        self.user_to_delete_department = user.get("department", "General")
        self.user_to_delete_projects = user.get("assigned_projects_display", "PRJ-TEMIS")
        self.show_delete_user_modal = True

    def close_delete_user_modal(self):
        self.show_delete_user_modal = False
        self.user_to_delete_email = ""
        self.user_to_delete_name = ""

    def confirm_delete_user(self):
        if not self.user_to_delete_email:
            self.show_delete_user_modal = False
            return
        try:
            from backend.services.user_service import delete_user, load_users
            ok, msg = delete_user(self.user_to_delete_email)
            if ok:
                self.users_list = load_users()
                self.status_message = msg
                self.trigger_toast(f"Usuario {self.user_to_delete_name} eliminado", "info")
            else:
                self.status_message = f"Error: {msg}"
                self.trigger_toast(msg, "error")
        except Exception as e:
            self.status_message = f"Error: {str(e)}"
        finally:
            self.show_delete_user_modal = False
            self.user_to_delete_email = ""

    def delete_user_action(self, email: str):
        self.open_delete_user_modal(email)

    # Navigation Mode: "hub" (Level 1 Monday.com Portfolio) or "workspace" (Level 2 Modeling Suite)
    active_mode: str = "hub"
    is_workspace_sidebar_collapsed: bool = False

    def toggle_workspace_sidebar(self):
        self.is_workspace_sidebar_collapsed = not self.is_workspace_sidebar_collapsed
    
    # User Profile & RBAC Role Simulation
    user_role: str = "super_admin"  # "super_admin", "project_manager", "collaborator"
    user_name: str = "Ing. José Antonio Hurtado"
    user_email: str = "mxjhurtado@maxillc.com"

    def set_user_role(self, role: str):
        self.user_role = role
        role_labels = {
            "super_admin": "Super Admin (Portafolio Total)",
            "project_manager": "Dueño de Proyecto (Asignados)",
            "collaborator": "Colaborador (Invitado)"
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

    def clear_hub_filters(self):
        """Reset search and filter criteria in Hub view"""
        self.search_hub_query = ""
        self.filter_hub_phase = "all"
        self.filter_hub_status = "all"
        self.status_message = "Filtros del portafolio restablecidos"

    # Modal Create New Project State & Drive Pipeline
    show_new_project_modal: bool = False
    new_proj_name: str = ""
    new_proj_code: str = ""
    new_proj_purpose: str = ""
    new_proj_manager: str = "Ing. José Antonio Hurtado"
    new_proj_sponsor: str = "Dirección de Operaciones & Tecnología"
    new_proj_start_date: str = "2026-09-22"
    new_proj_end_date: str = "2026-12-22"
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
            "status": "Completado",
            "story_points": 25,
            "hours_estimated": 80
        },
        {
            "sprint_id": "Sprint 02",
            "period": "2026-02-02 al 2026-02-16",
            "objective": "Mapeo SIPOC Six Sigma y definición de roles, sistemas y canales",
            "modules": "Diseño BPMN & SIPOC",
            "milestone": "SIPOC y Simbología BPMN Homologada",
            "status": "Completado",
            "story_points": 30,
            "hours_estimated": 90
        },
        {
            "sprint_id": "Sprint 03",
            "period": "2026-02-17 al 2026-03-03",
            "objective": "Construcción del lienzo interactivo y docking de herramientas BPMN",
            "modules": "UI/UX & Espacio de Trabajo",
            "milestone": "Editor Visual Bézier Operativo",
            "status": "Completado",
            "story_points": 35,
            "hours_estimated": 100
        },
        {
            "sprint_id": "Sprint 04",
            "period": "2026-08-15 al 2026-09-30",
            "objective": "Desacoplamiento backend REST e integración con Google Workspace Shared Drive",
            "modules": "Core & Integraciones",
            "milestone": "Service Account y Sync de Carpetas",
            "status": "En Progreso",
            "story_points": 40,
            "hours_estimated": 110
        },
        {
            "sprint_id": "Sprint 05",
            "period": "2026-10-01 al 2026-11-15",
            "objective": "Motor de Auditoría Six Sigma con Gemini 2.5 Flash y reglas de calidad 0-100",
            "modules": "Gobernanza & Auditoría IA",
            "milestone": "Auditor IA y Daily Logs Activos",
            "status": "Planificado",
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
            "status": "Completado"
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
            "status": "Completado"
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
            "status": "Completado"
        },
        {
            "item_id": "6",
            "module": "Core & Integraciones",
            "user_story": "Como Sistema, quiero sincronizar con Google Drive para respaldar versiones y hojas.",
            "sprint": "Sprint 04",
            "story_points": 8,
            "hours_estimated": 35,
            "start_date": "2026-08-15",
            "end_date": "2026-09-20",
            "role": "Backend Dev (FastAPI)",
            "priority": "Alta",
            "deliverable": "Drive Service & Sheets API",
            "status": "Completado"
        },
        {
            "item_id": "7",
            "module": "Gobernanza & Auditoría IA",
            "user_story": "Como Líder de Calidad, quiero que Gemini audite la consistencia del flujo de 0 a 100.",
            "sprint": "Sprint 05",
            "story_points": 8,
            "hours_estimated": 30,
            "start_date": "2026-10-01",
            "end_date": "2026-10-15",
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
        if not self.plan_sprints:
            return ["Sin Sprint Asignado"]
        seen = set()
        opts = []
        for s in self.plan_sprints:
            sid = s.get("sprint_id")
            if sid and sid not in seen:
                seen.add(sid)
                opts.append(sid)
        return opts or ["Sin Sprint Asignado"]

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
            self.save_current_project()
            self.status_message = f"Plan de Trabajo generado con IA: {len(self.plan_sprints)} Sprints y {len(self.plan_backlog_items)} tareas"
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
                self.save_current_project()
                self.status_message = "¡Plan de Trabajo sincronizado con éxito en Google Sheets!"
            else:
                self.status_message = f"Error al sincronizar con Google Sheets: {msg}"
        except Exception as e:
            self.status_message = f"Error en sincronización: {str(e)}"
        finally:
            self.is_syncing_plan_sheet = False

    # Task Creator & Editor Modal State (F04, H05)
    show_task_modal: bool = False
    task_modal_mode: str = "create"  # "create" or "edit"
    task_form_id: str = ""
    task_form_module: str = "General"
    task_form_story: str = ""
    task_form_sprint: str = "Sin Sprint Asignado"
    task_form_sp: int = 3
    task_form_hours: int = 10
    task_form_start_date: str = "2026-01-16"
    task_form_end_date: str = "2026-01-30"
    task_form_role: str = "Desarrollador"
    task_form_priority: str = "Media"
    task_form_deliverable: str = ""
    task_form_status: str = "Planificado"
    task_form_error: str = ""

    def set_task_form_module(self, val: str):
        self.task_form_module = val

    def set_task_form_story(self, val: str):
        self.task_form_story = val
        if val.strip():
            self.task_form_error = ""

    def set_task_form_sprint(self, val: str):
        self.task_form_sprint = val

    def set_task_form_sp(self, val: str):
        try:
            self.task_form_sp = int(val)
        except Exception:
            self.task_form_sp = 3

    def set_task_form_hours(self, val: str):
        try:
            self.task_form_hours = int(val)
        except Exception:
            self.task_form_hours = 10

    def set_task_form_start_date(self, val: str):
        self.task_form_start_date = val

    def set_task_form_end_date(self, val: str):
        self.task_form_end_date = val

    def set_task_form_role(self, val: str):
        self.task_form_role = val

    def set_task_form_priority(self, val: str):
        self.task_form_priority = val

    def set_task_form_deliverable(self, val: str):
        self.task_form_deliverable = val

    def set_task_form_status(self, val: str):
        self.task_form_status = val

    def open_add_task_modal(self):
        """Open modal to add a new task with custom parameters (H05)"""
        count = len(self.plan_backlog_items) + 1
        self.task_form_id = str(count)
        self.task_form_module = "General"
        self.task_form_story = ""
        self.task_form_sprint = self.plan_sprints[0]["sprint_id"] if self.plan_sprints else "Sin Sprint Asignado"
        self.task_form_sp = 3
        self.task_form_hours = 10
        self.task_form_start_date = self.plan_start_date
        self.task_form_end_date = self.plan_end_date
        self.task_form_role = "Desarrollador"
        self.task_form_priority = "Media"
        self.task_form_deliverable = ""
        self.task_form_status = "Planificado"
        self.task_form_error = ""
        self.task_modal_mode = "create"
        self.show_task_modal = True

    def open_edit_task_modal(self, item_id: str):
        """Open modal to edit an existing task"""
        selected = next((i for i in self.plan_backlog_items if i.get("item_id") == str(item_id)), None)
        if not selected:
            return
        self.task_form_id = str(selected.get("item_id", ""))
        self.task_form_module = str(selected.get("module", "General"))
        self.task_form_story = str(selected.get("user_story", ""))
        self.task_form_sprint = str(selected.get("sprint", (self.plan_sprints[0]["sprint_id"] if self.plan_sprints else "Sin Sprint Asignado")))
        self.task_form_sp = int(selected.get("story_points", 3))
        self.task_form_hours = int(selected.get("hours_estimated", 10))
        self.task_form_start_date = str(selected.get("start_date", self.plan_start_date))
        self.task_form_end_date = str(selected.get("end_date", self.plan_end_date))
        self.task_form_role = str(selected.get("role", "Desarrollador"))
        self.task_form_priority = str(selected.get("priority", "Media"))
        self.task_form_deliverable = str(selected.get("deliverable", ""))
        self.task_form_status = str(selected.get("status", "Planificado"))
        self.task_form_error = ""
        self.task_modal_mode = "edit"
        self.show_task_modal = True

    def close_task_modal(self):
        self.show_task_modal = False

    def save_task_modal(self):
        """Save created or updated task from modal with strict validation (H05)"""
        if not self.task_form_story.strip():
            self.task_form_error = "La historia de usuario o descripción técnica es obligatoria"
            self.trigger_toast("Ingresa la descripción de la tarea para continuar", "error")
            return
        self.task_form_error = ""
        item_data = {
            "item_id": self.task_form_id or str(len(self.plan_backlog_items) + 1),
            "module": self.task_form_module.strip() or "General",
            "user_story": self.task_form_story.strip(),
            "sprint": self.task_form_sprint,
            "story_points": int(self.task_form_sp),
            "hours_estimated": int(self.task_form_hours),
            "start_date": self.task_form_start_date,
            "end_date": self.task_form_end_date,
            "role": self.task_form_role.strip() or "Desarrollador",
            "priority": self.task_form_priority,
            "deliverable": self.task_form_deliverable.strip(),
            "status": self.task_form_status
        }
        if self.task_modal_mode == "create":
            self.plan_backlog_items.append(item_data)
            self.trigger_toast(f"Tarea #{item_data['item_id']} agregada al Backlog", "success")
        else:
            updated = []
            for it in self.plan_backlog_items:
                if str(it.get("item_id")) == str(self.task_form_id):
                    updated.append(item_data)
                else:
                    updated.append(it)
            self.plan_backlog_items = updated
            self.trigger_toast(f"Tarea #{item_data['item_id']} actualizada con éxito", "success")
        self.show_task_modal = False
        self.save_current_project()

    def add_backlog_item(self):
        """Add a new task row to the Backlog (opens task modal)"""
        self.open_add_task_modal()

    def delete_backlog_item(self, item_id: str):
        """Remove a task row from the Backlog"""
        self.plan_backlog_items = [i for i in self.plan_backlog_items if i.get("item_id") != str(item_id)]
        self.save_current_project()
        self.status_message = "Tarea eliminada del Backlog"
        self.trigger_toast("Tarea eliminada del Backlog", "info")

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
    # Dual SIPOC Matrix State (AS-IS vs TO-BE)
    sipoc_active_mode: str = "asis"  # "asis" or "tobe"
    sipoc_rows_asis: List[Dict[str, Any]] = []
    sipoc_rows_tobe: List[Dict[str, Any]] = []

    # Narrative Analysis & Source Document State
    narrative_documents: List[Dict[str, Any]] = []
    active_narrative_doc_id: str = ""
    active_narrative_doc_name: str = ""
    narrative_total_blocks: int = 0
    is_uploading_narrative: bool = False
    is_analyzing_narrative: bool = False
    is_generating_narrative: bool = False
    narrative_analysis_step: int = 1  # 1: Carga, 2: Revisión, 3: Generación, 4: Resultados
    extracted_findings: List[Dict[str, Any]] = []
    clarification_points: List[Dict[str, Any]] = []
    narrative_overview_target: str = ""
    narrative_overview_scope: str = ""
    narrative_overview_input: str = ""
    narrative_overview_output: str = ""
    narrative_overview_frequency: str = "Siempre que la operación lo requiera"
    narrative_legal_framework: List[str] = []
    narrative_validity_control: Dict[str, Any] = {}
    narrative_asis_steps_data: List[Dict[str, Any]] = []
    narrative_tobe_steps_data: List[Dict[str, Any]] = []
    generated_narrative_markdown: str = ""
    show_narrative_diff_modal: bool = False
    diff_proposal_data: Dict[str, Any] = {}
    
    # Multimedia & Transcript State
    active_narrative_is_media: bool = False
    active_narrative_media_type: str = "document"  # "document", "audio", "video", "zip_package"
    active_narrative_duration: str = ""
    has_active_transcript_backup: bool = False
    active_transcript_text: str = ""
    active_is_media_studio_package: bool = False
    narrative_keyframes_gallery: List[Dict[str, str]] = []
    has_keyframes_gallery: bool = False
    _cached_narrative_blocks: List[Any] = []
    _cached_narrative_bytes: bytes = b""
    _cached_narrative_ext: str = ""

    customer_requirements: str = "Tiempos de respuesta (SLA) menores a 5 min, trazabilidad de logs en Chronos y encuesta con satisfacción >= 95%."
    is_completing_sipoc: bool = False
    show_sipoc_ai_modal: bool = False
    ai_sipoc_proposal_rows: list[dict] = []
    sipoc_last_synced_at: str = ""
    is_sipoc_flow_outdated: bool = False
    is_inspector_collapsed: bool = False

    def toggle_inspector(self):
        self.is_inspector_collapsed = not self.is_inspector_collapsed

    def set_customer_requirements(self, val: str):
        self.customer_requirements = val
        if self.sipoc_last_synced_at:
            self.is_sipoc_flow_outdated = True
        self.trigger_auto_save()

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
        if self.sipoc_last_synced_at:
            self.is_sipoc_flow_outdated = True
        self.trigger_auto_save()
        self.status_message = f"Paso {count}.0 agregado a la Matriz SIPOC"

    def remove_sipoc_row(self, row_id: str):
        """Remove a step row from SIPOC matrix"""
        self.sipoc_rows = [r for r in self.sipoc_rows if r.get("id") != row_id]
        # Re-index step numbers
        for idx, r in enumerate(self.sipoc_rows):
            r["id"] = str(idx + 1)
            r["step_num"] = f"{idx + 1}.0"
        if self.sipoc_last_synced_at:
            self.is_sipoc_flow_outdated = True
        self.trigger_auto_save()
        self.status_message = "Fila eliminada de la Matriz SIPOC"

    def update_sipoc_provider(self, row_id: str, val: str):
        for r in self.sipoc_rows:
            if r.get("id") == row_id:
                r["provider"] = val
                break
        if self.sipoc_last_synced_at:
            self.is_sipoc_flow_outdated = True
        self.trigger_auto_save()

    def update_sipoc_input(self, row_id: str, val: str):
        for r in self.sipoc_rows:
            if r.get("id") == row_id:
                r["input"] = val
                break
        if self.sipoc_last_synced_at:
            self.is_sipoc_flow_outdated = True
        self.trigger_auto_save()

    def update_sipoc_step(self, row_id: str, val: str):
        for r in self.sipoc_rows:
            if r.get("id") == row_id:
                r["step"] = val
                break
        if self.sipoc_last_synced_at:
            self.is_sipoc_flow_outdated = True
        self.trigger_auto_save()

    def update_sipoc_output(self, row_id: str, val: str):
        for r in self.sipoc_rows:
            if r.get("id") == row_id:
                r["output"] = val
                break
        if self.sipoc_last_synced_at:
            self.is_sipoc_flow_outdated = True
        self.trigger_auto_save()

    def update_sipoc_customer(self, row_id: str, val: str):
        for r in self.sipoc_rows:
            if r.get("id") == row_id:
                r["customer"] = val
                break
        if self.sipoc_last_synced_at:
            self.is_sipoc_flow_outdated = True
        self.trigger_auto_save()

    def update_sipoc_reqs(self, row_id: str, val: str):
        for r in self.sipoc_rows:
            if r.get("id") == row_id:
                r["requirements"] = val
                break
        if self.sipoc_last_synced_at:
            self.is_sipoc_flow_outdated = True
        self.trigger_auto_save()

    def sync_sipoc_to_flow(self):
        """
        Transform SIPOC Table into Flowchart DAG on the Canvas in a non-destructive manner:
        Generates/updates a dedicated 'Flujo SIPOC' tab without overwriting other user pages.
        """
        import datetime
        if not self.sipoc_rows:
            self.status_message = "La matriz SIPOC está vacía"
            self.trigger_toast("La matriz SIPOC está vacía", "warning")
            return

        new_nodes = []
        new_edges = []
        
        # 1. Start Node
        first_input = self.sipoc_rows[0].get("input", "Inicio") or "Inicio"
        first_provider = self.sipoc_rows[0].get("provider", "Input") or "Input"
        new_nodes.append({
            "id": "node-1",
            "type": "node_start",
            "label": f"Inicio: {first_input[:28]}",
            "swimlane": first_provider,
            "x": 80,
            "y": 140,
            "activity_number": None,
            "attached_system": "",
            "attached_channel": "WhatsApp" if "whatsapp" in first_input.lower() else ""
        })

        # 2. Activity / Decision Nodes from SIPOC Steps
        prev_node_id = "node-1"
        for idx, r in enumerate(self.sipoc_rows):
            node_id = f"node-{idx + 2}"
            step_text = r.get("step", f"Paso {idx+1}.0") or f"Paso {idx+1}.0"
            provider = r.get("provider", "Actor 1") or "Actor 1"
            
            # Detect Decision node type
            is_decision = "?" in step_text or "¿" in step_text or "si " in step_text.lower() or "decisión" in step_text.lower() or "evaluar" in step_text.lower()
            node_type = "node_decision" if is_decision else "node_activity"
            
            # Detect Systems and Channels
            attached_sys = ""
            lower_text = (step_text + " " + r.get("input", "") + " " + r.get("output", "")).lower()
            if "chronos" in lower_text:
                attached_sys = "Chronos ERP"
            elif "freshdesk" in lower_text:
                attached_sys = "Freshdesk"
            elif "sap" in lower_text or "erp" in lower_text:
                attached_sys = "Chronos ERP"

            attached_chan = ""
            if "whatsapp" in lower_text:
                attached_chan = "WhatsApp"
            elif "bria" in lower_text or "llamada" in lower_text or "teléfono" in lower_text:
                attached_chan = "Bria"
            elif "correo" in lower_text or "email" in lower_text:
                attached_chan = "Correo / Formulario"

            x_pos = 80 + (idx + 1) * 260
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
        last_output = self.sipoc_rows[-1].get("output", "Fin") or "Fin"
        last_customer = self.sipoc_rows[-1].get("customer", "Output") or "Output"
        end_x = 80 + (len(self.sipoc_rows) + 1) * 260
        
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
            unique_lanes = ["Input", "Actor 1", "Actor 2", "Output"]

        # Non-destructive tab handling: Look for "Flujo SIPOC" tab or create it
        sipoc_tab_idx = -1
        for idx, p in enumerate(self.project_pages):
            if p.get("name") in ["Flujo SIPOC", "Flujo SIPOC (Generado)"]:
                sipoc_tab_idx = idx
                break

        # Save current active page before switching
        if 0 <= self.active_page_index < len(self.project_pages):
            self.project_pages[self.active_page_index]["nodes"] = list(self.nodes)
            self.project_pages[self.active_page_index]["edges"] = list(self.edges)
            self.project_pages[self.active_page_index]["swimlanes"] = list(self.swimlanes)

        if sipoc_tab_idx != -1:
            # Update existing SIPOC tab
            self.active_page_index = sipoc_tab_idx
            self.project_pages[sipoc_tab_idx]["nodes"] = list(new_nodes)
            self.project_pages[sipoc_tab_idx]["edges"] = list(new_edges)
            self.project_pages[sipoc_tab_idx]["swimlanes"] = list(unique_lanes)
        else:
            # Create dedicated SIPOC tab
            new_tab = {
                "page_id": f"sipoc-{len(self.project_pages) + 1}",
                "name": "Flujo SIPOC",
                "nodes": list(new_nodes),
                "edges": list(new_edges),
                "swimlanes": list(unique_lanes)
            }
            self.project_pages.append(new_tab)
            self.active_page_index = len(self.project_pages) - 1

        self.unselect_node()
        self.nodes = new_nodes
        self.edges = new_edges
        self.swimlanes = unique_lanes
        self.sipoc_last_synced_at = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        self.is_sipoc_flow_outdated = False

        self.status_message = f"Diagrama de Flujo generado en pestaña 'Flujo SIPOC' ({len(self.nodes)} nodos)"
        self.trigger_toast(f"Diagrama sincronizado en pestaña 'Flujo SIPOC' ({len(self.nodes)} nodos)", "success")
        self.active_view = "flow"

    def complete_sipoc_with_ai(self):
        """Auto-complete SIPOC rows using Gemini AI with double-submit guard and preview modal"""
        if self.is_completing_sipoc:
            return
        self.is_completing_sipoc = True
        self.status_message = "Consultando propuesta de Matriz SIPOC con IA..."
        try:
            from backend.routers.diagrams import complete_sipoc_with_ai, SipocAiRequest
            res = complete_sipoc_with_ai(SipocAiRequest(
                project_name=self.project_name,
                project_purpose=self.project_purpose,
                existing_rows=self.sipoc_rows
            ))
            if res.get("rows"):
                self.ai_sipoc_proposal_rows = res["rows"]
                self.show_sipoc_ai_modal = True
                self.status_message = f"Propuesta IA generada con {len(self.ai_sipoc_proposal_rows)} pasos. Esperando confirmación."
                self.trigger_toast(f"Propuesta IA lista ({len(self.ai_sipoc_proposal_rows)} pasos)", "info")
            else:
                self.status_message = "No se recibieron filas sugeridas de la IA"
                self.trigger_toast("No se obtuvieron resultados de la IA", "warning")
        except Exception as e:
            self.status_message = f"Error al autocompletar SIPOC: {str(e)}"
            self.trigger_toast(f"Error IA: {str(e)}", "error")
        finally:
            self.is_completing_sipoc = False

    def apply_sipoc_ai_proposal(self, mode: str = "replace"):
        """Apply the AI proposal to the current SIPOC matrix (replace or append)"""
        if not self.ai_sipoc_proposal_rows:
            self.show_sipoc_ai_modal = False
            return

        if mode == "replace":
            self.sipoc_rows = list(self.ai_sipoc_proposal_rows)
            for idx, r in enumerate(self.sipoc_rows):
                r["id"] = str(idx + 1)
                r["step_num"] = f"{idx + 1}.0"
        elif mode == "append":
            current_len = len(self.sipoc_rows)
            for idx, r in enumerate(self.ai_sipoc_proposal_rows):
                new_idx = current_len + idx + 1
                row_copy = dict(r)
                row_copy["id"] = str(new_idx)
                row_copy["step_num"] = f"{new_idx}.0"
                self.sipoc_rows.append(row_copy)

        self.show_sipoc_ai_modal = False
        self.ai_sipoc_proposal_rows = []
        if self.sipoc_last_synced_at:
            self.is_sipoc_flow_outdated = True
        self.trigger_auto_save()
        self.status_message = f"Matriz SIPOC actualizada ({len(self.sipoc_rows)} pasos en total)"
        self.trigger_toast("Matriz SIPOC actualizada con éxito", "success")

    def cancel_sipoc_ai_proposal(self):
        """Discard the AI proposal without altering manual rows"""
        self.show_sipoc_ai_modal = False
        self.ai_sipoc_proposal_rows = []
        self.status_message = "Propuesta de IA descartada"
        self.trigger_toast("Propuesta de IA descartada", "info")

    def export_sipoc_excel(self):
        """Download styled Six Sigma SIPOC Excel workbook (.xlsx) with official MIME type"""
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
            self.trigger_toast("Matriz SIPOC (.xlsx) descargada", "success")
            return rx.download(
                data=stream.getvalue(),
                filename=f"Matriz_SIPOC_{safe_name}.xlsx",
                mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            self.status_message = f"Error al exportar Excel: {str(e)}"
            self.trigger_toast("Error al exportar Excel", "error")

    @rx.var
    def current_sipoc_rows(self) -> List[Dict[str, Any]]:
        """Return either AS-IS or TO-BE SIPOC rows based on active mode"""
        if self.sipoc_active_mode == "tobe":
            return self.sipoc_rows_tobe if self.sipoc_rows_tobe else self.sipoc_rows
        else:
            return self.sipoc_rows_asis if self.sipoc_rows_asis else self.sipoc_rows

    def set_sipoc_active_mode(self, mode: Union[str, List[str]]):
        """Switch between AS-IS and TO-BE SIPOC matrix tabs"""
        val = mode[0] if isinstance(mode, list) else str(mode)
        self.sipoc_active_mode = val
        self.status_message = f"Vista de Matriz SIPOC cambiada a: {val.upper()}"

    def set_narrative_analysis_step(self, step: int):
        """Set sequential step in narrative analysis workflow"""
        self.narrative_analysis_step = step

    async def handle_narrative_file_upload(self, files: List[rx.UploadFile]):
        """Handle upload of DOCX, PDF, Subtitles or ZIP packages from TEMIS Media Studio"""
        print(f"[NarrativeUpload] Handler invoked with {len(files) if files else 0} files")
        if not files:
            self.trigger_toast("No se detectó ningún archivo en el paquete. Por favor selecciona el archivo nuevamente.", "warning")
            return
        self.is_uploading_narrative = True
        self.status_message = "Procesando e indexando paquete/documento..."
        self.trigger_toast("Procesando archivo subido...", "info")
        yield


        try:
            import datetime
            from backend.services.document_parser import DocumentParser
            from backend.services.transcript_exporter import TranscriptExporter

            for file in files:
                upload_data = await file.read()
                ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
                
                is_zip = (ext == ".zip")
                keyframes_list = []
                
                if is_zip:
                    zip_res = DocumentParser.parse_zip_package(upload_data, file.filename)
                    blocks = zip_res.get("blocks", [])
                    keyframes_list = zip_res.get("keyframes", [])
                    self.narrative_keyframes_gallery = [
                        {
                            "filename": str(k.get("filename", "")),
                            "data_uri": str(k.get("data_uri", "")),
                            "timestamp_formatted": str(k.get("timestamp_formatted", ""))
                        }
                        for k in keyframes_list
                    ]
                    self.has_keyframes_gallery = bool(keyframes_list)
                    self.active_is_media_studio_package = True

                    # Pre-load charter if present
                    charter = zip_res.get("charter", {})
                    if charter:
                        if charter.get("project_name"):
                            self.project_name = charter["project_name"]
                        if charter.get("scope"):
                            self.scope_in = charter["scope"]
                            self.narrative_overview_scope = charter["scope"]
                        if charter.get("purpose"):
                            self.project_purpose = charter["purpose"]
                            self.narrative_overview_target = charter["purpose"]

                    # Pre-load SIPOC if present
                    if zip_res.get("sipoc_rows"):
                        self.sipoc_rows_asis = list(zip_res["sipoc_rows"])
                        self.sipoc_rows = list(zip_res["sipoc_rows"])

                    # Pre-load BPMN diagram if present
                    diagram = zip_res.get("diagram", {})
                    if diagram.get("nodes"):
                        self.nodes = list(diagram["nodes"])
                    if diagram.get("edges"):
                        self.edges = list(diagram["edges"])

                    # Pre-load process steps if present
                    if zip_res.get("process_steps"):
                        self.narrative_asis_steps_data = list(zip_res["process_steps"])

                    media_cat = "zip_package"
                    is_media = False
                    meta = {
                        "is_media": False,
                        "media_type": "zip_package",
                        "duration_formatted": f"{len(keyframes_list)} capturas",
                        "duration_seconds": None
                    }
                else:
                    self.active_is_media_studio_package = False
                    self.has_keyframes_gallery = False
                    self.narrative_keyframes_gallery = []
                    is_media = False
                    media_cat = "document"
                    meta = {
                        "is_media": False,
                        "media_type": "document",
                        "duration_formatted": "N/A",
                        "duration_seconds": None
                    }
                    blocks = DocumentParser.extract_blocks(upload_data, ext, file.filename)

                doc_hash = DocumentParser.compute_file_hash(upload_data)
                
                # Generate transcript backup text if subtitles or zip transcript
                txt_backup = ""
                if is_zip or ext in [".vtt", ".srt"]:
                    blocks_dicts = [b.model_dump() for b in blocks]
                    txt_backup = TranscriptExporter.export_to_txt(
                        project_name=self.project_name,
                        source_filename=file.filename,
                        duration_str=meta.get("duration_formatted", "N/A"),
                        uploaded_by=f"{self.user_name} ({self.user_email})",
                        blocks=blocks_dicts
                    )

                doc_entry = {
                    "id": f"doc-{len(self.narrative_documents)+1}",
                    "filename": file.filename,
                    "extension": ext,
                    "file_hash": doc_hash,
                    "file_size_bytes": len(upload_data),
                    "total_paragraphs": len(blocks),
                    "is_media": is_media,
                    "media_type": media_cat,
                    "duration_formatted": meta.get("duration_formatted", "N/A"),
                    "has_transcript_backup": bool(txt_backup),
                    "transcript_txt_content": txt_backup,
                    "uploaded_by": self.user_email,
                    "uploaded_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.narrative_documents.append(doc_entry)
                self.active_narrative_doc_id = doc_entry["id"]
                self.active_narrative_doc_name = file.filename
                self.active_narrative_is_media = is_media
                self.active_narrative_media_type = media_cat
                self.active_narrative_duration = meta.get("duration_formatted", "N/A")
                self.has_active_transcript_backup = bool(txt_backup)
                self.active_transcript_text = txt_backup
                self.narrative_total_blocks = len(blocks)
                self._cached_narrative_blocks = blocks
                self._cached_narrative_bytes = upload_data
                self._cached_narrative_ext = ext
                
                if is_zip:
                    label_type = "Paquete TEMIS Media Studio"
                    info_extra = f" ({len(keyframes_list)} capturas de pantalla)"
                elif ext in [".vtt", ".srt"]:
                    label_type = "Transcripción Subtítulos"
                    info_extra = ""
                else:
                    label_type = "Documento"
                    info_extra = ""

                self.status_message = f"{label_type} '{file.filename}'{info_extra} cargado ({len(blocks)} bloques indexados)."
                self.trigger_toast(f"{label_type} procesado con éxito", "success")
                self.trigger_auto_save()
                yield rx.clear_selected_files("upload_narrative_doc")
        except Exception as e:
            self.status_message = f"Error al procesar archivo: {str(e)}"
            self.trigger_toast(f"Error al procesar archivo: {str(e)}", "error")
        finally:
            self.is_uploading_narrative = False
            yield


    def run_narrative_ai_analysis(self):
        """Execute Gemini AI extraction on the uploaded narrative document"""
        import datetime
        if not hasattr(self, "_cached_narrative_blocks") or not self._cached_narrative_blocks:
            self.status_message = "Cargue un documento DOCX o PDF antes de iniciar el análisis."
            self.trigger_toast("Cargue un documento primero", "warning")
            return

        self.is_analyzing_narrative = True
        self.status_message = "Gemini 2.5 Flash analizando la narrativa del cliente..."
        try:
            from backend.services.narrative_ai_extractor import NarrativeAiExtractor
            extractor = NarrativeAiExtractor()
            result = extractor.analyze_document(
                project_id=self.project_id,
                document_id=self.active_narrative_doc_id,
                blocks=self._cached_narrative_blocks
            )

            # Store extracted data
            self.extracted_findings = [f.model_dump() for f in result.findings]
            self.clarification_points = [c.model_dump() for c in result.clarification_points]
            self.narrative_overview_target = result.overview.target
            self.narrative_overview_scope = result.overview.scope
            self.narrative_overview_input = result.overview.process_input
            self.narrative_overview_output = result.overview.process_output
            self.narrative_overview_frequency = result.overview.frequency
            self.narrative_legal_framework = list(result.legal_framework.regulations)
            self.narrative_validity_control = result.validity_control.model_dump()
            self.narrative_asis_steps_data = [s.model_dump() for s in result.asis_steps]
            self.narrative_tobe_steps_data = [s.model_dump() for s in result.tobe_steps]

            # Also suggest updating Project Charter if purpose was empty
            if not self.project_purpose:
                self.project_purpose = result.overview.target
            if not self.scope_in:
                self.scope_in = result.overview.scope

            self.narrative_analysis_step = 2
            self.status_message = f"Análisis IA completado: {len(self.extracted_findings)} hallazgos y {len(result.asis_steps)} actividades extraídas con citas."
            self.trigger_toast(f"Análisis IA completado ({len(self.extracted_findings)} hallazgos)", "success")
            self.trigger_auto_save()
        except Exception as e:
            self.status_message = f"Error durante el análisis IA: {str(e)}"
            self.trigger_toast(f"Error en análisis: {str(e)}", "error")
        finally:
            self.is_analyzing_narrative = False

    def enrich_narrative_with_new_doc(self):
        """Incrementally enrich and merge current process with the newly uploaded document"""
        import datetime
        if not hasattr(self, "_cached_narrative_blocks") or not self._cached_narrative_blocks:
            self.status_message = "Cargue un documento complementario antes de fusionar."
            self.trigger_toast("Cargue un documento primero", "warning")
            return

        self.is_analyzing_narrative = True
        self.status_message = f"Gemini 2.5 Flash enriqueciendo proceso con '{self.active_narrative_doc_name}'..."
        try:
            from backend.models.narrative_source_model import (
                NarrativeAnalysisResult, ExtractedFinding, ProcessOverviewData, 
                LegalFrameworkData, ActivityStepData, ValidityControlData
            )
            from backend.services.narrative_ai_extractor import NarrativeAiExtractor

            # Reconstruct current result
            existing_findings = [ExtractedFinding(**f) for f in self.extracted_findings]
            existing_clarifs = [ExtractedFinding(**c) for c in self.clarification_points]
            existing_overview = ProcessOverviewData(
                target=self.narrative_overview_target,
                scope=self.narrative_overview_scope,
                process_input=self.narrative_overview_input,
                process_output=self.narrative_overview_output,
                frequency=self.narrative_overview_frequency
            )
            existing_legal = LegalFrameworkData(regulations=self.narrative_legal_framework)
            existing_asis = [ActivityStepData(**s) for s in self.narrative_asis_steps_data]
            existing_tobe = [ActivityStepData(**s) for s in self.narrative_tobe_steps_data]
            existing_validity = ValidityControlData(**(self.narrative_validity_control or {}))

            existing_result = NarrativeAnalysisResult(
                project_id=self.project_id,
                document_id=self.active_narrative_doc_id,
                project_purpose=self.narrative_overview_target,
                scope_in=self.narrative_overview_scope,
                findings=existing_findings,
                clarification_points=existing_clarifs,
                overview=existing_overview,
                legal_framework=existing_legal,
                asis_steps=existing_asis,
                tobe_steps=existing_tobe,
                validity_control=existing_validity
            )

            extractor = NarrativeAiExtractor()
            merged_result = extractor.enrich_existing_process(
                project_id=self.project_id,
                document_id=self.active_narrative_doc_id,
                document_name=self.active_narrative_doc_name,
                blocks=self._cached_narrative_blocks,
                existing_result=existing_result
            )

            # Store updated merged data
            self.extracted_findings = [f.model_dump() for f in merged_result.findings]
            self.clarification_points = [c.model_dump() for c in merged_result.clarification_points]
            self.narrative_overview_target = merged_result.overview.target
            self.narrative_overview_scope = merged_result.overview.scope
            self.narrative_overview_input = merged_result.overview.process_input
            self.narrative_overview_output = merged_result.overview.process_output
            self.narrative_overview_frequency = merged_result.overview.frequency
            self.narrative_legal_framework = list(merged_result.legal_framework.regulations)
            self.narrative_validity_control = merged_result.validity_control.model_dump()
            self.narrative_asis_steps_data = [s.model_dump() for s in merged_result.asis_steps]
            self.narrative_tobe_steps_data = [s.model_dump() for s in merged_result.tobe_steps]

            self.narrative_analysis_step = 2
            self.status_message = f"Proceso enriquecido con éxito: {len(self.extracted_findings)} hallazgos totales y {len(merged_result.asis_steps)} actividades."
            self.trigger_toast(f"Proceso enriquecido con {self.active_narrative_doc_name}", "success")
            self.trigger_auto_save()
        except Exception as e:
            self.status_message = f"Error al enriquecer proceso: {str(e)}"
            self.trigger_toast(f"Error al enriquecer: {str(e)}", "error")
        finally:
            self.is_analyzing_narrative = False

    def update_finding_status(self, finding_id: str, new_status: str):
        """Update curation status of a finding in Human-in-the-Loop review"""
        import datetime
        for f in self.extracted_findings:
            if f.get("id") == finding_id:
                f["curation_status"] = new_status
                f["curated_by"] = self.user_email
                f["curated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                break
        self.trigger_auto_save()

    def generate_dual_sipoc_from_analysis(self):
        """Generate AS-IS and TO-BE SIPOC rows from analyzed narrative steps"""
        from backend.models.narrative_source_model import NarrativeAnalysisResult, ActivityStepData
        from backend.services.process_generator_service import ProcessGeneratorService

        asis_objs = [ActivityStepData(**s) for s in self.narrative_asis_steps_data]
        tobe_objs = [ActivityStepData(**s) for s in self.narrative_tobe_steps_data]

        res = NarrativeAnalysisResult(
            project_id=self.project_id,
            document_id=self.active_narrative_doc_id,
            project_purpose=self.narrative_overview_target,
            scope_in=self.narrative_overview_scope,
            asis_steps=asis_objs,
            tobe_steps=tobe_objs
        )

        dual_sipoc = ProcessGeneratorService.generate_dual_sipoc(res)
        self.sipoc_rows_asis = [r.model_dump() for r in dual_sipoc.asis_rows]
        self.sipoc_rows_tobe = [r.model_dump() for r in dual_sipoc.tobe_rows]
        self.sipoc_rows = list(self.sipoc_rows_asis)
        self.sipoc_active_mode = "asis"
        self.is_sipoc_flow_outdated = True
        self.status_message = f"Matrices SIPOC Duales generadas: {len(self.sipoc_rows_asis)} pasos AS-IS y {len(self.sipoc_rows_tobe)} pasos TO-BE."
        self.trigger_toast("SIPOCs AS-IS y TO-BE generados con éxito", "success")
        self.trigger_auto_save()

    def generate_dual_bpmn_from_analysis(self):
        """Generate AS-IS and TO-BE multi-tab BPMN diagram pages on the flowchart canvas"""
        from backend.models.narrative_source_model import NarrativeAnalysisResult, ActivityStepData
        from backend.services.process_generator_service import ProcessGeneratorService

        asis_objs = [ActivityStepData(**s) for s in self.narrative_asis_steps_data]
        tobe_objs = [ActivityStepData(**s) for s in self.narrative_tobe_steps_data]

        res = NarrativeAnalysisResult(
            project_id=self.project_id,
            document_id=self.active_narrative_doc_id,
            project_purpose=self.narrative_overview_target,
            scope_in=self.narrative_overview_scope,
            asis_steps=asis_objs,
            tobe_steps=tobe_objs
        )

        page_asis, page_tobe = ProcessGeneratorService.generate_dual_bpmn(res)
        
        # Replace or add pages to project_pages
        new_pages = [page_asis, page_tobe]
        self.project_pages = new_pages
        self.active_page_index = 0
        self.nodes = list(page_asis.get("nodes", []))
        self.edges = list(page_asis.get("edges", []))
        self.swimlanes = list(page_asis.get("swimlanes", []))

        self.status_message = "Diagramas BPMN Duales ('Flujo AS-IS' y 'Flujo TO-BE') generados en el lienzo."
        self.trigger_toast("Diagramas BPMN AS-IS y TO-BE generados en el lienzo", "success")
        self.trigger_auto_save()

    def generate_narrative_document_from_analysis(self):
        """Generate official 4-table Markdown manual and prepare Word download"""
        from backend.services.process_narrative import generate_process_narrative_markdown

        overview_dict = {
            "target": self.narrative_overview_target,
            "scope": self.narrative_overview_scope,
            "process_input": self.narrative_overview_input,
            "process_output": self.narrative_overview_output,
            "frequency": self.narrative_overview_frequency,
        }

        md = generate_process_narrative_markdown(
            project_name=self.project_name,
            overview_data=overview_dict,
            steps_data=self.narrative_asis_steps_data,
            legal_framework=self.narrative_legal_framework,
            validity_data=self.narrative_validity_control,
            clarification_points=self.clarification_points,
            sipoc_rows=self.sipoc_rows,
            mode_label="AS-IS"
        )
        self.generated_narrative_markdown = md
        self.narrative_analysis_step = 4
        self.status_message = "Manual de procedimientos oficial generado exitosamente."
        self.trigger_toast("Manual de Procedimientos generado con éxito", "success")
        self.trigger_auto_save()

    def export_narrative_word(self):
        """Download styled 4-table Word (.docx) document"""
        try:
            from backend.services.process_narrative import export_narrative_to_docx
            overview_dict = {
                "target": self.narrative_overview_target,
                "scope": self.narrative_overview_scope,
                "process_input": self.narrative_overview_input,
                "process_output": self.narrative_overview_output,
                "frequency": self.narrative_overview_frequency,
            }
            buf = export_narrative_to_docx(
                project_name=self.project_name,
                overview_data=overview_dict,
                steps_data=self.narrative_asis_steps_data,
                legal_framework=self.narrative_legal_framework,
                validity_data=self.narrative_validity_control,
                clarification_points=self.clarification_points,
                mode_label="AS-IS"
            )
            safe_name = self.project_name.replace(" ", "_")
            self.status_message = "Documento Word (.docx) generado exitosamente"
            self.trigger_toast("Documento Word oficial descargado", "success")
            return rx.download(
                data=buf.getvalue(),
                filename=f"Procedimiento_{safe_name}.docx",
                mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        except Exception as e:
            self.status_message = f"Error al exportar Word: {str(e)}"
            self.trigger_toast(f"Error al exportar Word: {str(e)}", "error")

    def export_transcript_docx(self):
        """Export interview audio/video transcript backup as Word (.docx)"""
        try:
            from backend.services.transcript_exporter import TranscriptExporter
            blocks_dicts = [b.model_dump() if hasattr(b, "model_dump") else b for b in (getattr(self, "_cached_narrative_blocks", []) or [])]
            buf = TranscriptExporter.export_to_docx(
                project_name=self.project_name,
                source_filename=self.active_narrative_doc_name or "Entrevista",
                duration_str=self.active_narrative_duration or "N/A",
                uploaded_by=f"{self.user_name} ({self.user_email})",
                blocks=blocks_dicts
            )
            safe_name = (self.active_narrative_doc_name or "Entrevista").rsplit(".", 1)[0].replace(" ", "_")
            self.status_message = "Minuta y Transcripción Word descargada exitosamente"
            self.trigger_toast("Minuta de transcripción descargada (.docx)", "success")
            return rx.download(
                data=buf.getvalue(),
                filename=f"Transcripcion_{safe_name}.docx",
                mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        except Exception as e:
            self.status_message = f"Error al exportar transcripción: {str(e)}"
            self.trigger_toast(f"Error al exportar: {str(e)}", "error")

    def export_transcript_txt(self):
        """Export interview audio/video transcript backup as plain text (.txt)"""
        try:
            from backend.services.transcript_exporter import TranscriptExporter
            blocks_dicts = [b.model_dump() if hasattr(b, "model_dump") else b for b in (getattr(self, "_cached_narrative_blocks", []) or [])]
            txt_str = TranscriptExporter.export_to_txt(
                project_name=self.project_name,
                source_filename=self.active_narrative_doc_name or "Entrevista",
                duration_str=self.active_narrative_duration or "N/A",
                uploaded_by=f"{self.user_name} ({self.user_email})",
                blocks=blocks_dicts
            )
            safe_name = (self.active_narrative_doc_name or "Entrevista").rsplit(".", 1)[0].replace(" ", "_")
            self.status_message = "Transcripción (.txt) descargada exitosamente"
            self.trigger_toast("Archivo TXT de transcripción descargado", "success")
            return rx.download(
                data=txt_str,
                filename=f"Transcripcion_{safe_name}.txt",
                mime_type="text/plain"
            )
        except Exception as e:
            self.status_message = f"Error al exportar TXT: {str(e)}"
            self.trigger_toast(f"Error al exportar: {str(e)}", "error")

    def open_narrative_diff_modal(self):
        self.show_narrative_diff_modal = True

    def close_narrative_diff_modal(self):
        self.show_narrative_diff_modal = False

    def apply_narrative_diff_proposal(self):
        """Apply AI diff proposal without losing manual data"""
        self.show_narrative_diff_modal = False
        self.status_message = "Propuesta de IA aplicada correctamente."
        self.trigger_toast("Cambios aplicados", "success")

    def export_diagram_svg(self):
        """Export current flowchart diagram as a clean SVG vector file"""
        try:
            max_x = max([int(n.get("x", 100)) for n in self.nodes], default=600) + 300
            max_y = max([int(n.get("y", 140)) for n in self.nodes], default=400) + 300
            width = max(1200, max_x)
            height = max(800, max_y)

            svg_parts = [
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" style="background-color: #f8fafc; font-family: Inter, sans-serif;">',
                '  <defs>',
                '    <marker id="arrow-blue" viewBox="0 0 10 10" refX="6" refY="3.5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">',
                '      <polygon points="0 0, 10 3.5, 0 7" fill="#1e5a9a" />',
                '    </marker>',
                '  </defs>',
                f'  <!-- Title: {self.project_name} -->',
                f'  <text x="30" y="40" font-size="18" font-weight="bold" fill="#17283c">{self.project_name} — Diagrama BPMN</text>',
                f'  <text x="30" y="62" font-size="12" fill="#52657a">Código: {getattr(self, "project_code", "PRJ")} | Generado por TEMIS Web Flow</text>',
            ]

            # SVG Edges
            for edge in self.computed_edges:
                svg_parts.append(f'  <path d="{edge.get("d", "")}" stroke="#1e5a9a" stroke-width="2.5" fill="none" marker-end="url(#arrow-blue)" />')
                if edge.get("has_label"):
                    svg_parts.append(f'  <text x="{edge.get("label_x", 0)}" y="{edge.get("label_y", 0)}" fill="#065f46" font-size="11" font-weight="bold" text-anchor="middle">{edge.get("label", "")}</text>')

            # SVG Nodes
            for n in self.nodes:
                x = n.get("x", 80)
                y = n.get("y", 120)
                ntype = n.get("type", "node_activity")
                lbl = n.get("label", "")
                
                if ntype == "node_start":
                    svg_parts.append(f'  <g transform="translate({x},{y})">')
                    svg_parts.append('    <rect width="130" height="42" rx="21" ry="21" fill="#eff6ff" stroke="#1e5a9a" stroke-width="2" />')
                    svg_parts.append(f'    <text x="65" y="26" font-size="11" font-weight="bold" fill="#1e5a9a" text-anchor="middle">{lbl[:20]}</text>')
                    svg_parts.append('  </g>')
                elif ntype == "node_end":
                    svg_parts.append(f'  <g transform="translate({x},{y})">')
                    svg_parts.append('    <rect width="130" height="42" rx="21" ry="21" fill="#f1f5f9" stroke="#64748b" stroke-width="2" />')
                    svg_parts.append(f'    <text x="65" y="26" font-size="11" font-weight="bold" fill="#334155" text-anchor="middle">{lbl[:20]}</text>')
                    svg_parts.append('  </g>')
                elif ntype == "node_decision":
                    svg_parts.append(f'  <g transform="translate({x},{y})">')
                    svg_parts.append('    <rect width="160" height="68" rx="8" ry="8" fill="#fffbeb" stroke="#d97706" stroke-width="2" />')
                    svg_parts.append(f'    <text x="80" y="38" font-size="11" font-weight="bold" fill="#92400e" text-anchor="middle">{lbl[:24]}</text>')
                    svg_parts.append('  </g>')
                else:
                    svg_parts.append(f'  <g transform="translate({x},{y})">')
                    svg_parts.append('    <rect width="170" height="74" rx="8" ry="8" fill="#ffffff" stroke="#059669" stroke-width="2" />')
                    act_num = n.get("activity_number")
                    act_prefix = f"[{act_num}] " if act_num else ""
                    svg_parts.append(f'    <text x="12" y="28" font-size="11" font-weight="bold" fill="#17283c">{act_prefix}{lbl[:18]}</text>')
                    lane = n.get("swimlane", "")
                    if lane:
                        svg_parts.append(f'    <text x="12" y="52" font-size="10" fill="#52657a">Rol: {lane[:18]}</text>')
                    svg_parts.append('  </g>')

            svg_parts.append('</svg>')
            svg_content = "\n".join(svg_parts)
            safe_name = self.project_name.replace(" ", "_")
            self.status_message = "Diagrama SVG exportado exitosamente"
            self.trigger_toast("Diagrama exportado (.svg)", "success")
            return rx.download(
                data=svg_content,
                filename=f"Diagrama_{safe_name}.svg",
                mime_type="image/svg+xml"
            )
        except Exception as e:
            self.status_message = f"Error al exportar SVG: {str(e)}"
            self.trigger_toast("Error al exportar SVG", "error")

    # Narrative & Policy Manual State
    narrative_text: str = """# Manual de Procedimientos & Narrativa Oficial
# PROYECTO DEMO TEMIS

## 1. Objetivo y Propósito del Proceso
Estandarizar y automatizar el ciclo integral de atención de aclaraciones y transacciones de clientes vía canales digitales y sistemas centrales.

## 2. Matriz de Roles y Responsabilidades
- **Actores y Participantes:** Agente Operativo, Sistema Chronos, Usuario / Cliente
- **Sistemas y Plataformas:** Chronos, Freshdesk
- **Canales de Interacción:** WhatsApp

---

## 3. Narrativa Operativa Secuencial (Paso a Paso)

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

## 4. Políticas y Reglas de Negocio Clave
1. **Trazabilidad Absoluta:** Toda interacción por canal digital o sistema debe quedar registrada con marca de tiempo y folio.
2. **Control de Calidad:** Las compuertas de decisión deben validar que la totalidad de requisitos previos se cumplan antes de pasar a la siguiente fase.
3. **Escalamiento:** En caso de excepción no contemplada en las reglas estándar, el caso se turna al líder del proceso para dictamen.
"""
    is_generating_narrative: bool = False

    def set_narrative_text(self, val: str):
        self.narrative_text = val

    def generate_narrative_ai(self):
        """Generate procedure manual narrative in continuous prose from current Flow and SIPOC data"""
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
            self.status_message = "Narrativa Oficial redactada y sincronizada con éxito"
        except Exception as e:
            self.status_message = f"Error al generar narrativa: {str(e)}"
        finally:
            self.is_generating_narrative = False

    def export_narrative_markdown(self):
        """Download narrative as Markdown/Text document"""
        safe_name = self.project_name.replace(" ", "_")
        self.status_message = "Manual de Procedimientos exportado (.md)"
        self.trigger_toast("Manual de Procedimientos (.md) descargado", "success")
        return rx.download(
            data=self.narrative_text,
            filename=f"Manual_Procedimiento_{safe_name}.md"
        )

    def export_executive_charter_html(self):
        """Generate and download a self-contained Executive Project One-Pager in HTML/Print-ready format"""
        safe_name = self.project_name.replace(" ", "_")
        
        # Build SIPOC rows HTML
        sipoc_html_rows = ""
        for r in self.sipoc_rows:
            sipoc_html_rows += f"""
            <tr>
                <td style="padding: 8px 12px; border: 1px solid #d7e0ea; font-weight: bold; text-align: center; color: #2563eb;">{r.get('step_num', '')}</td>
                <td style="padding: 8px 12px; border: 1px solid #d7e0ea; color: #334155;">{r.get('provider', '')}</td>
                <td style="padding: 8px 12px; border: 1px solid #d7e0ea; color: #334155;">{r.get('input', '')}</td>
                <td style="padding: 8px 12px; border: 1px solid #d7e0ea; font-weight: 600; color: #0f172a;">{r.get('step', '')}</td>
                <td style="padding: 8px 12px; border: 1px solid #d7e0ea; color: #334155;">{r.get('output', '')}</td>
                <td style="padding: 8px 12px; border: 1px solid #d7e0ea; color: #334155;">{r.get('customer', '')}</td>
            </tr>
            """

        # Build Sprints rows HTML
        sprints_html = ""
        for s in self.plan_sprints:
            s_status = s.get('status', 'Planned')
            badge_color = "#16a34a" if s_status in ["Completado", "Done"] else ("#2563eb" if s_status in ["In Progress", "En Progreso"] else "#64748b")
            sprints_html += f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: #ffffff; border: 1px solid #d7e0ea; border-radius: 6px; margin-bottom: 6px;">
                <div>
                    <strong style="color: #0f172a;">{s.get('sprint_id', '')}</strong>: <span style="color: #475569;">{s.get('objective', '')}</span>
                    <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Periodo: {s.get('period', '')} · Hito: {s.get('milestone', '')}</div>
                </div>
                <span style="font-size: 11px; font-weight: bold; padding: 3px 8px; border-radius: 4px; background: {badge_color}15; color: {badge_color}; border: 1px solid {badge_color}40;">
                    {s_status}
                </span>
            </div>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ficha Ejecutiva - {self.project_name} ({self.project_code})</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #f3f6fa;
            color: #17283c;
            margin: 0;
            padding: 32px 16px;
        }}
        .container {{
            max-width: 960px;
            margin: 0 auto;
            background: #ffffff;
            border: 1px solid #d7e0ea;
            border-radius: 12px;
            padding: 36px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        }}
        .header-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #2563eb;
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        .logo {{
            font-size: 22px;
            font-weight: 800;
            color: #1d4ed8;
            letter-spacing: -0.02em;
        }}
        .badge-code {{
            background: #eff6ff;
            color: #1d4ed8;
            font-size: 12px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 6px;
            border: 1px solid #bfdbfe;
        }}
        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 24px;
        }}
        .card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
        }}
        .section-title {{
            font-size: 14px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            margin-bottom: 12px;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 6px;
        }}
        .meta-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 13px;
        }}
        .meta-label {{
            color: #64748b;
            font-weight: 500;
        }}
        .meta-val {{
            color: #0f172a;
            font-weight: 600;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-top: 10px;
        }}
        th {{
            background: #f1f5f9;
            color: #475569;
            font-weight: 700;
            text-align: left;
            padding: 8px 12px;
            border: 1px solid #d7e0ea;
        }}
        .score-box {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #ecfdf5;
            border: 1px solid #a7f3d0;
            border-radius: 8px;
            padding: 16px 20px;
            margin-top: 24px;
        }}
        .score-num {{
            font-size: 28px;
            font-weight: 800;
            color: #059669;
        }}
        @media print {{
            body {{ background: #ffffff; padding: 0; }}
            .container {{ border: none; box-shadow: none; padding: 0; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar">
            <div>
                <div class="logo">TEMIS · Process Suite</div>
                <div style="font-size: 12px; color: #64748b;">Ficha Ejecutiva Oficial & Project Charter</div>
            </div>
            <div style="text-align: right;">
                <span class="badge-code">{self.project_code}</span>
                <div style="font-size: 11px; color: #94a3b8; margin-top: 4px;">Generado el 22/09/2026</div>
            </div>
        </div>

        <h1 style="font-size: 22px; color: #0f172a; margin-top: 0; margin-bottom: 8px;">{self.project_name}</h1>
        <p style="font-size: 14px; color: #475569; line-height: 1.5; margin-bottom: 24px;">{self.project_purpose}</p>

        <div class="grid-2">
            <div class="card">
                <div class="section-title">Datos Maestros & Responsables</div>
                <div class="meta-row">
                    <span class="meta-label">Dueño de Proyecto (PM):</span>
                    <span class="meta-val">{self.project_manager}</span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Sponsor Directivo:</span>
                    <span class="meta-val">{self.project_sponsor}</span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Fecha de Inicio:</span>
                    <span class="meta-val">{self.start_date}</span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Fecha de Cierre:</span>
                    <span class="meta-val">{self.end_date}</span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Fase de Gobernanza:</span>
                    <span class="meta-val">{self.phase_name}</span>
                </div>
            </div>

            <div class="card">
                <div class="section-title">Alcance & Requisitos</div>
                <div style="font-size: 12px; margin-bottom: 8px;">
                    <strong style="color: #16a34a;">Alcance Incluido (In Scope):</strong><br>
                    <span style="color: #475569;">{self.scope_in}</span>
                </div>
                <div style="font-size: 12px; margin-bottom: 8px;">
                    <strong style="color: #dc2626;">Fuera de Alcance (Out of Scope):</strong><br>
                    <span style="color: #475569;">{self.scope_out}</span>
                </div>
                <div style="font-size: 12px;">
                    <strong style="color: #2563eb;">Requisitos del Cliente:</strong><br>
                    <span style="color: #475569;">{self.customer_requirements}</span>
                </div>
            </div>
        </div>

        <div class="card" style="margin-bottom: 24px;">
            <div class="section-title">Matriz SIPOC Resumida (Mapeo Six Sigma)</div>
            <table>
                <thead>
                    <tr>
                        <th style="width: 40px; text-align: center;">#</th>
                        <th style="width: 18%;">Proveedores (S)</th>
                        <th style="width: 18%;">Entradas (I)</th>
                        <th style="width: 26%;">Proceso (P)</th>
                        <th style="width: 18%;">Salidas (O)</th>
                        <th style="width: 16%;">Clientes (C)</th>
                    </tr>
                </thead>
                <tbody>
                    {sipoc_html_rows}
                </tbody>
            </table>
        </div>

        <div class="card" style="margin-bottom: 20px;">
            <div class="section-title">Plan de Trabajo & Sprints Scrum</div>
            {sprints_html}
        </div>

        <div class="score-box">
            <div>
                <div style="font-size: 16px; font-weight: bold; color: #065f46;">Certificación de Calidad Six Sigma (IA TEMIS)</div>
                <div style="font-size: 12px; color: #047857; margin-top: 2px;">Auditoría automatizada de gobierno, completitud y trazabilidad de flujo.</div>
            </div>
            <div style="text-align: right;">
                <div class="score-num">{self.audit_score} / 100</div>
                <div style="font-size: 11px; font-weight: bold; color: #059669;">Nivel de Calidad Óptimo</div>
            </div>
        </div>

        <div style="margin-top: 32px; text-align: center;" class="no-print">
            <button onclick="window.print()" style="background: #2563eb; color: #ffffff; border: none; padding: 10px 24px; font-size: 14px; font-weight: bold; border-radius: 6px; cursor: pointer;">
                Imprimir o Guardar como PDF
            </button>
        </div>
    </div>
</body>
</html>"""

        self.status_message = "Ficha Ejecutiva del Proyecto exportada exitosamente"
        self.trigger_toast(f"Ficha Ejecutiva de '{self.project_name}' generada", "success")
        return rx.download(
            data=html_content,
            filename=f"Ficha_Ejecutiva_{safe_name}.html"
        )

    def export_project_charter_pdf(self):
        """Export executive project charter HTML/PDF download"""
        return self.export_executive_charter_html()

    
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
        self.node_label_edit = ""
        self.node_swimlane_edit = ""
        self.selected_node_type = ""
        self.selected_node_system = ""
        self.selected_node_channel = ""

    def set_selected_node_label(self, val: str):
        self.node_label_edit = val
        if not self.selected_node_id:
            return
        for n in self.nodes:
            if n["id"] == self.selected_node_id:
                n["label"] = val
                break
        self.trigger_auto_save()

    def set_selected_node_type(self, val: str):
        self.selected_node_type = val
        if not self.selected_node_id:
            return
        for n in self.nodes:
            if n["id"] == self.selected_node_id:
                n["type"] = val
                break
        self.trigger_auto_save()

    def set_selected_node_swimlane(self, val: str):
        self.node_swimlane_edit = val
        if not self.selected_node_id:
            return
        for n in self.nodes:
            if n["id"] == self.selected_node_id:
                n["swimlane"] = val
                break
        self.trigger_auto_save()

    def set_selected_node_system(self, val: str):
        self.selected_node_system = val
        if not self.selected_node_id:
            return
        for n in self.nodes:
            if n["id"] == self.selected_node_id:
                n["attached_system"] = val
                break
        self.trigger_auto_save()

    def set_selected_node_channel(self, val: str):
        self.selected_node_channel = val
        if not self.selected_node_id:
            return
        for n in self.nodes:
            if n["id"] == self.selected_node_id:
                n["attached_channel"] = val
                break
        self.trigger_auto_save()

    # AI Text-to-Diagram Generation State
    ai_prompt_text: str = ""
    is_generating_ai: bool = False
    status_message: str = "Listo"

    # Phase Gate Governance State & Audit Log (F01, H01)
    show_phase_gate_modal: bool = False
    show_phase_blocked_modal: bool = False
    target_gate_phase_num: int = 1
    target_gate_phase_name: str = ""
    target_gate_phase_owner: str = ""
    target_gate_criteria: str = ""
    target_gate_deliverables: List[str] = []
    phase_gate_signer: str = ""
    phase_gate_notes: str = ""
    phase_gate_checked_deliverables: List[str] = []
    gate_approvals_history: List[Dict[str, Any]] = []

    @rx.var
    def all_gate_deliverables_checked(self) -> bool:
        if not self.target_gate_deliverables:
            return True
        return len(self.phase_gate_checked_deliverables) >= len(self.target_gate_deliverables)

    def set_phase_gate_signer(self, val: str):
        self.phase_gate_signer = val

    def set_phase_gate_notes(self, val: str):
        self.phase_gate_notes = val

    def toggle_gate_deliverable(self, item: str):
        if item in self.phase_gate_checked_deliverables:
            self.phase_gate_checked_deliverables = [d for d in self.phase_gate_checked_deliverables if d != item]
        else:
            self.phase_gate_checked_deliverables = self.phase_gate_checked_deliverables + [item]

    def request_phase_change(self, target_phase: int):
        """Evaluate governance gate requirements before activating target phase (F01, H01)"""
        if target_phase == self.current_phase:
            return

        phase_info = {
            1: {"name": "Fase 1: Diagnóstico Estratégico", "owner": "Dirección General / Sponsor", "deliverables": ["Ficha de Diagnóstico", "Matriz de Interesados", "Justificación de Negocio"], "gate_criteria": "Aprobación de oportunidad y factibilidad inicial."},
            2: {"name": "Fase 2: Inicio del Proyecto", "owner": "Project Manager (PM)", "deliverables": ["Project Charter Oficial", "Matriz SIPOC Inicial", "Asignación RACI"], "gate_criteria": "Charter firmado y alcance preliminar delimitado."},
            3: {"name": "Fase 3: Planificación Híbrida", "owner": "PM & Analista de Procesos", "deliverables": ["Diagrama BPMN Multi-Pestaña", "Backlog Scrum Técnico", "Matriz de Riesgos"], "gate_criteria": "Plan de trabajo desglosado en Sprints y estimación de SP."},
            4: {"name": "Fase 4: Ejecución Iterativa", "owner": "Equipo de Desarrollo & Procesos", "deliverables": ["Manual de Políticas y Procedimientos", "Servicios Backend / UI", "Daily Logs (EOD)"], "gate_criteria": "Entregables del sprint completados y documentados."},
            5: {"name": "Fase 5: Monitoreo y Control", "owner": "Auditor QA / Six Sigma", "deliverables": ["Auditoría IA de Calidad (0-100)", "Reporte de Cumplimiento SLA", "Pruebas UAT"], "gate_criteria": "Score de calidad Six Sigma >= 80 y sin bloqueos P0."},
            6: {"name": "Fase 6: Mejora Continua", "owner": "Operaciones & Mejora Continua", "deliverables": ["Plan de Ajustes Kaizen", "Encuesta de Satisfacción", "Métricas Operativas"], "gate_criteria": "Retroalimentación recopilada y plan de optimización activo."},
            7: {"name": "Fase 7: Cierre del Proyecto", "owner": "PM & Sponsor", "deliverables": ["Acta de Cierre Aprobada", "Paquete .temis.json Exportado", "Lecciones Aprendidas"], "gate_criteria": "Acta de cierre firmada y archivo respaldado en Drive."}
        }

        # Going back to earlier phase
        if target_phase < self.current_phase:
            self.set_phase(target_phase)
            self.trigger_toast(f"Retornaste a {PHASE_NAMES.get(target_phase, f'Fase {target_phase}')}", "info")
            return

        # Promoting to immediate next phase (Sequential Gate Verification)
        if target_phase == self.current_phase + 1:
            curr_data = phase_info.get(self.current_phase, phase_info[1])
            target_data = phase_info.get(target_phase, phase_info[1])
            self.target_gate_phase_num = target_phase
            self.target_gate_phase_name = target_data["name"]
            self.target_gate_phase_owner = target_data["owner"]
            self.target_gate_criteria = curr_data["gate_criteria"]
            self.target_gate_deliverables = list(curr_data["deliverables"])
            self.phase_gate_checked_deliverables = []  # Requires explicit verification check!
            self.phase_gate_signer = f"{self.user_name} ({self.user_role.upper()})"
            self.phase_gate_notes = ""
            self.show_phase_gate_modal = True
            return

        # Multi-phase jump blocked
        if target_phase > self.current_phase + 1:
            target_data = phase_info.get(target_phase, phase_info[1])
            self.target_gate_phase_num = target_phase
            self.target_gate_phase_name = target_data["name"]
            self.show_phase_blocked_modal = True

    def close_phase_gate_modal(self):
        self.show_phase_gate_modal = False

    def close_phase_blocked_modal(self):
        self.show_phase_blocked_modal = False

    def confirm_phase_gate_approval(self):
        """Approve gate deliverable signoff, log immutable audit entry, and advance phase (H01)"""
        if len(self.phase_gate_checked_deliverables) < len(self.target_gate_deliverables):
            missing = len(self.target_gate_deliverables) - len(self.phase_gate_checked_deliverables)
            self.trigger_toast(f"Falta validar {missing} entregable(s) requerido(s) para este Gate", "warning")
            return

        from datetime import datetime
        now = datetime.now()
        log_entry = {
            "phase": self.target_gate_phase_num,
            "phase_name": self.target_gate_phase_name,
            "from_phase": self.current_phase,
            "approved_by": self.user_name,
            "user_email": self.user_email,
            "user_role": self.user_role,
            "approved_at": now.strftime("%d %b %Y, %H:%M"),
            "gate_criteria": self.target_gate_criteria,
            "deliverables": list(self.phase_gate_checked_deliverables),
            "notes": self.phase_gate_notes.strip() or "Aprobación formal de Gate metodológico TEMIS",
            "project_code": getattr(self, "project_code", "PRJ")
        }
        self.gate_approvals_history.append(log_entry)
        self.set_phase(self.target_gate_phase_num)
        self.show_phase_gate_modal = False
        self.trigger_toast(f"Gate Aprobado: Avanzaste a {self.phase_name}", "success")

    # Set phase handler (T16 Governance)
    def set_phase(self, phase_num: int):
        self.current_phase = phase_num
        self.phase_name = PHASE_NAMES.get(phase_num, f"Fase {phase_num}")
        self.save_current_project()
        self.status_message = f"Fase {phase_num} activada exitosamente para '{self.project_name}' por {self.user_name}"

    # Set prompt text handler
    def set_ai_prompt_text(self, val: str):
        self.ai_prompt_text = val

    # Add Node from Symbology Palette with smart collision avoidance
    def add_node_by_type(self, node_type: str, label: str):
        count = len(self.nodes) + 1
        new_id = f"node-{count}"
        swimlane = self.swimlanes[0] if self.swimlanes else "Actor 1"
        
        # Calculate sequential activity number if activity
        activity_num = None
        if node_type == "node_activity":
            activities = [n for n in self.nodes if n.get("type") == "node_activity"]
            activity_num = len(activities) + 1

        # Smart collision positioning
        if self.selected_node_id and any(n["id"] == self.selected_node_id for n in self.nodes):
            sel_node = next(n for n in self.nodes if n["id"] == self.selected_node_id)
            target_x = sel_node.get("x", 80) + 240
            target_y = sel_node.get("y", 140)
            swimlane = sel_node.get("swimlane", swimlane)
            if target_x > 1400:
                target_x = 80
                target_y += 150
        else:
            if self.nodes:
                max_x = max(int(n.get("x", 80)) for n in self.nodes)
                target_x = max_x + 240
                target_y = 140
                if target_x > 1400:
                    target_x = 80
                    target_y = max(int(n.get("y", 140)) for n in self.nodes) + 150
            else:
                target_x = 80
                target_y = 140

        new_node = {
            "id": new_id,
            "type": node_type,
            "label": label,
            "swimlane": swimlane,
            "x": target_x,
            "y": target_y,
            "activity_number": activity_num,
            "attached_system": "",
            "attached_channel": ""
        }
        self.nodes.append(new_node)
        self.selected_node_id = new_id
        self.node_label_edit = label
        self.node_swimlane_edit = swimlane
        self.selected_node_type = node_type
        self.selected_node_system = ""
        self.selected_node_channel = ""
        self.trigger_auto_save()
        self.status_message = f"Símbolo '{label}' agregado al lienzo"

    # Clear diagram canvas
    def clear_canvas(self):
        self.nodes = []
        self.edges = []
        self.unselect_node()
        self.trigger_auto_save()
        self.status_message = "Lienzo limpiado"

    # Delete Selected Node
    def delete_selected_node(self):
        if not self.selected_node_id:
            return
        self.nodes = [n for n in self.nodes if n["id"] != self.selected_node_id]
        self.edges = [e for e in self.edges if e["source"] != self.selected_node_id and e["target"] != self.selected_node_id]
        self.unselect_node()
        self.trigger_auto_save()
        self.status_message = "Nodo eliminado"

    # Move Selected Node
    def move_selected_node(self, dx: int, dy: int):
        """Move or reposition selected node on canvas"""
        if not self.selected_node_id:
            return
        for n in self.nodes:
            if n["id"] == self.selected_node_id:
                n["x"] = max(10, int(n.get("x", 0)) + dx)
                n["y"] = max(10, int(n.get("y", 0)) + dy)
                break
        self.trigger_auto_save()
        self.status_message = f"Nodo {self.selected_node_id} reposicionado ({dx:+d}, {dy:+d})"

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
    # Saved Projects / Flujos Guardados Catalog State (Dynamic Google Drive Sync)
    show_recent_modal: bool = False
    search_saved_query: str = ""
    saved_projects: List[Dict[str, Any]] = []
    is_syncing_drive_projects: bool = False

    def load_projects_from_drive(self, force_remote: bool = False):
        """Load projects using instant local cache first, syncing with Drive when requested"""
        import os, json
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        cache_file = os.path.join(data_dir, "saved_projects.json")

        # 1. Load from local cache immediately for instant UI response
        if not force_remote and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                    if isinstance(cached, list) and cached:
                        self.saved_projects = cached
                        return
            except Exception as e:
                print(f"[FlowState] Error reading local cache: {e}")

        # 2. Remote Drive scan
        self.is_syncing_drive_projects = True
        try:
            from backend.services.drive_service import DriveService
            ds = DriveService()
            drive_projs = ds.scan_projects_from_drive()
            if drive_projs:
                self.saved_projects = drive_projs
                try:
                    os.makedirs(data_dir, exist_ok=True)
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(drive_projs, f, indent=2, ensure_ascii=False)
                except Exception:
                    pass
                return
        except Exception as e:
            print(f"[FlowState] Error loading projects from Drive: {e}")
        finally:
            self.is_syncing_drive_projects = False

    def sync_projects_from_drive_action(self):
        """Action handler to manually trigger a sync with Google Drive"""
        self.load_projects_from_drive(force_remote=True)
        count = len(self.saved_projects)
        if count > 0:
            self.trigger_toast(f"Sincronización con Google Drive completada ({count} proyectos activos)", "success")
        else:
            self.trigger_toast("Google Drive no contiene carpetas de proyectos adicionales", "info")

    def init_app_data(self):
        """Global initialization handler on page load (instant cache first)"""
        try:
            from backend.services.user_service import load_users
            self.users_list = load_users()
        except Exception as e:
            print(f"[FlowState] Error initializing users: {e}")
        self.load_projects_from_drive(force_remote=False)

    # Hub Computed Properties & KPIs
    @rx.var
    def filtered_hub_projects(self) -> List[Dict[str, Any]]:
        """Filter projects based on User Role, Search Query, Phase and Health Status"""
        projs = list(self.saved_projects)

        # 1. Role Filter
        if self.user_role == "project_manager":
            projs = [p for p in projs if "José" in p.get("manager", "") or "Antonio" in p.get("manager", "") or "Hurtado" in p.get("manager", "")]
        elif self.user_role == "collaborator":
            curr_u = next((u for u in self.users_list if u.get("email", "").strip().lower() == self.user_email.strip().lower()), None)
            assigned = curr_u.get("assigned_projects", []) if curr_u else []
            if "all" not in assigned and assigned:
                projs = [p for p in projs if p.get("id") in assigned or p.get("code") in assigned]

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
        evaluated = [int(p.get("audit_score", 0)) for p in self.saved_projects if p.get("health_status") != "unrated" and int(p.get("audit_score", 0)) > 0]
        if not evaluated:
            return 100
        return int(sum(evaluated) / len(evaluated))

    @rx.var
    def hub_drive_synced_count(self) -> int:
        return sum(1 for p in self.saved_projects if p.get("drive_folder_url"))

    @rx.var
    def hub_drive_synced_pct(self) -> int:
        total = len(self.saved_projects)
        if total == 0:
            return 0
        return int((self.hub_drive_synced_count / total) * 100)

    @rx.var
    def hub_drive_status_summary(self) -> str:
        return f"{self.hub_drive_synced_count} de {len(self.saved_projects)} integrados con Drive ({self.hub_drive_synced_pct}%)"

    @rx.var
    def active_sprints_count(self) -> int:
        count = 0
        for p in self.saved_projects:
            sprints = p.get("plan_sprints", [])
            has_active = any(s.get("status") in ["In Progress", "En Progreso", "Activo"] for s in sprints)
            if has_active:
                count += 1
        return count

    @rx.var
    def projects_needing_attention(self) -> List[Dict[str, Any]]:
        """Return projects in yellow or red status requiring executive attention"""
        return [p for p in self.saved_projects if p.get("health_status") in ["yellow", "red"]]

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
        """Open project in Level 2 Workspace and load full state (T15 & F02)"""
        self.unselect_node()
        self.load_saved_project(proj_id)
        self.active_mode = "workspace"
        self.active_view = "charter"  # Clear landing on Charter view for consistent onboarding & context
        self.is_workspace_dirty = False
        self.auto_save_status = "Sincronizado"
        self.status_message = f"Espacio de trabajo abierto: {self.project_name}"

    def return_to_hub(self):
        """Save changes and return to Level 1 Hub (F02)"""
        self.unselect_node()
        if getattr(self, "is_workspace_dirty", False):
            self.save_current_project()
            self.is_workspace_dirty = False
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

    # 3-Step Project Creation Wizard State
    new_proj_wizard_step: int = 1

    def set_new_proj_wizard_step(self, step: int):
        self.new_proj_wizard_step = step

    def next_wizard_step(self):
        if self.new_proj_wizard_step == 1:
            name_clean = self.new_proj_name.strip()
            if not name_clean:
                self.status_message = "Por favor ingresa un nombre para el proyecto."
                return
            code_clean = self.new_proj_code.strip().upper()
            if not code_clean:
                self.new_proj_code = f"PRJ-{len(self.saved_projects) + 1:03d}"
            elif any(p.get("code", "").strip().upper() == code_clean for p in self.saved_projects):
                self.status_message = f"Error: Ya existe un proyecto con el código '{code_clean}'. Ingresa un código único."
                return
            self.new_proj_wizard_step = 2
        elif self.new_proj_wizard_step == 2:
            self.new_proj_wizard_step = 3

    def prev_wizard_step(self):
        if self.new_proj_wizard_step > 1:
            self.new_proj_wizard_step -= 1

    def open_new_project_modal(self):
        import datetime
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        default_end = (datetime.date.today() + datetime.timedelta(days=90)).strftime("%Y-%m-%d")
        self.new_proj_name = ""
        self.new_proj_code = f"PRJ-{len(self.saved_projects) + 1:03d}"
        self.new_proj_purpose = ""
        self.new_proj_manager = self.user_name
        self.new_proj_sponsor = "Dirección de Operaciones & Tecnología"
        self.new_proj_start_date = today_str
        self.new_proj_end_date = default_end
        self.creation_progress_status = ""
        self.is_creating_project_drive = False
        self.new_proj_wizard_step = 1
        self.show_new_project_modal = True

    def close_new_project_modal(self):
        self.show_new_project_modal = False
        self.is_creating_project_drive = False
        self.new_proj_wizard_step = 1

    def set_show_new_project_modal(self, val: bool):
        self.show_new_project_modal = val

    def create_project_with_drive(self):
        """Create new project in Drive via SA, replicate sheet and open workspace"""
        if self.is_creating_project_drive:
            return

        name_clean = self.new_proj_name.strip()
        if not name_clean:
            self.status_message = "Por favor ingresa un nombre para el proyecto."
            return

        code_clean = self.new_proj_code.strip().upper()
        if not code_clean:
            code_clean = f"PRJ-{len(self.saved_projects) + 1:03d}"

        # T03: Validate unique project code before triggering backend/Drive
        if any(p.get("code", "").strip().upper() == code_clean for p in self.saved_projects):
            self.status_message = f"Error: Ya existe un proyecto con el código '{code_clean}'. Ingresa un código único."
            return

        self.is_creating_project_drive = True
        self.creation_progress_status = "1/4 Conectando con Google Drive Service Account..."

        drive_folder_id = ""
        drive_folder_url = ""
        sheet_id = ""
        sheet_url = ""

        try:
            from backend.services.drive_service import DriveService
            ds = DriveService()

            clean_folder_name = name_clean.replace(" ", "_")
            self.creation_progress_status = "2/4 Creando estructura de 11 carpetas oficiales en Drive..."

            # 1. Create project folder + 11 subfolders
            ok_folder, folder_res = ds.create_project_folder(clean_folder_name, code_clean)
            if ok_folder:
                drive_folder_id = folder_res
                drive_folder_url = f"https://drive.google.com/drive/folders/{drive_folder_id}"
                self.creation_progress_status = "3/4 Replicando plantilla oficial de Google Sheets..."

                # 2. Replicate master Google Sheet
                ok_sheet, sheet_res = ds.replicate_master_sheet_template(drive_folder_id, clean_folder_name)
                if ok_sheet:
                    sheet_id = sheet_res
                    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
        except Exception as e:
            print(f"Drive creation notice: {e}")

        self.creation_progress_status = "4/4 Inicializando proyecto y plan de trabajo..."

        # Build project dictionary with exact form dates and unrated health status
        import datetime
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        new_id = f"proj-{int(datetime.datetime.now().timestamp())}"

        manager_name = self.new_proj_manager.strip() or self.user_name
        initials = "".join([part[0].upper() for part in manager_name.split() if part])[:2] or "JH"

        start_d = self.new_proj_start_date or datetime.date.today().strftime("%Y-%m-%d")
        end_d = self.new_proj_end_date or (datetime.date.today() + datetime.timedelta(days=90)).strftime("%Y-%m-%d")
        purpose_str = self.new_proj_purpose.strip() or "Definir el alcance y objetivos operativos."

        new_proj_dict = {
            "id": new_id,
            "code": code_clean,
            "name": name_clean,
            "purpose": purpose_str,
            "manager": manager_name,
            "manager_initials": initials,
            "sponsor": self.new_proj_sponsor.strip() or "Dirección de Operaciones & Tecnología",
            "start_date": start_d,
            "end_date": end_d,
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
            "total_sp": 0,
            "completed_tasks": 0,
            "total_tasks": 0,
            "health_status": "unrated",
            "audit_score": 0,
            "nodes_count": 1,
            "steps_count": 1,
            "plan_start_date": start_d,
            "plan_end_date": end_d,
            "plan_daily_hours": 8,
            "plan_work_days_mode": "mon_fri",
            "plan_activities_description": purpose_str,
            "plan_sprints": [],
            "plan_backlog_items": [],
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
            "narrative_text": f"# Manual de Procedimientos\n# {name_clean}\n\n## 1. Objetivo\n{purpose_str}\n"
        }

        self.saved_projects.insert(0, new_proj_dict)
        self.is_creating_project_drive = False
        self.show_new_project_modal = False
        self.open_project_workspace(new_id)
        self.status_message = f"Proyecto '{name_clean}' ({code_clean}) creado con éxito"

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
        self.narrative_text = f"# Manual de Procedimientos\n# {self.project_name}\n\n## 1. Objetivo\n{self.project_purpose}\n"
        self.show_recent_modal = False
        self.status_message = f"Nuevo proceso '{self.project_name}' inicializado"

    def select_page_tab(self, index: int):
        """Save current tab state and switch active page with strict deselection"""
        self.unselect_node()
        if 0 <= self.active_page_index < len(self.project_pages):
            self.project_pages[self.active_page_index]["nodes"] = list(self.nodes)
            self.project_pages[self.active_page_index]["edges"] = list(self.edges)
            self.project_pages[self.active_page_index]["swimlanes"] = list(self.swimlanes)

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
        self.unselect_node()
        # Save current active page
        if 0 <= self.active_page_index < len(self.project_pages):
            self.project_pages[self.active_page_index]["nodes"] = list(self.nodes)
            self.project_pages[self.active_page_index]["edges"] = list(self.edges)
            self.project_pages[self.active_page_index]["swimlanes"] = list(self.swimlanes)

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
        """Delete a diagram page tab from the project with strict deselection"""
        self.unselect_node()
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
            if page.get("swimlanes"):
                self.swimlanes = list(page["swimlanes"])
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

        # Dynamic metrics derived directly from backlog and structure
        total_sp = sum(int(item.get("story_points", 0)) for item in self.plan_backlog_items)
        completed_sp = sum(int(item.get("story_points", 0)) for item in self.plan_backlog_items if item.get("status") in ["Completado", "Done", "Finalizado"])
        prog_pct = round((completed_sp / max(1, total_sp)) * 100, 1) if total_sp > 0 else 0.0
        total_tasks = len(self.plan_backlog_items)
        completed_tasks = sum(1 for item in self.plan_backlog_items if item.get("status") in ["Completado", "Done", "Finalizado"])

        current_dict = {
            "id": self.project_id or f"proj-{len(self.saved_projects) + 1}",
            "code": getattr(self, "project_code", existing.get("code", "PRJ")),
            "name": self.project_name,
            "purpose": self.project_purpose,
            "manager": self.project_manager,
            "manager_initials": existing.get("manager_initials", "JH"),
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
            "current_sprint": next((s["sprint_id"] for s in self.plan_sprints if s.get("status") in ["En Progreso", "In Progress", "Activo"]), ("Sprint 01" if self.plan_sprints else "Sin Sprint")),
            "current_sprint_name": next((s.get("modules", "General") for s in self.plan_sprints if s.get("status") in ["En Progreso", "In Progress", "Activo"]), (self.plan_sprints[0].get("modules", "General") if self.plan_sprints else "Sin Agenda")),
            "progress_percentage": prog_pct,
            "completed_sp": completed_sp,
            "total_sp": total_sp,
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks,
            "health_status": "green" if self.audit_score >= 80 else ("yellow" if self.audit_score >= 60 else ("unrated" if not self.has_audit_run else "red")),
            "audit_score": self.audit_score,
            "previous_audit_score": self.previous_audit_score,
            "last_audit_date": self.last_audit_date,
            "has_audit_run": self.has_audit_run,
            "is_audit_outdated": self.is_audit_outdated,
            "audit_findings": list(self.audit_findings),
            "gate_approvals_history": list(self.gate_approvals_history),
            "nodes_count": len(self.nodes),
            "steps_count": len(self.sipoc_rows),
            "plan_start_date": self.plan_start_date,
            "plan_end_date": self.plan_end_date,
            "plan_daily_hours": self.plan_daily_hours,
            "plan_work_days_mode": self.plan_work_days_mode,
            "plan_activities_description": self.plan_activities_description,
            "plan_sprints": list(self.plan_sprints),
            "plan_backlog_items": list(self.plan_backlog_items),
            "sipoc_rows": list(self.sipoc_rows),
            "customer_requirements": self.customer_requirements,
            "nodes": list(self.nodes),
            "edges": list(self.edges),
            "swimlanes": list(self.swimlanes),
            "project_pages": list(self.project_pages),
            "narrative_text": self.narrative_text,
            "narrative_documents": list(self.narrative_documents),
            "active_narrative_doc_id": self.active_narrative_doc_id,
            "active_narrative_doc_name": self.active_narrative_doc_name,
            "narrative_total_blocks": self.narrative_total_blocks,
            "extracted_findings": list(self.extracted_findings),
            "clarification_points": list(self.clarification_points),
            "narrative_overview_target": self.narrative_overview_target,
            "narrative_overview_scope": self.narrative_overview_scope,
            "narrative_overview_input": self.narrative_overview_input,
            "narrative_overview_output": self.narrative_overview_output,
            "narrative_overview_frequency": self.narrative_overview_frequency,
            "narrative_legal_framework": list(self.narrative_legal_framework),
            "narrative_validity_control": dict(self.narrative_validity_control),
            "narrative_asis_steps_data": list(self.narrative_asis_steps_data),
            "narrative_tobe_steps_data": list(self.narrative_tobe_steps_data),
            "generated_narrative_markdown": self.generated_narrative_markdown,
            "sipoc_rows_asis": list(self.sipoc_rows_asis),
            "sipoc_rows_tobe": list(self.sipoc_rows_tobe)
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

        # Update local file cache
        try:
            import os, json
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            os.makedirs(data_dir, exist_ok=True)
            cache_file = os.path.join(data_dir, "saved_projects.json")
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(new_list, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        # Sync project state to Google Drive
        try:
            from backend.services.drive_service import DriveService
            ds = DriveService()
            ok_drv, drv_msg = ds.save_project_to_drive(current_dict)
            if ok_drv and current_dict.get("drive_folder_id"):
                self.drive_folder_id = current_dict["drive_folder_id"]
                self.drive_folder_url = current_dict.get("drive_folder_url", "")
        except Exception as e:
            print(f"[FlowState] Drive save warning: {e}")

        try:
            from datetime import datetime
            self.last_saved_time = datetime.now().strftime("%H:%M")
        except Exception:
            self.last_saved_time = "12:00"
        self.auto_save_status = f"Sincronizado {self.last_saved_time}"
        self.status_message = f"Proceso '{self.project_name}' guardado exitosamente ({now_str})"
        self.trigger_toast(f"Proyecto '{self.project_name}' sincronizado con éxito", "success")

    def save_diagram(self):
        """Alias for save_current_project called from menu"""
        self.save_current_project()

    def load_saved_project(self, proj_id: str):
        """Load a selected project from saved projects into active workspace (F02, F03, H01)"""
        self.unselect_node()
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

        # T04 & T02: Work plan & Backlog isolation per project
        self.plan_start_date = selected.get("plan_start_date", selected.get("start_date", "2026-01-16"))
        self.plan_end_date = selected.get("plan_end_date", selected.get("end_date", "2026-12-04"))
        self.plan_daily_hours = selected.get("plan_daily_hours", 8)
        self.plan_work_days_mode = selected.get("plan_work_days_mode", "mon_fri")
        self.plan_activities_description = selected.get("plan_activities_description", selected.get("purpose", ""))
        self.plan_sprints = list(selected.get("plan_sprints", []))
        self.plan_backlog_items = list(selected.get("plan_backlog_items", []))

        if selected.get("sipoc_rows"):
            self.sipoc_rows = list(selected["sipoc_rows"])
        if selected.get("customer_requirements"):
            self.customer_requirements = selected["customer_requirements"]

        self.narrative_documents = list(selected.get("narrative_documents", []))
        self.active_narrative_doc_id = selected.get("active_narrative_doc_id", "")
        self.active_narrative_doc_name = selected.get("active_narrative_doc_name", "")
        self.narrative_total_blocks = int(selected.get("narrative_total_blocks", 0))
        self.extracted_findings = list(selected.get("extracted_findings", []))
        self.clarification_points = list(selected.get("clarification_points", []))
        self.narrative_overview_target = selected.get("narrative_overview_target", "")
        self.narrative_overview_scope = selected.get("narrative_overview_scope", "")
        self.narrative_overview_input = selected.get("narrative_overview_input", "")
        self.narrative_overview_output = selected.get("narrative_overview_output", "")
        self.narrative_overview_frequency = selected.get("narrative_overview_frequency", "Siempre que la operación lo requiera")
        self.narrative_legal_framework = list(selected.get("narrative_legal_framework", []))
        self.narrative_validity_control = dict(selected.get("narrative_validity_control", {}))
        self.narrative_asis_steps_data = list(selected.get("narrative_asis_steps_data", []))
        self.narrative_tobe_steps_data = list(selected.get("narrative_tobe_steps_data", []))
        self.generated_narrative_markdown = selected.get("generated_narrative_markdown", "")
        self.sipoc_rows_asis = list(selected.get("sipoc_rows_asis", []))
        self.sipoc_rows_tobe = list(selected.get("sipoc_rows_tobe", []))

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

        self.gate_approvals_history = list(selected.get("gate_approvals_history", []))
        self.is_audit_outdated = bool(selected.get("is_audit_outdated", False))

        if selected.get("has_audit_run") or selected.get("last_audit_date"):
            self.has_audit_run = True
            self.last_audit_date = str(selected.get("last_audit_date", ""))
            self.audit_score = int(selected.get("audit_score", 0))
            self.previous_audit_score = int(selected.get("previous_audit_score", self.audit_score))
            self.audit_findings = list(selected.get("audit_findings", []))
        else:
            self.has_audit_run = False
            self.last_audit_date = ""
            self.audit_score = 0
            self.previous_audit_score = 0
            self.audit_findings = []

        self.show_recent_modal = False
        self.status_message = f"Flujo '{self.project_name}' cargado con éxito en todas las vistas"

    def delete_saved_project(self, proj_id: str):
        """Delete a project from catalog and move its folder to Trash in Google Drive"""
        target = next((p for p in self.saved_projects if p.get("id") == proj_id), None)
        self.saved_projects = [p for p in self.saved_projects if p.get("id") != proj_id]
        
        # Update local cache
        try:
            import os, json
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            cache_file = os.path.join(data_dir, "saved_projects.json")
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(self.saved_projects, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        # Trash folder in Google Drive
        if target and target.get("drive_folder_id"):
            try:
                from backend.services.drive_service import DriveService
                ds = DriveService()
                ds.delete_project_from_drive(target["drive_folder_id"])
            except Exception as e:
                print(f"[FlowState] Error trashing project in Drive: {e}")

        proj_name = target.get("name", proj_id) if target else proj_id
        self.status_message = f"Proyecto '{proj_name}' eliminado"
        self.trigger_toast(f"Proyecto '{proj_name}' eliminado del catálogo", "info")

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

    # Toast Notification System State
    show_toast: bool = False
    toast_message: str = ""
    toast_type: str = "success"

    def trigger_toast(self, message: str, toast_type: str = "success"):
        """Display a floating non-intrusive notification toast"""
        self.toast_message = message
        self.toast_type = toast_type
        self.show_toast = True

    def dismiss_toast(self):
        """Close floating notification toast"""
        self.show_toast = False

    # Connector Modal & Interactive Line Connection State
    show_connect_modal: bool = False
    connect_target_id: str = ""
    connect_label: str = ""
    auto_save_status: str = "Sincronizado"
    last_saved_time: str = "12:00"

    @rx.var
    def target_node_options(self) -> List[str]:
        """Return candidate target node option strings for connect modal"""
        return [f"{n['id']} - {n.get('label', '')}" for n in self.nodes if n["id"] != self.selected_node_id]

    # AI Process Auditor State & Quality Deltas (F03, H03)
    show_audit_modal: bool = False
    is_auditing_ai: bool = False
    has_audit_run: bool = False
    is_audit_outdated: bool = False
    audit_score: int = 0
    previous_audit_score: int = 0
    last_audit_date: str = ""
    audit_rules_version: str = "v2.4 Six Sigma Enterprise"
    audit_findings: List[Dict[str, Any]] = []

    @rx.var
    def audit_score_delta(self) -> int:
        return self.audit_score - self.previous_audit_score

    @rx.var
    def audit_score_delta_label(self) -> str:
        if not self.has_audit_run or self.previous_audit_score == 0:
            return "Primera evaluación"
        delta = self.audit_score_delta
        if delta > 0:
            return f"+{delta} pts"
        elif delta < 0:
            return f"{delta} pts"
        return "= pts"

    def mark_audit_outdated(self):
        """Flag audit as outdated when BPMN or SIPOC model is modified (H03)"""
        if self.has_audit_run:
            self.is_audit_outdated = True

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
        self.mark_audit_outdated()
        self.trigger_auto_save()

    def delete_edge(self, edge_id: str):
        """Delete an edge connector"""
        self.edges = [e for e in self.edges if e.get("id") != edge_id]
        self.status_message = "Conector eliminado"
        self.mark_audit_outdated()
        self.trigger_auto_save()

    def trigger_auto_save(self):
        """Save active diagram page state and update auto-save badge"""
        if 0 <= self.active_page_index < len(self.project_pages):
            self.project_pages[self.active_page_index]["nodes"] = list(self.nodes)
            self.project_pages[self.active_page_index]["edges"] = list(self.edges)
        self.auto_save_status = "Cambios Guardados"

    def open_audit_modal(self):
        """Open AI Process Auditor modal (F03)"""
        self.show_audit_modal = True

    def close_audit_modal(self):
        self.show_audit_modal = False

    def run_ai_process_audit(self):
        """Execute Gemini AI & Structural Governance Audit on current active flowchart tab (F03, H03)"""
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

        from datetime import datetime
        new_score = max(0, 100 - deductions)
        self.previous_audit_score = self.audit_score if self.has_audit_run else new_score
        self.audit_score = new_score
        self.has_audit_run = True
        self.is_audit_outdated = False
        self.last_audit_date = datetime.now().strftime("%d %b %Y, %H:%M")
        self.audit_findings = findings
        self.is_auditing_ai = False
        self.save_current_project()
        self.trigger_toast(f"Auditoría IA completada: {self.audit_score}/100 pts", "success")

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
