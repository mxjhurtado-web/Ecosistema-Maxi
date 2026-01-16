@echo off
REM TEMIS Desktop Starter Script
echo ========================================
echo Starting TEMIS Desktop Application
echo ========================================
echo.

cd /d "%~dp0"
set PYTHONPATH=%CD%

echo Desktop directory: %CD%\desktop
echo PYTHONPATH: %PYTHONPATH%
echo.

python desktop\main.py

pause
