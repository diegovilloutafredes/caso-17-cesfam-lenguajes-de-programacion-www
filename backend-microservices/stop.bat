@echo off
REM Detiene los containers del sandbox.

cd /d "%~dp0"

docker compose down
echo OK Sandbox detenido.
