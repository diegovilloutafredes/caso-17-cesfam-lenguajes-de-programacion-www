from fastapi import FastAPI
from services.prescriptions.routers import prescriptions
from services.common import db

app = FastAPI(title="Prescriptions Service")
app.include_router(prescriptions.router)


@app.on_event("startup")
def startup():
	db.create_tables()
