@echo off
 
setlocal

cd /d "%~dp0"

set PORT=%1
if "%PORT%"=="" set PORT=8000

if not exist ".venv" (
    echo Error: virtual environment not found. Run install.bat first.
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Starting sandbox on http://localhost:%PORT%
echo   Swagger UI:  http://localhost:%PORT%/docs
echo   ReDoc:       http://localhost:%PORT%/redoc
echo   OpenAPI:     http://localhost:%PORT%/openapi.json
echo.
echo Press Ctrl+C to stop.
echo.

uvicorn main:app --port %PORT% --reload
endlocal
