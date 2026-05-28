@echo off
REM Mata los procesos uvicorn que ocupan los puertos del sandbox.

cd /d "%~dp0"

echo Buscando y deteniendo procesos uvicorn en puertos 8000-8006...

for %%p in (8000 8001 8002 8003 8004 8005 8006) do (
    for /f "tokens=5" %%i in ('netstat -aon ^| findstr ":%%p " ^| findstr "LISTENING"') do (
        taskkill /PID %%i /F >nul 2>nul
        if not errorlevel 1 echo  OK puerto %%p liberado ^(PID %%i^)
    )
)

echo.
echo OK Sandbox local detenido.
