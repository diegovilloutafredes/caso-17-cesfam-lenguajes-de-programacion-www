#!/usr/bin/env bash
# Arranca los 7 servicios en background con docker-compose.

set -e
cd "$(dirname "$0")"

if ! docker info >/dev/null 2>&1; then
    echo "✗ Docker daemon no responde. Abre Docker Desktop primero."
    exit 1
fi

echo "=== Iniciando 7 servicios ==="
docker compose up -d

echo
echo "Esperando que todos los servicios estén healthy (~15s)..."
sleep 15

docker compose ps --format "table {{.Service}}\t{{.Status}}"

cat <<EOF

✓ Sandbox arriba.

Documentación Swagger UI:
  ApiGateway:    http://localhost:8000/docs   ← entrypoint del frontend
  Identity:      http://localhost:8001/docs
  Patient:       http://localhost:8002/docs
  Inventory:     http://localhost:8003/docs
  Prescription:  http://localhost:8004/docs
  Notification:  http://localhost:8005/docs
  Report:        http://localhost:8006/docs

Probar login:
  curl -X POST http://localhost:8000/api/v1/auth/login \\
    -H "Content-Type: application/json" \\
    -d '{"username":"drperez","password":"medico2026"}'

Detener:             ./stop.sh
Ver logs:            docker compose logs -f <servicio>
EOF
