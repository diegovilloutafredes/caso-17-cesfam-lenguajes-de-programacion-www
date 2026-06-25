#!/usr/bin/env bash
# Test de resiliencia (5.4): con InventoryService caído, el sistema degrada de forma
# acotada (error claro, no cuelga) y otros flujos siguen operando; el Circuit Breaker
# abre tras varios fallos (fail-fast medible por latencia). Requiere docker en el host
# y los servicios arriba.
set -uo pipefail
G="${GATEWAY_URL:-http://localhost:8000}"
TOK="sandbox-token-USR-001"
fail=0
ok() { echo "  ✓ $1"; }
ko() { echo "  ✗ $1"; fail=1; }

echo "1) crear receta SUBMITTED (inventory arriba)"
RID=$(curl -s -X POST "$G/api/v1/prescriptions" -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' \
  -d '{"patientId":"PAT-002","treatmentType":"SHORT","durationDays":7,"pickupDeadline":"2026-07-20","items":[{"medicationId":"MED-0001","dosesPerInterval":1,"intervalHours":8,"doseDescription":"x","durationDays":7,"totalQuantity":5}]}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['id'])")
echo "   receta $RID"

echo "2) detener InventoryService"
docker stop cesfam_inventory >/dev/null

echo "3) prepare con inventory caído debe fallar con error claro (no colgar)"
RESP=$(curl -s -m 12 -X POST "$G/api/v1/prescriptions/$RID/prepare" -H "Authorization: Bearer $TOK")
CODE=$(echo "$RESP" | python3 -c "import sys,json;print((json.load(sys.stdin).get('error') or {}).get('code','NONE'))" 2>/dev/null)
case "$CODE" in
  INVENTORY_SERVICE_ERROR|CONNECTION_REFUSED|CIRCUIT_OPEN|TIMEOUT) ok "falla acotada ($CODE)";;
  *) ko "esperaba error de inventario, got '$CODE'";;
esac

echo "4) degradación: otros flujos siguen operando (listar pacientes)"
PAT=$(curl -s -m 5 -o /dev/null -w "%{http_code}" "$G/api/v1/patients?limit=2" -H "Authorization: Bearer $TOK")
[ "$PAT" = "200" ] && ok "pacientes responde 200" || ko "pacientes responde $PAT"

echo "5) Circuit Breaker abre tras varios fallos (fail-fast por latencia)"
T1=$(curl -s -m 12 -o /dev/null -w "%{time_total}" -X POST "$G/api/v1/prescriptions/$RID/prepare" -H "Authorization: Bearer $TOK")
for _ in 1 2 3 4 5 6; do curl -s -m 12 -o /dev/null -X POST "$G/api/v1/prescriptions/$RID/prepare" -H "Authorization: Bearer $TOK"; done
T2=$(curl -s -m 12 -o /dev/null -w "%{time_total}" -X POST "$G/api/v1/prescriptions/$RID/prepare" -H "Authorization: Bearer $TOK")
echo "   latencia con CB cerrado (reintentos): ${T1}s | con CB abierto (fail-fast): ${T2}s"
python3 -c "import sys; sys.exit(0 if float('$T2') < float('$T1') else 1)" && ok "el breaker abrió (fail-fast más rápido)" || ko "no se observó fail-fast"

echo "6) reactivar InventoryService y esperar recuperación"
docker start cesfam_inventory >/dev/null
curl -s -m 45 --retry 35 --retry-delay 1 --retry-all-errors "$G/api/v1/medications/stock-summary" -H "Authorization: Bearer $TOK" >/dev/null \
  && ok "inventory recuperado" || ko "inventory no recuperó"

echo ""
[ $fail -eq 0 ] && echo "RESILIENCE TEST: PASS" || { echo "RESILIENCE TEST: FAIL"; exit 1; }
