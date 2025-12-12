# MaxiBot v4.6.2 DevOpsMCP

## 🆕 Nueva Versión

Esta es una versión especializada de MaxiBot que incluye integración con DevOps MCP para consultas de operaciones.

## 📋 Cambios vs v4.6.1

### ✨ Nuevas Funcionalidades

1. **Pestaña de Operaciones** 🔧
   - Chat dedicado exclusivamente para DevOps MCP
   - Consultas sobre agencias, sistemas y servicios
   - Indicador de estado en tiempo real (🟢 Conectado / 🔴 Desconectado)
   - Botón "Herramientas MCP" para ver tools disponibles

2. **Integración DevOps MCP**
   - Cliente completo con autenticación Keycloak
   - Usa Gemini 2.5 Flash (`gemini-2.5-flash`)
   - Reinicialización automática al ingresar API key
   - Soporte para consultas async y sync

3. **Módulo `devops_mcp.py`**
   - Cliente standalone para DevOps MCP
   - Interfaz async y sync
   - Gestión automática de sesiones
   - Manejo de errores robusto

### 🔧 Mejoras Técnicas

- **Modelo Gemini**: Actualizado a `gemini-2.5-flash` en todos los componentes
- **Autenticación**: Integración mejorada con Keycloak
- **UX**: Indicadores visuales de estado del MCP
- **Logging**: Mensajes informativos de inicialización

## 🚀 Uso

### Iniciar MaxiBot v4.6.2

```bash
cd "d:\zyzen 3\Documents\Ecosistema-Maxi\Maxibot"
& "d:/zyzen 3/Documents/Ecosistema-Maxi/.venv/Scripts/python.exe" "MaxiBot_V4.6.2_DevOpsMCP.py"
```

### Acceder a Operaciones

1. **Login con SSO** (Keycloak)
2. **Ingresar API Key** de Gemini
3. **Hacer clic** en el botón "🔧 Operaciones"
4. **Consultar** información de DevOps

### Ejemplos de Consultas

```
Dame el status de la agencia NM-238
¿Por qué está deshabilitada la agencia NM-150?
Muéstrame el estado de los servicios en producción
```

## 📦 Dependencias Nuevas

```
google-genai>=0.2.0
mcp>=1.0.0
```

**Instalar**:
```bash
pip install -r requirements.txt
```

## 🔑 Configuración

### Variables de Entorno

El sistema configura automáticamente:
- `KEYCLOAK_TOKEN`: Token de autenticación SSO
- `GEMINI_API_KEY`: API key ingresada por el usuario

### Configuración DevOps MCP

- **URL**: `https://mcp.mylabs.mx/tools/operations/mcp/`
- **Modelo**: `gemini-2.5-flash`
- **Temperatura**: 0 (determinístico)

## 📊 Arquitectura

```
MaxiBot v4.6.2
├── Chat Principal (gemini-2.5-flash)
│   ├── Excel/KB
│   ├── DOCS
│   ├── WEATHER
│   ├── NEWS
│   ├── MCP
│   └── WEB
│
└── Pestaña Operaciones (DevOps MCP)
    └── DevOps MCP (gemini-2.5-flash)
        ├── Autenticación Keycloak
        ├── Consultas directas
        └── Sin cascada de búsqueda
```

## 🆚 Diferencias con v4.6.1

| Característica | v4.6.1 | v4.6.2 DevOpsMCP |
|----------------|--------|------------------|
| Chat Principal | ✅ | ✅ |
| Keycloak SSO | ✅ | ✅ |
| Modelo Gemini | gemini-2.5-flash | gemini-2.5-flash |
| **Pestaña Operaciones** | ❌ | ✅ |
| **DevOps MCP** | ❌ | ✅ |
| **Indicador Estado MCP** | ❌ | ✅ |

## 🔒 Seguridad

- ✅ Autenticación SSO con Keycloak
- ✅ Tokens no persistidos en archivos
- ✅ API keys solo en memoria
- ✅ Validación de roles de usuario

## 📝 Notas para Desarrollo

### Evitar Conflictos

Esta versión (`v4.6.2`) fue creada para evitar conflictos con otros desarrolladores trabajando en `v4.6.1`. 

**Recomendaciones**:
- Usar `MaxiBot_V4.6.2_DevOpsMCP.py` para desarrollo con DevOps MCP
- Mantener `MaxiBot_V4.6.1_Keycloack.py` para desarrollo base
- Sincronizar cambios mediante Git branches

### Archivos Relacionados

- `devops_mcp.py` - Cliente DevOps MCP
- `keycloak_auth.py` - Autenticación Keycloak
- `requirements.txt` - Dependencias
- `operaciones_tab.py` - Código de referencia (no usado directamente)

## 🐛 Troubleshooting

### Error: "DevOps MCP no está conectado"

**Causa**: Falta API key de Gemini o token de Keycloak

**Solución**:
1. Asegúrate de hacer login con SSO
2. Ingresa tu API key de Gemini
3. Verifica el mensaje: "✅ DevOps MCP reinicializado con API Key"

### Error: "Model not found"

**Causa**: Modelo incorrecto en configuración

**Solución**: Verificar que `devops_mcp.py` use `gemini-2.5-flash`

## 📚 Documentación Adicional

- [Plan de Implementación](devops_mcp_plan.md)
- [Walkthrough DevOps MCP](devops_mcp_walkthrough.md)
- [Verificación de Modelos](gemini_model_verification.md)

## 👥 Créditos

**Versión**: 4.6.2 DevOpsMCP  
**Fecha**: 2025-12-10  
**Cambios**: Integración DevOps MCP + Pestaña Operaciones

---

**¿Preguntas?** Revisa la documentación en los artifacts o consulta los logs de consola.
