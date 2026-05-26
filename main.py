"""Backend FastAPI sandbox para el prototipo CESFAM.

Ejecutar:
    uvicorn main:app --reload --port 8000

Documentación:
    http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.inventory.routers import writeoffs
from services.auth.routers import auth
from services.inventory.routers import batches
from services.medications.routers import medications
from services.patients.routers import patients
from services.prescriptions.routers import prescriptions
from services.reports.routers import reports

app = FastAPI(
    title="API Sandbox CESFAM",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(medications.router)
app.include_router(batches.router)
app.include_router(writeoffs.router)
app.include_router(prescriptions.router)
app.include_router(reports.router)


@app.get("/", include_in_schema=False)
def root():
    return {"message": "API Sandbox CESFAM — documentación en /docs"}
