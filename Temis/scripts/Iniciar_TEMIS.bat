@echo off
echo ========================================
echo   TEMIS - Sistema de Gestion Hibrido
echo ========================================
echo.

REM Verificar que los ejecutables existan
if not exist "TEMIS-Backend.exe" (
    echo [ERROR] No se encontro TEMIS-Backend.exe
    echo Por favor, construye el backend primero.
    pause
    exit /b 1
)

if not exist "TEMIS.exe" (
    echo [ERROR] No se encontro TEMIS.exe
    echo Por favor, construye el frontend primero.
    pause
    exit /b 1
)

echo [1/2] Iniciando backend...
start "" /MIN "TEMIS-Backend.exe"

REM Esperar 5 segundos para que el backend inicie
echo Esperando que el backend inicie...
timeout /t 5 /nobreak >nul

echo [2/2] Iniciando TEMIS...
start "" "TEMIS.exe"

echo.
echo ========================================
echo   TEMIS Iniciado Correctamente
echo ========================================
echo.
echo - Backend corriendo en segundo plano
echo - Frontend abierto
echo.
echo Para cerrar TEMIS:
echo 1. Cierra la ventana de TEMIS
echo 2. El backend se cerrara automaticamente
echo.
