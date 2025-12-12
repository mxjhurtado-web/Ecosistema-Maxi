@echo off
REM Start ATHENAS Web Backend
echo Starting ATHENAS Web Backend...

cd /d "%~dp0"

REM Set PYTHONPATH to include backend and athenas_lite
set PYTHONPATH=%CD%;%CD%\..\..\athenas_lite;%PYTHONPATH%

REM Start uvicorn
python -m uvicorn main:app --reload --port 8000 --host 0.0.0.0

pause
