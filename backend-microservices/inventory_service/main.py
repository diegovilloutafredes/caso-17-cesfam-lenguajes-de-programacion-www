"""InventoryService — catálogo de medicamentos, partidas, stock y bajas."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from inventory_service.db import init_db
from inventory_service.routers import batches, medications, writeoffs
from inventory_service.seed import seed
from shared.errors import register_envelope_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed()
    yield


app = FastAPI(title="InventoryService", version="1.0.0", lifespan=lifespan)
register_envelope_handler(app)

app.include_router(medications.router)
app.include_router(batches.router)
app.include_router(writeoffs.router)


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "service": "inventory_service"}


@app.get("/", include_in_schema=False)
def root():
    return {"service": "InventoryService", "port": 8003}
