#!/usr/bin/env bash
# CESFAM — levanta el stack local completo (backend microservicios + frontend) en una
# sola terminal. Ctrl+C detiene todo.
set -e

GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"
COMPOSE="docker compose -f backend-microservices/docker-compose.yml"

docker info >/dev/null 2>&1 || { echo -e "${RED}✗ Docker no está corriendo. Abre Docker Desktop.${NC}"; exit 1; }

cleanup() {
  echo ""
  echo -e "${YELLOW}Deteniendo el stack...${NC}"
  $COMPOSE down >/dev/null 2>&1 || true
  echo -e "${GREEN}Detenido.${NC}"
}
trap cleanup EXIT INT TERM

echo -e "${CYAN}▶ Backend: 7 servicios + Postgres (docker compose)...${NC}"
$COMPOSE up -d --build

echo -e "${CYAN}▶ Esperando al gateway (:8000)...${NC}"
curl -s -m 90 --retry 60 --retry-delay 1 --retry-all-errors http://localhost:8000/health >/dev/null \
  && echo -e "${GREEN}✓ Backend listo${NC}" || { echo -e "${RED}✗ El backend no respondió${NC}"; exit 1; }

[ -d frontend/node_modules ] || { echo -e "${CYAN}▶ Instalando dependencias del frontend...${NC}"; npm --prefix frontend install; }

echo ""
echo -e "${GREEN}=== CESFAM corriendo ===${NC}"
echo "  App:     http://localhost:5173"
echo "  API/BFF: http://localhost:8000/health"
echo "  Login:   drperez (médico) · mgonzalez (farmacia)"
echo ""
echo -e "${YELLOW}Ctrl+C para detener todo${NC}"
echo ""
VITE_API_URL=http://localhost:8000 npm --prefix frontend run dev
