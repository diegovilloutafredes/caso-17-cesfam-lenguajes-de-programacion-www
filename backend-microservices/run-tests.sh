#!/usr/bin/env bash
# Corre la suite de tests de integración cross-service contra el sistema levantado.
# Requiere los servicios arriba:  docker compose up -d --build
# Los tests corren en un contenedor python:3.12 sobre la red del compose, entrando
# por el ApiGateway (api_gateway:8000).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
NET="$(docker network ls --format '{{.Name}}' | grep -E 'backend-microservices.*default' | head -1)"
NET="${NET:-backend-microservices_default}"
docker run --rm --network "$NET" \
  -v "$HERE/tests:/tests:ro" -w /tests \
  -e GATEWAY_URL=http://api_gateway:8000 \
  python:3.12-slim sh -c "pip install -q pytest httpx && python -m pytest -q"
