#!/usr/bin/env bash
# CESFAM — despliega el frontend a la nube (Vercel) desde local. Publica el deploy
# principal (URL estable). Requiere 'vercel login' (la sesión vive en ~/.vercel, fuera del repo).
# Sin secretos en el repo: la URL del backend se pasa como build-env.
set -euo pipefail

GREEN='\033[0;32m'; CYAN='\033[0;36m'; RED='\033[0;31m'; NC='\033[0m'
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR/frontend"

API_URL="${VITE_API_URL:-}"
if [ -z "$API_URL" ]; then
  echo -e "${RED}Define VITE_API_URL con la URL del backend en Railway. Ej:${NC}"
  echo "  VITE_API_URL=https://<tu-backend>.up.railway.app ./scripts/deploy-frontend.sh"
  exit 1
fi
command -v vercel >/dev/null 2>&1 || { echo -e "${RED}Falta la CLI de Vercel: npm i -g vercel${NC}"; exit 1; }
vercel whoami >/dev/null 2>&1 || { echo -e "${RED}Inicia sesión primero: vercel login${NC}"; exit 1; }

echo -e "${CYAN}▶ Desplegando frontend a Vercel (URL estable), API=$API_URL ...${NC}"
vercel deploy --prod --yes --build-env VITE_API_URL="$API_URL"
echo -e "${GREEN}Listo.${NC}"
