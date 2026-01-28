#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de verificación pre-ejecución para MaxiBot V4.6.2
Verifica que todas las configuraciones estén correctas antes de ejecutar
"""

import sys
import os

print("=" * 60)
print("🔍 VERIFICACIÓN PRE-EJECUCIÓN - MaxiBot V4.6.2 DevOpsMCP")
print("=" * 60)

# 1. Verificar Python
print(f"\n✅ Python: {sys.version.split()[0]}")

# 2. Verificar dependencias críticas
print("\n📦 Verificando dependencias críticas...")
dependencias = {
    "mcp": "MCP SDK",
    "google.genai": "Google GenAI",
    "jwt": "PyJWT (Keycloak)",
    "requests": "Requests",
    "tkinter": "Tkinter (UI)"
}

faltantes = []
for modulo, nombre in dependencias.items():
    try:
        __import__(modulo)
        print(f"   ✅ {nombre}")
    except ImportError:
        print(f"   ❌ {nombre} - NO INSTALADO")
        faltantes.append(nombre)

if faltantes:
    print(f"\n⚠️  Dependencias faltantes: {', '.join(faltantes)}")
    print("   Ejecuta: pip install -r requirements.txt")
else:
    print("\n✅ Todas las dependencias instaladas")

# 3. Verificar configuración de Keycloak
print("\n🔐 Verificando configuración de Keycloak...")
try:
    import keycloak_config
    print(f"   ✅ URL: {keycloak_config.KEYCLOAK_URL}")
    print(f"   ✅ Realm: {keycloak_config.REALM}")
    print(f"   ✅ Client ID: {keycloak_config.CLIENT_ID}")
    print(f"   ✅ Client Secret: {'*' * 20} (configurado)")
    print(f"   ✅ Redirect URI: {keycloak_config.REDIRECT_URI}")
except Exception as e:
    print(f"   ❌ Error al cargar keycloak_config: {e}")

# 4. Verificar configuración de DevOps MCP
print("\n🔧 Verificando configuración de DevOps MCP...")
try:
    from devops_mcp import DevOpsMCP
    mcp = DevOpsMCP()
    print(f"   ✅ URL del MCP: {mcp.url}")
    print(f"   ℹ️  Token Keycloak: {'Configurado' if mcp.keycloak_token else 'Pendiente (se obtiene al hacer login)'}")
    print(f"   ℹ️  Gemini API Key: {'Configurado' if mcp.gemini_api_key else 'Pendiente (se ingresa en la app)'}")
except Exception as e:
    print(f"   ❌ Error al cargar DevOps MCP: {e}")

# 5. Verificar archivos críticos
print("\n📁 Verificando archivos críticos...")
archivos_criticos = [
    "MaxiBot_V4.6.2_DevOpsMCP.py",
    "keycloak_auth.py",
    "keycloak_config.py",
    "devops_mcp.py",
    "api_key_manager.py",
    "requirements.txt"
]

for archivo in archivos_criticos:
    if os.path.exists(archivo):
        print(f"   ✅ {archivo}")
    else:
        print(f"   ❌ {archivo} - NO ENCONTRADO")

# 6. Resumen final
print("\n" + "=" * 60)
if not faltantes:
    print("✅ SISTEMA LISTO PARA EJECUTAR")
    print("\nPara iniciar MaxiBot, ejecuta:")
    print("   python MaxiBot_V4.6.2_DevOpsMCP.py")
else:
    print("⚠️  SISTEMA NO LISTO - Instala las dependencias faltantes")
print("=" * 60)
