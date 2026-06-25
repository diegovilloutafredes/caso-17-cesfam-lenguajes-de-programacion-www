#!/usr/bin/env bash
# CESFAM — detiene el stack local (docker + frontend) y libera puertos.
set -uo pipefail

GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"
COMPOSE="docker compose -f backend-microservices/docker-compose.yml"

if docker info >/dev/null 2>&1; then
  echo -e "${CYAN}Bajando el backend (docker)...${NC}"
  $COMPOSE down >/dev/null 2>&1 || true
fi

# Frontend nativo (Vite) en :5173.
pids="$(lsof -ti tcp:5173 2>/dev/null || true)"
if [ -n "$pids" ]; then
  echo -e "${CYAN}Deteniendo el frontend (:5173)...${NC}"
  echo "$pids" | xargs kill 2>/dev/null || true
fi

echo -e "${GREEN}Listo. Stack local detenido.${NC}"
