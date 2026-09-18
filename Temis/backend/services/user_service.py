# -*- coding: utf-8 -*-
"""
User Management & Authentication Service for TEMIS
Handles JSON-based persistence, authentication, RBAC profiles and user directory.
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
        "label": "👑 Super Admin",
        "description": "Acceso total a portafolio, usuarios, auditoría y Google Workspace",
        "badge_color": "purple"
    },
    "project_manager": {
        "label": "👔 Dueño de Proyecto (PM)",
        "description": "Gestión completa de sus proyectos, Sprints, Backlog y Flujos",
        "badge_color": "blue"
    },
    "analyst": {
        "label": "📊 Analista de Procesos",
        "description": "Modelado de diagramas Bézier, matriz SIPOC y bitácora de daily logs",
        "badge_color": "teal"
    },
    "qa_auditor": {
        "label": "🛡️ Auditor QA / Six Sigma",
        "description": "Auditoría de calidad IA, evaluación de reglas y control de fases",
        "badge_color": "amber"
    },
    "collaborator": {
        "label": "👥 Colaborador (Invitado)",
        "description": "Lectura, visualización y aportación de comentarios",
        "badge_color": "gray"
    }
}

DEFAULT_SUPER_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "mxjhurtado@maxillc.com")
DEFAULT_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "Temis123456*")

SEED_USERS: List[Dict[str, Any]] = [
    {
        "email": DEFAULT_SUPER_ADMIN_EMAIL,
        "name": "Ing. Mario Hurtado",
        "password": DEFAULT_PASSWORD,
        "role": "super_admin",
        "role_label": "👑 Super Admin",
        "department": "Dirección General & Tecnología",
        "status": "active",
        "created_at": "2026-01-16",
        "last_login": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    },
    {
        "email": "ana.martinez@maxillc.com",
        "name": "Lic. Ana Martínez",
        "password": DEFAULT_PASSWORD,
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
        "password": DEFAULT_PASSWORD,
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
        "password": DEFAULT_PASSWORD,
        "role": "qa_auditor",
        "role_label": "🛡️ Auditor QA / Six Sigma",
        "department": "Calidad & Gobernanza",
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
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
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
    password: str = DEFAULT_PASSWORD
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
    
    new_user = {
        "email": clean_email,
        "name": name.strip(),
        "password": password or DEFAULT_PASSWORD,
        "role": role,
        "role_label": role_info["label"],
        "department": department.strip() or "General",
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
            save_users(users)
            return True, f"Perfil de '{clean_email}' actualizado a {role_info['label']}."
            
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
