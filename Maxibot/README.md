# MaxiBot V4.6.1

Asistente inteligente con integración SSO Keycloak y Google APIs.

## 📋 Requisitos

- **Python 3.13.1** (requerido)
- **pyenv** (recomendado para gestionar versiones de Python)
- **Tkinter** (incluido en Python del sistema)

## 🚀 Inicio Rápido

### Opción 1: Usar el script de inicio (Recomendado)

```bash
chmod +x start.sh
./start.sh
```

El script automáticamente:
- Verifica la versión de Python
- Crea el entorno virtual si no existe
- Instala las dependencias
- Muestra la configuración de Keycloak
- Inicia MaxiBot

### Opción 2: Instalación Manual

```bash
# 1. Configurar Python 3.13.1 con pyenv
pyenv install 3.13.1
pyenv local 3.13.1

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# 4. Ejecutar
python MaxiBot_V4.6.1_mcp.py
```

## ⚙️ Configuración

### Keycloak SSO

Edita `keycloak_config.py` o usa variables de entorno:

```bash
export KEYCLOAK_URL="https://sso.maxilabs.net/auth"
export KEYCLOAK_REALM="zeusDev"
export KEYCLOAK_CLIENT_ID="maxi-business-ai"
export KEYCLOAK_CLIENT_SECRET="tu-client-secret"
export KEYCLOAK_REDIRECT_URI="http://localhost:8080/callback"
```

**Valores por defecto** (en `keycloak_config.py`):
- URL: `https://sso.maxilabs.net/auth`
- Realm: `zeusDev`
- Client ID: `maxi-business-ai`
- Callback: `http://localhost:8080/callback`

### API Key de Gemini

```bash
export GEMINI_API_KEY="tu-api-key"
```

O edita `MaxiBot_V4.6.1_mcp.py` línea 90.

## 📦 Dependencias Principales

- `requests` - Peticiones HTTP
- `pandas` - Manejo de datos
- `google-api-python-client` - Google APIs
- `PyJWT` - Autenticación Keycloak
- `tkinter` - Interfaz gráfica (incluido en Python)

Ver `requirements.txt` para la lista completa.

## 🔧 Solución de Problemas

### Error: "Python version incorrecta"

Asegúrate de tener Python 3.13.1 instalado:
```bash
pyenv install 3.13.1
pyenv local 3.13.1
python --version  # Debe mostrar 3.13.1
```

### Error: "No module named '_tkinter'"

Usa Python del sistema o instala Tkinter:
```bash
# macOS
brew install python-tk

# O usa Python del sistema
/usr/bin/python3 -m venv venv
```

### Puerto 8080 en uso

Cambia el puerto en `keycloak_config.py`:
```python
APP_PORT = 8081  # o cualquier puerto libre
```

## 📁 Estructura del Proyecto

```
Maxibot_Operaciones/
├── MaxiBot_V4.6.1_mcp.py    # Aplicación principal
├── keycloak_config.py        # Configuración Keycloak
├── keycloak_auth.py          # Lógica SSO
├── requirements.txt          # Dependencias
├── start.sh                  # Script de inicio
└── README.md                 # Este archivo
```

## 📚 Documentación Adicional

- `KEYCLOAK_SSO_README.md` - Guía completa de SSO
- `QUICKSTART.md` - Guía rápida de inicio

## ✅ Checklist Pre-Ejecución

- [ ] Python 3.13.1 instalado y configurado
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Keycloak configurado (o usar autenticación manual)
- [ ] API Key de Gemini configurada
- [ ] Puerto 8080 libre (para callback de Keycloak)

---

**Versión:** 4.6.1  
**Python:** 3.13.1 (requerido)

