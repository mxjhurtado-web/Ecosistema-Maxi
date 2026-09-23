# -*- coding: utf-8 -*-
"""
User Management & Authentication Service for TEMIS
Handles JSON-based persistence, authentication, RBAC profiles, assigned projects, and user directory.
100% Emoji-free and compliant with WCAG 2.2 AA.
"""

import os
import json
import logging
import datetime
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

ROLE_MAP = {
    "super_admin": {
        "label": "Super Admin",
        "description": "Acceso total a portafolio, usuarios, auditoría y Google Workspace",
        "badge_color": "purple"
    },
    "project_manager": {
        "label": "Dueño de Proyecto (PM)",
        "description": "Gestión completa de sus proyectos, Sprints, Backlog y Flujos",
        "badge_color": "blue"
    },
    "analyst": {
        "label": "Analista de Procesos",
        "description": "Modelado de diagramas Bézier, matriz SIPOC y bitácora de daily logs",
        "badge_color": "teal"
    },
    "qa_auditor": {
        "label": "Auditor QA / Six Sigma",
        "description": "Auditoría de calidad IA, evaluación de reglas y control de fases",
        "badge_color": "amber"
    },
    "collaborator": {
        "label": "Colaborador (Invitado)",
        "description": "Lectura, visualización y aportación de comentarios",
        "badge_color": "gray"
    }
}

DEFAULT_SUPER_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "mxjhurtado@maxillc.com")
DEFAULT_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "Temis123456*")

SEED_USERS: List[Dict[str, Any]] = [
    {
        "email": DEFAULT_SUPER_ADMIN_EMAIL,
        "name": "Ing. José Antonio Hurtado",
        "initials": "JH",
        "password": DEFAULT_PASSWORD,
        "role": "super_admin",
        "role_label": "Super Admin",
        "department": "Dirección General & Tecnología",
        "assigned_projects": ["all"],
        "status": "active",
        "created_at": "2026-01-16",
        "last_login": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    },
    {
        "email": "ana.martinez@maxillc.com",
        "name": "Lic. Ana Martínez",
        "initials": "AM",
        "password": DEFAULT_PASSWORD,
        "role": "project_manager",
        "role_label": "Dueño de Proyecto (PM)",
        "department": "Operaciones & Procesos",
        "assigned_projects": ["PRJ-TEMIS", "PRJ-X"],
        "status": "active",
        "created_at": "2026-02-01",
        "last_login": "2026-09-17 10:30"
    },
    {
        "email": "carlos.lopez@maxillc.com",
        "name": "Ing. Carlos López",
        "initials": "CL",
        "password": DEFAULT_PASSWORD,
        "role": "analyst",
        "role_label": "Analista de Procesos",
        "department": "Ingeniería de Software",
        "assigned_projects": ["PRJ-TEMIS"],
        "status": "active",
        "created_at": "2026-02-15",
        "last_login": "2026-09-18 09:15"
    },
    {
        "email": "laura.torres@maxillc.com",
        "name": "Mtra. Laura Torres",
        "initials": "LT",
        "password": DEFAULT_PASSWORD,
        "role": "qa_auditor",
        "role_label": "Auditor QA / Six Sigma",
        "department": "Calidad & Gobernanza",
        "assigned_projects": ["PRJ-TEMIS", "PRJ-X"],
        "status": "active",
        "created_at": "2026-03-01",
        "last_login": "2026-09-16 16:45"
    }
]


def _ensure_data_file() -> None:
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(USERS_FILE):
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(SEED_USERS, f, indent=2, ensure_ascii=False)
            logger.info("Initialized users.json with seed accounts.")
    except Exception as e:
        logger.error(f"Error ensuring users file: {e}")


def load_users() -> List[Dict[str, Any]]:
    _ensure_data_file()
    try:
        raw_users = list(SEED_USERS)
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                raw_users = json.load(f)
                
        # Ensure seed PM Ana Martínez is safely present in directory
        if not any(u.get("email", "").strip().lower() == "ana.martinez@maxillc.com" for u in raw_users):
            ana = next((s for s in SEED_USERS if s["email"] == "ana.martinez@maxillc.com"), None)
            if ana:
                raw_users.insert(1, dict(ana))
                save_users(raw_users)

        # Normalize fields: clean old emojis, ensure initials, assigned_projects, is_global_access and assigned_projects_display
        changed = False
        for u in raw_users:
            role = u.get("role", "collaborator")
            role_info = ROLE_MAP.get(role, ROLE_MAP["collaborator"])
            if u.get("role_label") != role_info["label"]:
                u["role_label"] = role_info["label"]
                changed = True
            if "assigned_projects" not in u:
                if role == "super_admin":
                    u["assigned_projects"] = ["all"]
                else:
                    u["assigned_projects"] = ["PRJ-TEMIS"]
                changed = True
            if not u.get("initials"):
                parts = u.get("name", "").split()
                u["initials"] = "".join([p[0].upper() for p in parts if p])[:2] or "US"
                changed = True
            
            # Precompute UI display properties
            is_global = (role == "super_admin") or ("all" in u.get("assigned_projects", []))
            u["is_global_access"] = is_global
            if is_global:
                u["assigned_projects_display"] = "Acceso Global"
            else:
                projs = [p for p in u.get("assigned_projects", []) if p != "all"]
                u["assigned_projects_display"] = ", ".join(projs) if projs else "Sin proyectos"
        
        if changed:
            save_users(raw_users)
        return raw_users
    except Exception as e:
        logger.error(f"Error loading users: {e}")
    return list(SEED_USERS)


def save_users(users: List[Dict[str, Any]]) -> bool:
    _ensure_data_file()
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving users: {e}")
        return False


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    if not email or not password:
        return {"error": "Por favor ingresa tu correo y contraseña."}
    
    clean_email = email.strip().lower()
    users = load_users()
    
    for u in users:
        if u.get("email", "").strip().lower() == clean_email:
            if u.get("password") == password:
                if u.get("status") == "inactive":
                    return {"error": "Tu cuenta se encuentra inactiva. Contacta al Administrador."}
                
                u["last_login"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                save_users(users)
                return u
            else:
                return {"error": "Contraseña incorrecta."}
                
    return {"error": "No existe una cuenta registrada con este correo."}


def create_user(
    email: str,
    name: str,
    role: str = "collaborator",
    department: str = "General",
    password: str = DEFAULT_PASSWORD,
    assigned_projects: Optional[List[str]] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    if not email or "@" not in email:
        return False, "El correo electrónico ingresado no es válido.", None
    if not name or len(name.strip()) < 3:
        return False, "El nombre completo debe tener al menos 3 caracteres.", None
    
    clean_email = email.strip().lower()
    users = load_users()
    
    for u in users:
        if u.get("email", "").strip().lower() == clean_email:
            return False, f"El correo '{clean_email}' ya está registrado en el sistema.", None
            
    role_info = ROLE_MAP.get(role, ROLE_MAP["collaborator"])
    parts = name.strip().split()
    initials = "".join([p[0].upper() for p in parts if p])[:2] or "US"
    
    if assigned_projects is None:
        if role == "super_admin":
            assigned_projects = ["all"]
        else:
            assigned_projects = ["PRJ-TEMIS"]
    
    new_user = {
        "email": clean_email,
        "name": name.strip(),
        "initials": initials,
        "password": password or DEFAULT_PASSWORD,
        "role": role,
        "role_label": role_info["label"],
        "department": department.strip() or "General",
        "assigned_projects": assigned_projects,
        "status": "active",
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d"),
        "last_login": "Sin ingresos aún"
    }
    
    users.append(new_user)
    if save_users(users):
        return True, f"Usuario '{clean_email}' registrado con éxito con perfil {role_info['label']}.", new_user
    else:
        return False, "Error al guardar el usuario en el almacenamiento persistente.", None


def update_user_role(email: str, new_role: str) -> Tuple[bool, str]:
    clean_email = email.strip().lower()
    users = load_users()
    
    for u in users:
        if u.get("email", "").strip().lower() == clean_email:
            role_info = ROLE_MAP.get(new_role, ROLE_MAP["collaborator"])
            u["role"] = new_role
            u["role_label"] = role_info["label"]
            if new_role == "super_admin" and "all" not in u.get("assigned_projects", []):
                u["assigned_projects"] = ["all"]
            save_users(users)
            return True, f"Perfil de '{clean_email}' actualizado a {role_info['label']}."
            
    return False, f"No se encontró el usuario '{clean_email}'."


def update_user_projects(email: str, assigned_projects: List[str]) -> Tuple[bool, str]:
    clean_email = email.strip().lower()
    users = load_users()
    
    for u in users:
        if u.get("email", "").strip().lower() == clean_email:
            u["assigned_projects"] = list(assigned_projects) if assigned_projects else []
            save_users(users)
            proj_str = ", ".join(assigned_projects) if assigned_projects else "Sin proyectos"
            return True, f"Proyectos de '{clean_email}' actualizados a: {proj_str}."
            
    return False, f"No se encontró el usuario '{clean_email}'."


def toggle_user_status(email: str) -> Tuple[bool, str]:
    clean_email = email.strip().lower()
    if clean_email == DEFAULT_SUPER_ADMIN_EMAIL:
        return False, "No se puede desactivar la cuenta del Super Administrador Principal."
        
    users = load_users()
    for u in users:
        if u.get("email", "").strip().lower() == clean_email:
            new_status = "inactive" if u.get("status") == "active" else "active"
            u["status"] = new_status
            save_users(users)
            status_text = "Activada" if new_status == "active" else "Desactivada"
            return True, f"Cuenta de '{clean_email}' {status_text}."
            
    return False, f"No se encontró el usuario '{clean_email}'."


def delete_user(email: str) -> Tuple[bool, str]:
    clean_email = email.strip().lower()
    if clean_email == DEFAULT_SUPER_ADMIN_EMAIL:
        return False, "No se puede eliminar la cuenta del Super Administrador Principal."
        
    users = load_users()
    initial_len = len(users)
    users = [u for u in users if u.get("email", "").strip().lower() != clean_email]
    
    if len(users) < initial_len:
        save_users(users)
        return True, f"Usuario '{clean_email}' eliminado correctamente."
    return False, f"No se encontró el usuario '{clean_email}'."
