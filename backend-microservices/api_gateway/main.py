"""ApiGateway (BFF) — punto de entrada del frontend.

Expone:
- POST /api/v1/auth/login (passthrough a IdentityService)
- GET /api/v1/doctor/dashboard (agregación BFF)
- GET /api/v1/pharmacy/dashboard (agregación BFF)

Para endpoints no agregados (CRUD directo de pacientes, medicamentos, etc.) el
frontend va directo a los servicios correspondientes. El gateway solo agrega
cuando vale la pena (= reducir N round-trips a 1).
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api_gateway.routers import auth, dashboards, proxy
from shared.errors import register_envelope_handler

app = FastAPI(title="ApiGateway (BFF)", version="1.0.0")
register_envelope_handler(app)

# CORS en el BFF (única entrada del frontend). Auth Bearer en header (sin cookies),
# por eso allow_credentials=False y se acepta el wildcard.
_cors = os.getenv("CORS_ORIGINS", "*").strip()
_origins = ["*"] if _cors == "*" else [o.strip() for o in _cors.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboards.router)
# El proxy catch-all va al final: las rutas específicas (login, dashboards) ganan.
app.include_router(proxy.router)


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "service": "api_gateway"}


@app.get("/", include_in_schema=False)
def root():
    return {
        "service": "ApiGateway",
        "port": 8000,
        "documentation": "/docs",
        "services": {
            "identity": "http://localhost:8001",
            "patient": "http://localhost:8002",
            "inventory": "http://localhost:8003",
            "prescription": "http://localhost:8004",
            "notification": "http://localhost:8005",
            "report": "http://localhost:8006",
        },
    }
