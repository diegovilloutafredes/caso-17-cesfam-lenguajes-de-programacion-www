#!/usr/bin/env bash
# Instala el sandbox usando Docker (modo recomendado).
# Pre-requisito: Docker Desktop instalado y corriendo.

set -e
cd "$(dirname "$0")"

echo "=== Verificando Docker ==="
if ! command -v docker >/dev/null 2>&1; then
    echo "✗ Docker no está instalado. Instalalo desde https://www.docker.com/products/docker-desktop"
    exit 1
fi
if ! docker info >/dev/null 2>&1; then
    echo "✗ Docker daemon no responde. Abre Docker Desktop y espera al ícono verde."
    exit 1
fi
echo "✓ Docker activo: $(docker --version)"
echo

echo "=== Build de las 7 imágenes (~2 min primera vez) ==="
docker compose build
echo
echo "✓ Instalación completa. Para arrancar el sandbox: ./run.sh"
