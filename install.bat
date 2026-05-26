@echo off
 
setlocal enabledelayedexpansion

cd /d "%~dp0"

 
where python >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found on PATH.
    echo Install Python 3.11 or 3.12 from https://www.python.org/downloads/
    echo During install, check "Add Python to PATH".
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PY_VERSION=%%i
echo Using !PY_VERSION!

if exist ".venv" (
    echo Virtual environment .venv already exists; reusing it.
) else (
    echo Creating virtual environment in .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        exit /b 1
    )
)

call .venv\Scripts\activate.bat

echo Upgrading pip ...
python -m pip install --upgrade pip --quiet

echo Installing dependencies from requirements.txt ...
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo Failed to install dependencies.
    exit /b 1
)

echo.
echo Install complete. Start the server with:  run.bat
endlocal
