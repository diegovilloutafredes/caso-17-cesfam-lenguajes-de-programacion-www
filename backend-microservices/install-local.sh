#!/usr/bin/env bash
# Instalación SIN Docker — usa Python venv local.
# Pre-requisito: Python 3.11+ (no 3.13 por hashlib issues).
# Cuando termine, ejecutá ./run-local.sh para arrancar los 7 servicios.

set -e
cd "$(dirname "$0")"

echo "=== Verificando Python ==="
if ! command -v python3 >/dev/null 2>&1; then
    echo "✗ Python 3 no está instalado."
    echo "  macOS: brew install python@3.12"
    echo "  Linux: sudo apt install python3 python3-venv"
    echo "  Otro: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Python $PYTHON_VERSION encontrado"

if [ "$PYTHON_VERSION" = "3.13" ]; then
    echo "⚠ Python 3.13 tiene regresiones en hashlib que generan warnings ruidosos."
    echo "  El sandbox funciona igual, pero verás errores en stderr. Continuamos..."
fi

echo
echo "=== Creando virtual environment ==="
if [ -d ".venv" ]; then
    echo "✓ .venv ya existe — reusando"
else
    python3 -m venv .venv
    echo "✓ .venv creado"
fi

echo
echo "=== Instalando dependencias ==="
source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "✓ Dependencias instaladas"

echo
echo "✓ Instalación local completa. Arrancá los 7 servicios con: ./run-local.sh"
