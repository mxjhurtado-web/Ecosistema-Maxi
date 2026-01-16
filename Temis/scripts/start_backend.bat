@echo off
REM TEMIS Backend Starter Script
echo ========================================
echo Starting TEMIS Backend Server
echo ========================================
echo.

cd /d "%~dp0"
set PYTHONPATH=%CD%

echo Backend directory: %CD%\backend
echo PYTHONPATH: %PYTHONPATH%
echo.

python backend\main.py

pause
