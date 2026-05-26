from fastapi import FastAPI
from services.patients.routers import patients
from services.common import db

app = FastAPI(title="Patients Service")
app.include_router(patients.router)


@app.on_event("startup")
def startup():
	db.create_tables()
