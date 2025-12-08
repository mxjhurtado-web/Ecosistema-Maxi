@echo off
echo Deteniendo servidores existentes...

:: Matar procesos en puertos específicos
for /f "tokens=5" %%a in ('netstat -aon ^| find ":3000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8080" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo Esperando a que se liberen los puertos...
timeout /t 3 /nobreak >nul

echo Iniciando servidores...

:: Iniciar Callback Server (8080)
start "Callback Server" cmd /k "cd backend && .\venv\Scripts\activate && python callback_server.py"

:: Iniciar Backend API (8000)
start "Backend API" cmd /k "cd backend && .\venv\Scripts\activate && python main.py"

:: Iniciar Frontend (3000)
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ===================================================
echo   ATHENAS Lite Web - Servidores Reiniciados
echo ===================================================
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo Callback: http://localhost:8080
echo.
echo Por favor espera unos segundos a que Next.js compile...
pause
