"""IdentityService — autenticación de usuarios del sistema CESFAM."""

from fastapi import FastAPI

from identity_service.routers import auth
from shared.errors import register_envelope_handler

app = FastAPI(title="IdentityService", version="1.0.0")
register_envelope_handler(app)

app.include_router(auth.router)


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "service": "identity_service"}


@app.get("/", include_in_schema=False)
def root():
    return {"service": "IdentityService", "port": 8001}
