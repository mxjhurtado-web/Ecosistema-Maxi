@echo off
echo Starting ATHENAS Lite Web Application...
echo.

REM Start callback server on port 8080
echo [1/3] Starting OAuth callback server (port 8080)...
start "ATHENAS Callback Server" cmd /k "cd backend && venv\Scripts\activate && python callback_server.py"
timeout /t 3 /nobreak > nul

REM Start main backend on port 8000
echo [2/3] Starting main backend (port 8000)...
start "ATHENAS Backend" cmd /k "cd backend && venv\Scripts\activate && python main.py"
timeout /t 3 /nobreak > nul

REM Start frontend on port 3000
echo [3/3] Starting frontend (port 3000)...
start "ATHENAS Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo ATHENAS Lite is starting...
echo ========================================
echo.
echo Callback Server: http://localhost:8080
echo Backend API:     http://localhost:8000
echo Frontend:        http://localhost:3000
echo.
echo Press any key to stop all servers...
pause > nul

REM Kill all servers
taskkill /FI "WindowTitle eq ATHENAS*" /T /F
