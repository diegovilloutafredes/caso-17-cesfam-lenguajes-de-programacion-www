@echo off
REM Instalacion SIN Docker en Windows. Pre-requisito: Python 3.11+ con "Add to PATH".

cd /d "%~dp0"

echo === Verificando Python ===
where python >nul 2>nul
if errorlevel 1 (
    echo Python no esta en PATH. Instalar desde https://www.python.org/downloads/ marcando "Add to PATH".
    exit /b 1
)
python --version
echo.

echo === Creando virtual environment ===
if exist .venv (
    echo .venv ya existe - reusando
) else (
    python -m venv .venv
)

echo.
echo === Instalando dependencias ===
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
echo OK dependencias instaladas

echo.
echo OK Instalacion local completa. Arranca con: run-local.bat
