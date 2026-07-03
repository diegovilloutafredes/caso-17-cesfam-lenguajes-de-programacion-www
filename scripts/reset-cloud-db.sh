#!/usr/bin/env bash
# CESFAM — resetea el Postgres de la nube (Railway) para volver a aplicar el seed.
#
# Destructivo: borra todos los datos del backend en la nube. El seed solo corre con las
# tablas vacías, así que esto es necesario cuando cambian los datos del seed. Tras correrlo,
# redesplegar (./scripts/deploy-backend.sh) recrea las 5 bases y las vuelve a sembrar.
#
# La clave del Postgres no se imprime ni se versiona: se lee de la conexión pública del
# servicio (DATABASE_PUBLIC_URL) y se pasa al contenedor por variable de entorno.
set -euo pipefail

CYAN='\033[0;36m'; RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
PG_SERVICE="${RAILWAY_PG_SERVICE:-Postgres}"

# el link de Railway vive en backend-microservices; desde otra ruta la CLI no resuelve el proyecto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR/backend-microservices"

command -v railway >/dev/null 2>&1 || { echo -e "${RED}Falta la CLI de Railway: npm i -g @railway/cli${NC}"; exit 1; }
command -v docker  >/dev/null 2>&1 || { echo -e "${RED}Falta Docker (se usa para conectarse a Postgres).${NC}"; exit 1; }
railway whoami >/dev/null 2>&1 || { echo -e "${RED}Inicia sesión primero: railway login${NC}"; exit 1; }

echo -e "${YELLOW}Esto BORRA todos los datos del backend en la nube (las 5 bases).${NC}"
read -r -p "Escribe 'reset' para continuar: " ans
[ "$ans" = "reset" ] || { echo "Cancelado."; exit 0; }

echo -e "${CYAN}▶ Obteniendo la conexión pública de Postgres...${NC}"
# la CLI puede anteponer avisos (p. ej. de actualización) al JSON; se recortan
PUBURL="$(railway variables -s "$PG_SERVICE" --json | sed -n '/^{/,$p' | python3 -c 'import sys,json;print(json.load(sys.stdin).get("DATABASE_PUBLIC_URL",""))')"
[ -n "$PUBURL" ] || { echo -e "${RED}No se obtuvo DATABASE_PUBLIC_URL del servicio '$PG_SERVICE'.${NC}"; exit 1; }

PYTMP="$(mktemp)"; trap 'rm -f "$PYTMP"' EXIT
cat > "$PYTMP" <<'PYEOF'
import os, psycopg2
con = psycopg2.connect(os.environ["DBURL"])
con.autocommit = True
cur = con.cursor()
for db in ["identity_db", "patient_db", "inventory_db", "prescription_db", "notification_db"]:
    cur.execute('DROP DATABASE IF EXISTS "%s" WITH (FORCE)' % db)
    print("  dropped", db)
con.close()
PYEOF

echo -e "${CYAN}▶ Borrando las 5 bases...${NC}"
docker run --rm -e DBURL="$PUBURL" -v "$PYTMP":/drop.py:ro python:3.12-slim \
  sh -c "pip install -q psycopg2-binary && python /drop.py"

echo -e "${GREEN}Bases borradas. Ahora redespliega para recrearlas y sembrarlas:${NC}"
echo "  ./scripts/deploy-backend.sh"
