@echo off
REM Arranca los 7 servicios LOCALMENTE en Windows (sin Docker).
REM Cada servicio en una ventana separada de cmd. Cerrar cada ventana o usar stop-local.bat.

cd /d "%~dp0"

if not exist .venv (
    echo .venv no existe. Corre install-local.bat primero.
    exit /b 1
)

REM Env vars para que los clients sepan donde encontrar a los otros servicios
set IDENTITY_SERVICE_URL=http://localhost:8001
set PATIENT_SERVICE_URL=http://localhost:8002
set INVENTORY_SERVICE_URL=http://localhost:8003
set PRESCRIPTION_SERVICE_URL=http://localhost:8004
set NOTIFICATION_SERVICE_URL=http://localhost:8005

echo Arrancando 7 servicios en ventanas separadas...

start "identity_service:8001" cmd /k ".venv\Scripts\activate.bat && uvicorn identity_service.main:app --port 8001"
timeout /t 1 /nobreak >nul
start "patient_service:8002" cmd /k ".venv\Scripts\activate.bat && uvicorn patient_service.main:app --port 8002"
timeout /t 1 /nobreak >nul
start "inventory_service:8003" cmd /k ".venv\Scripts\activate.bat && uvicorn inventory_service.main:app --port 8003"
timeout /t 1 /nobreak >nul
start "notification_service:8005" cmd /k ".venv\Scripts\activate.bat && uvicorn notification_service.main:app --port 8005"
timeout /t 1 /nobreak >nul
start "prescription_service:8004" cmd /k ".venv\Scripts\activate.bat && uvicorn prescription_service.main:app --port 8004"
timeout /t 1 /nobreak >nul
start "report_service:8006" cmd /k ".venv\Scripts\activate.bat && uvicorn report_service.main:app --port 8006"
timeout /t 1 /nobreak >nul
start "api_gateway:8000" cmd /k ".venv\Scripts\activate.bat && uvicorn api_gateway.main:app --port 8000"

echo.
echo OK Sandbox local arriba (7 ventanas de cmd, una por servicio).
echo.
echo Gateway: http://localhost:8000/docs
echo.
echo Para detener: cerrar cada ventana manualmente, o ejecutar stop-local.bat
