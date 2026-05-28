@echo off
REM Arranca los 7 servicios en background con docker-compose.

cd /d "%~dp0"

docker info >nul 2>nul
if errorlevel 1 (
    echo Docker daemon no responde. Abri Docker Desktop primero.
    exit /b 1
)

echo === Iniciando 7 servicios ===
docker compose up -d
if errorlevel 1 exit /b 1

echo.
echo Esperando que todos los servicios esten healthy (~15s)...
timeout /t 15 /nobreak >nul

docker compose ps

echo.
echo OK Sandbox arriba.
echo.
echo Documentacion Swagger UI:
echo   ApiGateway:    http://localhost:8000/docs  ^(entrypoint del frontend^)
echo   Identity:      http://localhost:8001/docs
echo   Patient:       http://localhost:8002/docs
echo   Inventory:     http://localhost:8003/docs
echo   Prescription:  http://localhost:8004/docs
echo   Notification:  http://localhost:8005/docs
echo   Report:        http://localhost:8006/docs
echo.
echo Detener:             stop.bat
echo Ver logs:            docker compose logs -f ^<servicio^>
