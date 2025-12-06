#!/bin/bash
# Script de inicio para MaxiBot con SSO Keycloak

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== MaxiBot V4.6.1 con SSO Keycloak ===${NC}"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "MaxiBot_V4.6.1_Keycloack.py" ]; then
    echo -e "${RED}Error: MaxiBot_V4.6.1_Keycloack.py no encontrado${NC}"
    echo "Ejecuta este script desde el directorio del proyecto"
    exit 1
fi

# Verificar versión de Python (debe ser 3.13.1)
REQUIRED_VERSION="3.13.1"
if [ -f ".python-version" ]; then
    CURRENT_VERSION=$(cat .python-version)
    if [ "$CURRENT_VERSION" != "$REQUIRED_VERSION" ]; then
        echo -e "${YELLOW}⚠️  Versión de Python incorrecta: $CURRENT_VERSION${NC}"
        echo -e "${YELLOW}    Configurando Python $REQUIRED_VERSION...${NC}"
        echo "$REQUIRED_VERSION" > .python-version
    fi
else
    echo "$REQUIRED_VERSION" > .python-version
fi

# Mostrar versión de Python
echo -e "${BLUE}Python: $(python --version)${NC}"

# Verificar que existe el venv
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment no encontrado. Creando...${NC}"
    python -m venv venv
    echo -e "${GREEN}✅ Virtual environment creado${NC}"
fi

# Activar venv
echo -e "${YELLOW}Activando virtual environment...${NC}"
source venv/bin/activate

# Verificar dependencias
echo -e "${YELLOW}Verificando dependencias...${NC}"
python -c "import tkinter, keycloak_auth, keycloak_config, pandas, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Instalando dependencias...${NC}"
    pip install -q -r requirements.txt
    echo -e "${GREEN}✅ Dependencias instaladas${NC}"
else
    echo -e "${GREEN}✅ Todas las dependencias están instaladas${NC}"
fi

# Mostrar configuración de Keycloak
echo ""
echo -e "${GREEN}Configuración Keycloak:${NC}"
python -c "import keycloak_config as kc; print(f'  • URL: {kc.KEYCLOAK_URL}'); print(f'  • Realm: {kc.REALM}'); print(f'  • Client ID: {kc.CLIENT_ID}'); print(f'  • Callback: {kc.REDIRECT_URI}')"
echo ""

# Iniciar MaxiBot
echo -e "${GREEN}🚀 Iniciando MaxiBot...${NC}"
echo ""
python MaxiBot_V4.6.1_Keycloack.py
