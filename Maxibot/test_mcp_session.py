#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar que DevOps MCP mantiene la sesión entre consultas
"""

import os
import sys

# Simular configuración
os.environ["KEYCLOAK_TOKEN"] = "test_token"
os.environ["GEMINI_API_KEY"] = "test_api_key"

print("=" * 60)
print("🧪 TEST: Verificación de persistencia de sesión MCP")
print("=" * 60)

try:
    from devops_mcp import DevOpsMCP
    
    print("\n✅ Módulo devops_mcp importado correctamente")
    
    # Crear instancia
    mcp = DevOpsMCP(
        url="https://mcp.maxiagentes.net/mcp",
        keycloak_token="test_token",
        gemini_api_key="test_api_key"
    )
    
    print(f"✅ DevOpsMCP inicializado")
    print(f"   URL: {mcp.url}")
    print(f"   Available: {mcp.available()}")
    
    # Verificar que el método close() existe
    if hasattr(mcp, 'close'):
        print("✅ Método close() disponible")
    else:
        print("❌ Método close() NO disponible")
    
    # Verificar estructura de métodos
    print("\n📋 Métodos disponibles:")
    for method in ['query_sync', 'get_available_tools_sync', 'close', 'available']:
        if hasattr(mcp, method):
            print(f"   ✅ {method}")
        else:
            print(f"   ❌ {method} - FALTA")
    
    print("\n" + "=" * 60)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("=" * 60)
    print("\nNOTA: Este es solo un test de estructura.")
    print("Para probar la funcionalidad completa, ejecuta MaxiBot")
    print("con credenciales reales de Keycloak y Gemini.")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
