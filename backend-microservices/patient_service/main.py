"""PatientService — datos de pacientes y apoderados."""

from fastapi import FastAPI

from patient_service.routers import patients
from shared.errors import register_envelope_handler

app = FastAPI(title="PatientService", version="1.0.0")
register_envelope_handler(app)

app.include_router(patients.router)


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "service": "patient_service"}


@app.get("/", include_in_schema=False)
def root():
    return {"service": "PatientService", "port": 8002}
