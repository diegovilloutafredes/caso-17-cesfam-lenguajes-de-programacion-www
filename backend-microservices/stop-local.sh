#!/usr/bin/env bash
# Detiene los 7 servicios locales (modo sin Docker) usando los PIDs guardados.

cd "$(dirname "$0")"

if [ ! -d ".pids" ]; then
    echo "No hay servicios locales corriendo (sin carpeta .pids/)."
    exit 0
fi

for pidfile in .pids/*.pid; do
    [ -f "$pidfile" ] || continue
    pid=$(cat "$pidfile")
    name=$(basename "$pidfile" .pid)
    if kill "$pid" 2>/dev/null; then
        echo "  ✓ Detenido $name (PID $pid)"
    else
        echo "  · $name (PID $pid) ya no estaba activo"
    fi
done

rm -rf .pids
echo
echo "✓ Sandbox local detenido."
