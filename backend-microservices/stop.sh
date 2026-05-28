#!/usr/bin/env bash
# Detiene los containers del sandbox.

cd "$(dirname "$0")"

docker compose down
echo "✓ Sandbox detenido."
