#!/usr/bin/env bash
# Arranque en Railway: los 7 procesos uvicorn en un contenedor, solo el gateway
# es público. Requiere bash (wait -n no existe en sh/dash).
set -eu

: "${PGHOST:?falta PGHOST (referencia a la base Postgres de Railway)}"
: "${PGUSER:?falta PGUSER}"
: "${PGPASSWORD:?falta PGPASSWORD}"
PGPORT="${PGPORT:-5432}"
PGBASE="postgresql+psycopg2://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}"

# espera Postgres y crea las bases que falten (Railway trae una sola)
python - <<'PY'
import os, time, psycopg2
dsn = dict(host=os.environ["PGHOST"], port=int(os.environ.get("PGPORT", "5432")),
           user=os.environ["PGUSER"], password=os.environ["PGPASSWORD"],
           dbname=os.environ.get("PGDATABASE", "railway"))
con = None
for _ in range(30):
    try:
        con = psycopg2.connect(**dsn)
        break
    except Exception as e:
        print("esperando Postgres...", e); time.sleep(2)
if con is None:
    raise SystemExit("Postgres no respondió")
con.autocommit = True
cur = con.cursor()
for db in ("identity_db", "patient_db", "inventory_db", "prescription_db", "notification_db"):
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db,))
    if not cur.fetchone():
        cur.execute('CREATE DATABASE "%s"' % db)
        print("base creada:", db)
con.close()
PY

# todos los servicios viven en localhost dentro del contenedor
export IDENTITY_SERVICE_URL="http://127.0.0.1:8001"
export PATIENT_SERVICE_URL="http://127.0.0.1:8002"
export INVENTORY_SERVICE_URL="http://127.0.0.1:8003"
export PRESCRIPTION_SERVICE_URL="http://127.0.0.1:8004"
export NOTIFICATION_SERVICE_URL="http://127.0.0.1:8005"
export REPORT_SERVICE_URL="http://127.0.0.1:8006"

# propaga el apagado a los hijos
trap 'kill 0' INT TERM

# cada servicio con su propia base; solo el gateway es público
DATABASE_URL="${PGBASE}/identity_db"     uvicorn identity_service.main:app     --host 127.0.0.1 --port 8001 &
DATABASE_URL="${PGBASE}/patient_db"      uvicorn patient_service.main:app      --host 127.0.0.1 --port 8002 &
DATABASE_URL="${PGBASE}/inventory_db"    uvicorn inventory_service.main:app    --host 127.0.0.1 --port 8003 &
DATABASE_URL="${PGBASE}/prescription_db" uvicorn prescription_service.main:app --host 127.0.0.1 --port 8004 &
DATABASE_URL="${PGBASE}/notification_db" uvicorn notification_service.main:app --host 127.0.0.1 --port 8005 &
uvicorn report_service.main:app --host 127.0.0.1 --port 8006 &
uvicorn api_gateway.main:app --host 0.0.0.0 --port "${PORT:-8000}" &

# si un proceso muere, el script sale con error y Railway reinicia el contenedor
wait -n || true
exit 1
