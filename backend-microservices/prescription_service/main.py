"""PrescriptionService — recetas, state machine y orquestación de inventory + notification."""

from fastapi import FastAPI

from prescription_service.routers import prescriptions
from shared.errors import register_envelope_handler

app = FastAPI(title="PrescriptionService", version="1.0.0")
register_envelope_handler(app)

app.include_router(prescriptions.router)


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "service": "prescription_service"}


@app.get("/", include_in_schema=False)
def root():
    return {"service": "PrescriptionService", "port": 8004}
