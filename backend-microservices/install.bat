@echo off
REM Instala el sandbox usando Docker.
REM Pre-requisito: Docker Desktop instalado y corriendo.

cd /d "%~dp0"

echo === Verificando Docker ===
where docker >nul 2>nul
if errorlevel 1 (
    echo Docker no esta instalado. Instalalo desde https://www.docker.com/products/docker-desktop
    exit /b 1
)
docker info >nul 2>nul
if errorlevel 1 (
    echo Docker daemon no responde. Abri Docker Desktop y espera al icono verde.
    exit /b 1
)
echo OK Docker activo
echo.

echo === Build de las 7 imagenes (toma ~2 min primera vez) ===
docker compose build
if errorlevel 1 (
    echo Error en el build.
    exit /b 1
)

echo.
echo OK Instalacion completa. Para arrancar el sandbox: run.bat
