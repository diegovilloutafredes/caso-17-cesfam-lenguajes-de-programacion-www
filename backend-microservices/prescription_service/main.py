from contextlib import asynccontextmanager

from fastapi import FastAPI

from prescription_service.db import init_db
from prescription_service.routers import prescriptions
from prescription_service.seed import seed
from shared.errors import register_envelope_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed()
    yield


app = FastAPI(title="PrescriptionService", version="1.0.0", lifespan=lifespan)
register_envelope_handler(app)

app.include_router(prescriptions.router)


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "service": "prescription_service"}


@app.get("/", include_in_schema=False)
def root():
    return {"service": "PrescriptionService", "port": 8004}
