#!/usr/bin/env bash
 
set -euo pipefail

cd "$(dirname "$0")"

PORT="${1:-8000}"

if [ ! -d ".venv" ]; then
  echo "Error: virtual environment not found. Run ./install.sh first."
  exit 1
fi

source .venv/bin/activate

echo "Starting sandbox on http://localhost:${PORT}"
echo "  Swagger UI:  http://localhost:${PORT}/docs"
echo "  ReDoc:       http://localhost:${PORT}/redoc"
echo "  OpenAPI:     http://localhost:${PORT}/openapi.json"
echo ""
echo "Press Ctrl+C to stop."
echo ""

exec uvicorn main:app --port "$PORT" --reload
