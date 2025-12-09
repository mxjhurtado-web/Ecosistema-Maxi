#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuración de Keycloak para ATHENAS Lite
Usa la misma configuración que MaxiBot y HADES (mismo client)
"""

import os

# ============================================
# 🔧 CONFIGURACIÓN DE KEYCLOAK (EDITAR AQUÍ)
# ============================================
# Puedes usar variables de entorno o valores hardcoded

# URL del servidor Keycloak (sin / al final)
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "https://sso.maxilabs.net/auth")

# Nombre del Realm en Keycloak
REALM = os.getenv("KEYCLOAK_REALM", "zeusDev")

# Client ID configurado en Keycloak (mismo que MaxiBot y HADES)
CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "maxi-business-ai")

# Client Secret (obtenerlo de Keycloak -> Clients -> Credentials)
CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "mOLonfMkGYnhq3M4CSnzY4p7fFakNciu")

# URI de redirección (debe estar configurada en Keycloak)
REDIRECT_URI = os.getenv("KEYCLOAK_REDIRECT_URI", "http://localhost:8080/callback")

# Puerto y host para el servidor de callback local
APP_PORT = int(os.getenv("KEYCLOAK_CALLBACK_PORT", "8080"))
APP_HOST = os.getenv("KEYCLOAK_CALLBACK_HOST", "localhost")

# Roles requeridos para acceder a ATHENAS (vacío = todos los usuarios autenticados)
REQUIRED_ROLES = []

# ============================================
# Endpoints de Keycloak (generados automáticamente)
# ============================================
AUTH_ENDPOINT = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/auth"
TOKEN_ENDPOINT = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
USERINFO_ENDPOINT = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/userinfo"
LOGOUT_ENDPOINT = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/logout"
