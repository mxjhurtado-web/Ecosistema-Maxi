@echo off
echo ========================================
echo   TEMIS - Construccion de Ejecutable
echo ========================================
echo.

REM Verificar que PyInstaller este instalado
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [ERROR] PyInstaller no esta instalado
    echo Instalando PyInstaller...
    pip install pyinstaller
)

echo [1/3] Limpiando builds anteriores...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

echo [2/3] Construyendo ejecutable...
pyinstaller temis.spec

if errorlevel 1 (
    echo.
    echo [ERROR] Fallo la construccion
    pause
    exit /b 1
)

echo [3/3] Verificando ejecutable...
if exist "dist\TEMIS.exe" (
    echo.
    echo ========================================
    echo   EXITO! Ejecutable creado
    echo ========================================
    echo.
    echo Ubicacion: dist\TEMIS.exe
    echo Tamano: 
    dir "dist\TEMIS.exe" | find "TEMIS.exe"
    echo.
    echo Puedes copiar TEMIS.exe a cualquier computadora
    echo.
) else (
    echo [ERROR] No se encontro el ejecutable
)

pause
