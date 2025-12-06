# registro_adapter.py
# -*- coding: utf-8 -*-
"""
Adaptador de logging para MaxiBot v4.5 con soporte para Keycloak.s
- Expone métodos info/warn/error que MaxiBot espera.
- Persiste en SQLite vía las funciones de registro.py originales.
- Integra información de autenticación Keycloak cuando está disponible.
"""
from __future__ import annotations

from typing import Any
import registro as reg  # usa tu archivo `registro.py` existente


class RegistroSQLiteAdapter:
    def __init__(self, correo="sistema@maxi", nombre="MaxiBot",
                 version="v4.5-keycloak", keycloak_auth=None):
        try:
            reg.crear_base()
        except Exception:
            pass

        # Usar información de Keycloak si está disponible
        if (keycloak_auth and hasattr(keycloak_auth, 'get_user_email')
                and keycloak_auth.get_user_email()):
            self.correo = keycloak_auth.get_user_email()
            self.nombre = keycloak_auth.get_user_name() or "Usuario Keycloak"
        else:
            self.correo = correo
            self.nombre = nombre

        self.version = version
        self.keycloak_auth = keycloak_auth

        try:
            reg.registrar_ingreso(self.correo, self.nombre, self.version)
        except Exception:
            pass

    def _get_auth_source(self) -> str:
        """Determina la fuente de autenticación para el logging"""
        if (self.keycloak_auth and hasattr(self.keycloak_auth, 'is_authenticated')
                and self.keycloak_auth.is_authenticated()):
            return "KEYCLOAK"
        return "TRADICIONAL"

    def info(self, msg: str, **kwargs: Any):
        try:
            auth_source = self._get_auth_source()
            full_msg = f"[{auth_source}] {msg} {kwargs or ''}"
            reg.registrar_consulta(self.correo, "INFO", full_msg)
        except Exception:
            print("[INFO]", msg, kwargs or "")

    def warn(self, msg: str, **kwargs: Any):
        try:
            auth_source = self._get_auth_source()
            full_msg = f"[{auth_source}] {msg} {kwargs or ''}"
            reg.registrar_consulta(self.correo, "WARN", full_msg)
        except Exception:
            print("[WARN]", msg, kwargs or "")

    def error(self, msg: str, **kwargs: Any):
        try:
            auth_source = self._get_auth_source()
            full_msg = f"[{auth_source}] {msg} {kwargs or ''}"
            reg.registrar_consulta(self.correo, "ERROR", full_msg)
        except Exception:
            print("[ERROR]", msg, kwargs or "")

    def update_auth(self, keycloak_auth=None):
        """Actualiza la información de autenticación"""
        self.keycloak_auth = keycloak_auth
        if (keycloak_auth and hasattr(keycloak_auth, 'get_user_email')
                and keycloak_auth.get_user_email()):
            self.correo = keycloak_auth.get_user_email()
            self.nombre = keycloak_auth.get_user_name() or "Usuario Keycloak"
