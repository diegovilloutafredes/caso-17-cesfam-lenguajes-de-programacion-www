"""PatientService — datos de pacientes y apoderados."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from patient_service.db import init_db
from patient_service.routers import patients
from patient_service.seed import seed
from shared.errors import register_envelope_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed()
    yield


app = FastAPI(title="PatientService", version="1.0.0", lifespan=lifespan)
register_envelope_handler(app)

app.include_router(patients.router)


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "service": "patient_service"}


@app.get("/", include_in_schema=False)
def root():
    return {"service": "PatientService", "port": 8002}
