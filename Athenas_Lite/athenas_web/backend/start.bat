@echo off
REM ========================================
REM ATHENAS Web - Backend Startup Script
REM ========================================

echo.
echo ========================================
echo   ATHENAS Web Backend
echo ========================================
echo.

REM Get the directory where this script is located
cd /d "%~dp0"

REM Configure PYTHONPATH to include backend and athenas_lite
set "BACKEND_DIR=%CD%"
set "ATHENAS_LITE_DIR=%CD%\..\..\athenas_lite"
set "PYTHONPATH=%BACKEND_DIR%;%ATHENAS_LITE_DIR%;%PYTHONPATH%"

echo [INFO] Backend directory: %BACKEND_DIR%
echo [INFO] ATHENAS Lite directory: %ATHENAS_LITE_DIR%
echo [INFO] PYTHONPATH configured
echo.

REM Start uvicorn
echo [INFO] Starting uvicorn on port 8000...
echo.

python -m uvicorn main:app --reload --port 8000 --host 0.0.0.0

REM If uvicorn exits, pause to see any error messages
if errorlevel 1 (
    echo.
    echo [ERROR] Backend failed to start!
    echo.
    pause
)
