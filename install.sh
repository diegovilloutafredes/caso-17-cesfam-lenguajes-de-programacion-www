#!/usr/bin/env bash
 
set -euo pipefail

cd "$(dirname "$0")"

 
PY="python3"
if ! command -v "$PY" >/dev/null 2>&1; then
  PY="python"
  if ! command -v "$PY" >/dev/null 2>&1; then
    echo "Error: Python not found. Install Python 3.11 or 3.12 from https://www.python.org/downloads/"
    exit 1
  fi
fi

PY_VERSION=$("$PY" --version 2>&1)
echo "Using $PY_VERSION"

if [ -d ".venv" ]; then
  echo "Virtual environment .venv already exists; reusing it."
else
  echo "Creating virtual environment in .venv ..."
  "$PY" -m venv .venv
fi

source .venv/bin/activate

echo "Upgrading pip ..."
pip install --upgrade pip --quiet

echo "Installing dependencies from requirements.txt ..."
pip install -r requirements.txt --quiet

echo ""
echo "Install complete. Start the server with:  ./run.sh"
