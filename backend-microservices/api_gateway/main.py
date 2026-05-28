"""ApiGateway (BFF) — punto de entrada del frontend.

Expone:
- POST /api/v1/auth/login (passthrough a IdentityService)
- GET /api/v1/doctor/dashboard (agregación BFF)
- GET /api/v1/pharmacy/dashboard (agregación BFF)

Para endpoints no agregados (CRUD directo de pacientes, medicamentos, etc.) el
frontend va directo a los servicios correspondientes. El gateway solo agrega
cuando vale la pena (= reducir N round-trips a 1).
"""

from fastapi import FastAPI

from api_gateway.routers import auth, dashboards
from shared.errors import register_envelope_handler

app = FastAPI(title="ApiGateway (BFF)", version="1.0.0")
register_envelope_handler(app)

app.include_router(auth.router)
app.include_router(dashboards.router)


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
