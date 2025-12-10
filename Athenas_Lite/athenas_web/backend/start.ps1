# ========================================
# ATHENAS Web - Backend Startup Script
# ========================================

Write-Host ""
Write-Host "========================================"  -ForegroundColor Cyan
Write-Host "   ATHENAS Web Backend" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$BackendDir = $PSScriptRoot
$AthenasliteDir = Join-Path $BackendDir "..\..\athenas_lite" | Resolve-Path

# Configure PYTHONPATH
$env:PYTHONPATH = "$BackendDir;$AthenasliteDir"

Write-Host "[INFO] Backend directory: $BackendDir" -ForegroundColor Green
Write-Host "[INFO] ATHENAS Lite directory: $AthenasliteDir" -ForegroundColor Green
Write-Host "[INFO] PYTHONPATH configured" -ForegroundColor Green
Write-Host ""
Write-Host "[INFO] Starting uvicorn on port 8000..." -ForegroundColor Yellow
Write-Host ""

# Start uvicorn
python -m uvicorn main:app --reload --port 8000 --host 0.0.0.0

# If uvicorn exits with error
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Backend failed to start!" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
}
