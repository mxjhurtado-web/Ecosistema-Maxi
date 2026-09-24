@echo off
chcp 65001 > nul
echo =========================================================
echo   TEMIS Media Studio — Generador de Ejecutable (.exe)
echo =========================================================

REM Verificar si ffmpeg.exe existe en resources, si no, copiar de Athenas
if not exist "resources\ffmpeg\ffmpeg.exe" (
    echo [INFO] Buscando binario local de FFmpeg...
    if exist "C:\Users\User\Downloads\Athenas1.2 py\Athenas1.2 py\resources\ffmpeg\ffmpeg.exe" (
        echo [INFO] Copiando FFmpeg desde carpeta de descargas de Athenas...
        mkdir "resources\ffmpeg" 2>nul
        copy "C:\Users\User\Downloads\Athenas1.2 py\Athenas1.2 py\resources\ffmpeg\ffmpeg.exe" "resources\ffmpeg\ffmpeg.exe" /y
    )
)

REM Verificar si los modelos de Whisper existen
if not exist "resources\models\base.pt" (
    if exist "C:\Users\User\Downloads\Athenas1.2 py\Athenas1.2 py\resources\base.pt" (
        echo [INFO] Copiando modelo Whisper base.pt...
        mkdir "resources\models" 2>nul
        copy "C:\Users\User\Downloads\Athenas1.2 py\Athenas1.2 py\resources\base.pt" "resources\models\base.pt" /y
    )
)

if not exist "resources\models\medium.pt" (
    if exist "C:\Users\User\Downloads\Athenas1.2 py\Athenas1.2 py\resources\medium.pt" (
        echo [INFO] Copiando modelo Whisper medium.pt...
        mkdir "resources\models" 2>nul
        copy "C:\Users\User\Downloads\Athenas1.2 py\Athenas1.2 py\resources\medium.pt" "resources\models\medium.pt" /y
    )
)

REM Verificar si pyinstaller está instalado
pyinstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Instalando PyInstaller...
    pip install pyinstaller
)

echo.
echo [INFO] Ejecutando compilación con PyInstaller...
pyinstaller --noconfirm temis_media_studio.spec

if %errorlevel% equ 0 (
    echo.
    echo =========================================================
    echo   [EXITO] Compilación completada.
    echo   Ejecutable generado en: dist\TEMIS_Media_Studio\TEMIS_Media_Studio.exe
    echo =========================================================
) else (
    echo.
    echo [ERROR] Ocurrió un fallo en la compilación.
)
pause
