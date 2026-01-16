#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuración de Keycloak para TEMIS
Reutiliza la configuración de Maxibot
"""

import os

# ============================================
# 🔧 CONFIGURACIÓN DE KEYCLOAK (MAXIBOT)
# ============================================

# URL del servidor Keycloak (sin / al final)
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "https://sso.maxilabs.net/auth")

# Nombre del Realm en Keycloak
REALM = os.getenv("KEYCLOAK_REALM", "zeusDev")

# Client ID configurado en Keycloak (MISMO QUE MAXIBOT)
CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "maxi-business-ai")

# Client Secret (obtenerlo de Keycloak -> Clients -> Credentials)
CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "mOLonfMkGYnhq3M4CSnzY4p7fFakNciu")

# URI de redirección (debe estar configurada en Keycloak)
REDIRECT_URI = os.getenv("KEYCLOAK_REDIRECT_URI", "http://localhost:8080/callback")

# Puerto y host para el servidor de callback local
APP_PORT = int(os.getenv("KEYCLOAK_CALLBACK_PORT", "8080"))
APP_HOST = os.getenv("KEYCLOAK_CALLBACK_HOST", "localhost")

# ============================================
# 👤 CONFIGURACIÓN DE OWNER PRINCIPAL
# ============================================

# Owner principal de TEMIS (puede asignar otros owners)
PRIMARY_OWNER_EMAIL = "mxjhurtado@maxillc.com"

# Roles requeridos para acceder a TEMIS
REQUIRED_ROLES = []  # Sin restricción de roles, validación por email

# ============================================
# Endpoints de Keycloak (generados automáticamente)
# ============================================
AUTH_ENDPOINT = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/auth"
TOKEN_ENDPOINT = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
USERINFO_ENDPOINT = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/userinfo"
LOGOUT_ENDPOINT = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/logout"
