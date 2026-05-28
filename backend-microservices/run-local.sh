#!/usr/bin/env bash
# Arranca los 7 servicios LOCALMENTE (sin Docker), cada uno como un proceso uvicorn en background.
# Los logs van a ./logs/, los PIDs a ./.pids/.
# Detener con ./stop-local.sh

set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "✗ .venv no existe. Corré ./install-local.sh primero."
    exit 1
fi

source .venv/bin/activate

# Verificar que los puertos estén libres
for port in 8000 8001 8002 8003 8004 8005 8006; do
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "✗ Puerto $port ya está en uso (PID $(lsof -ti:$port)). Liberalo antes de arrancar."
        exit 1
    fi
done

mkdir -p logs .pids

# Orden importa: leaf services primero (sin clientes inter-servicio), después orquestadores
SERVICES=(
    "identity_service:8001"
    "patient_service:8002"
    "inventory_service:8003"
    "notification_service:8005"
    "prescription_service:8004"
    "report_service:8006"
    "api_gateway:8000"
)

# Env vars: cuando corremos local, todos los servicios viven en localhost
export IDENTITY_SERVICE_URL="http://localhost:8001"
export PATIENT_SERVICE_URL="http://localhost:8002"
export INVENTORY_SERVICE_URL="http://localhost:8003"
export PRESCRIPTION_SERVICE_URL="http://localhost:8004"
export NOTIFICATION_SERVICE_URL="http://localhost:8005"

for entry in "${SERVICES[@]}"; do
    name="${entry%:*}"
    port="${entry#*:}"
    echo "Iniciando $name en puerto $port..."
    nohup uvicorn "${name}.main:app" --port "$port" > "logs/${name}.log" 2>&1 &
    echo $! > ".pids/${name}.pid"
    sleep 0.5
done

echo
echo "Esperando que arranquen (~5s)..."
sleep 5

# Health check rápido
echo
echo "=== Health checks ==="
for port in 8000 8001 8002 8003 8004 8005 8006; do
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port/health" 2>/dev/null | grep -q "200"; then
        echo "  ✓ puerto $port OK"
    else
        echo "  ✗ puerto $port no responde — ver logs/${name}.log"
    fi
done

cat <<EOF

✓ Sandbox local arriba (sin Docker).

Gateway: http://localhost:8000/docs
Logs:    ./logs/<servicio>.log
PIDs:    ./.pids/<servicio>.pid

Detener:     ./stop-local.sh
EOF
