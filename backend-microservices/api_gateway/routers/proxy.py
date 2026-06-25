"""Proxy genérico del BFF: reenvía cada prefijo de dominio al servicio dueño.

El frontend usa una sola base URL (el gateway, :8000). Para los endpoints que NO
son agregadores (login y dashboards tienen sus propias rutas), este proxy reenvía
la petición tal cual (método, path, query, body y token) al servicio correspondiente
y devuelve su respuesta sin alterar el envelope. Maneja JSON y texto plano (reportes).
"""

import os

import httpx
from fastapi import APIRouter, Request, Response

router = APIRouter(tags=["BFF Proxy"])

# Prefijo de path → URL base del servicio dueño.
PROXY_MAP = {
    "patients": os.getenv("PATIENT_SERVICE_URL", "http://localhost:8002"),
    "medications": os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8003"),
    "batches": os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8003"),
    "write-offs": os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8003"),
    "prescriptions": os.getenv("PRESCRIPTION_SERVICE_URL", "http://localhost:8004"),
    "notifications": os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8005"),
    "reports": os.getenv("REPORT_SERVICE_URL", "http://localhost:8006"),
    "analytics": os.getenv("REPORT_SERVICE_URL", "http://localhost:8006"),
    "auth": os.getenv("IDENTITY_SERVICE_URL", "http://localhost:8001"),
}


async def _forward(base_url: str, request: Request) -> Response:
    url = f"{base_url}{request.url.path}"
    headers = {}
    if "authorization" in request.headers:
        headers["Authorization"] = request.headers["authorization"]
    if "content-type" in request.headers:
        headers["Content-Type"] = request.headers["content-type"]
    body = await request.body()
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            upstream = await client.request(
                request.method,
                url,
                params=dict(request.query_params),
                content=body or None,
                headers=headers,
            )
        except httpx.HTTPError:
            return Response(
                content=(
                    '{"statusCode":503,"data":null,"error":'
                    '{"code":"GATEWAY_UPSTREAM","message":"Servicio no disponible"}}'
                ),
                status_code=503,
                media_type="application/json",
            )
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )


def _make_proxy(base_url: str):
    async def proxy(rest: str, request: Request):
        return await _forward(base_url, request)

    return proxy


# Registra una ruta catch-all por prefijo. Se monta DESPUÉS de auth/dashboards en
# main.py, así las rutas específicas (login, dashboards) ganan al matchear.
for _prefix, _base in PROXY_MAP.items():
    router.add_api_route(
        f"/api/v1/{_prefix}{{rest:path}}",
        _make_proxy(_base),
        methods=["GET", "POST", "PUT", "DELETE"],
        include_in_schema=False,
    )
