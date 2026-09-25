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
    }
]


def _ensure_data_file() -> None:
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(USERS_FILE):
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(SEED_USERS, f, indent=2, ensure_ascii=False)
            logger.info("Initialized users.json with super admin account.")
    except Exception as e:
        logger.error(f"Error ensuring users file: {e}")


def load_users() -> List[Dict[str, Any]]:
    """
    Load users directory from Google Drive (primary cloud storage)
    or local users.json (offline fallback cache).
    """
    _ensure_data_file()
    raw_users = None

    # 1. Try loading from Google Drive 00_Configuracion/users_directory.json
    try:
        from backend.services.drive_service import DriveService
        ds = DriveService()
        drive_users = ds.load_users_from_drive()
        if drive_users and isinstance(drive_users, list) and len(drive_users) > 0:
            raw_users = drive_users
            # Sync to local cache
            try:
                with open(USERS_FILE, "w", encoding="utf-8") as f:
                    json.dump(drive_users, f, indent=2, ensure_ascii=False)
            except Exception:
                pass
    except Exception as e:
        logger.debug(f"Drive users load unavailable (using local cache): {e}")

    # 2. If not loaded from Drive, read local cache
    if raw_users is None:
        try:
            if os.path.exists(USERS_FILE):
                with open(USERS_FILE, "r", encoding="utf-8") as f:
                    raw_users = json.load(f)
        except Exception as e:
            logger.error(f"Error reading local users.json: {e}")

    if not raw_users or not isinstance(raw_users, list):
        raw_users = list(SEED_USERS)

    # 3. Ensure super admin exists
    if not any(u.get("role") == "super_admin" for u in raw_users):
        raw_users.insert(0, dict(SEED_USERS[0]))

    # 4. Normalize fields
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
                u["assigned_projects"] = []
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


def save_users(users: List[Dict[str, Any]]) -> bool:
    """
    Save users to local file cache and sync immediately to Google Drive.
    """
    _ensure_data_file()
    ok_local = False
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        ok_local = True
    except Exception as e:
        logger.error(f"Error saving local users: {e}")

    # Sync to Google Drive
    try:
        from backend.services.drive_service import DriveService
        ds = DriveService()
        ds.save_users_to_drive(users)
    except Exception as e:
        logger.debug(f"Could not sync users to Google Drive: {e}")

    return ok_local


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
