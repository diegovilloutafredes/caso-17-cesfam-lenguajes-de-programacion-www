from fastapi import FastAPI
from services.inventory.routers import batches, writeoffs
from services.common import db

app = FastAPI(title="Inventory Service")
app.include_router(batches.router)
app.include_router(writeoffs.router)


@app.on_event("startup")
def startup():
	db.create_tables()
