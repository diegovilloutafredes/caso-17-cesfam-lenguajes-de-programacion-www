#!/usr/bin/env bash
# CESFAM — despliega el backend a la nube (Railway) desde local, sin push a GitHub.
# Requiere 'railway login' (la sesión vive en ~/.railway, fuera del repo). No hay
# secretos en el repo: las claves (Postgres, etc.) son variables del servicio en Railway.
set -euo pipefail

GREEN='\033[0;32m'; CYAN='\033[0;36m'; RED='\033[0;31m'; NC='\033[0m'
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR/backend-microservices"
SERVICE="${RAILWAY_SERVICE:-cesfam-backend}"

command -v railway >/dev/null 2>&1 || { echo -e "${RED}Falta la CLI de Railway: npm i -g @railway/cli${NC}"; exit 1; }
railway whoami >/dev/null 2>&1 || { echo -e "${RED}Inicia sesión primero: railway login${NC}"; exit 1; }

echo -e "${CYAN}▶ Desplegando '$SERVICE' a Railway (sube el código local)...${NC}"
railway up --service "$SERVICE" --ci

echo -e "${CYAN}▶ Estado del despliegue:${NC}"
railway status
echo -e "${GREEN}Listo.${NC}"
