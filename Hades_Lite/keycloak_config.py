#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuración de Keycloak para HADES
Usa la misma configuración que MaxiBot (mismo client)
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

# Client ID configurado en Keycloak (mismo que MaxiBot)
CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "maxi-business-ai")

# Client Secret (obtenerlo de Keycloak -> Clients -> Credentials)
CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "mOLonfMkGYnhq3M4CSnzY4p7fFakNciu")

# URI de redirección (debe estar configurada en Keycloak)
REDIRECT_URI = os.getenv("KEYCLOAK_REDIRECT_URI", "http://localhost:8080/callback")

# Puerto y host para el servidor de callback local
APP_PORT = int(os.getenv("KEYCLOAK_CALLBACK_PORT", "8080"))
APP_HOST = os.getenv("KEYCLOAK_CALLBACK_HOST", "localhost")

# Roles requeridos para acceder a MaxiBot (configurar en Keycloak)
REQUIRED_ROLES = []

# ============================================
# Endpoints de Keycloak (generados automáticamente)
# ============================================
AUTH_ENDPOINT = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/auth"
TOKEN_ENDPOINT = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
USERINFO_ENDPOINT = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/userinfo"
LOGOUT_ENDPOINT = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/logout"


# ============================================
# 📋 INSTRUCCIONES DE CONFIGURACIÓN
# ============================================
"""
Para configurar Keycloak con tu servicio existente:

1. EDITAR LOS VALORES ARRIBA O USAR VARIABLES DE ENTORNO:

   Opción A - Valores hardcoded (editar directamente en este archivo):
   KEYCLOAK_URL = "https://tu-keycloak.com"
   REALM = "tu-realm"
   CLIENT_ID = "tu-client-id"
   CLIENT_SECRET = "tu-client-secret"
   REDIRECT_URI = "http://localhost:8080/callback"

   Opción B - Variables de entorno (recomendado):
   export KEYCLOAK_URL="https://tu-keycloak.com"
   export KEYCLOAK_REALM="tu-realm"
   export KEYCLOAK_CLIENT_ID="tu-client-id"
   export KEYCLOAK_CLIENT_SECRET="tu-client-secret"
   export KEYCLOAK_REDIRECT_URI="http://localhost:8080/callback"

2. CONFIGURAR EN KEYCLOAK:

   a) Crear un Client en Keycloak:
      - Client ID: el valor de CLIENT_ID arriba
      - Client Protocol: openid-connect
      - Access Type: confidential
      - Valid Redirect URIs: http://localhost:8080/callback
      - Web Origins: http://localhost:8080

   b) Obtener Client Secret:
      - En Keycloak Admin -> Clients -> tu-client -> Credentials
      - Copiar el Secret y ponerlo en CLIENT_SECRET

   c) Crear Roles:
      - En Keycloak Admin -> Roles -> Add Role
      - Crear roles: maxibot-user y/o maxibot-admin

   d) Asignar Roles a Usuarios:
      - En Keycloak Admin -> Users -> [usuario] -> Role Mappings
      - Asignar rol maxibot-user o maxibot-admin

3. INSTALAR DEPENDENCIAS:
   pip install requests PyJWT

4. EJECUTAR:
   python MaxiBot_V4.6.1_mcp.py
"""
