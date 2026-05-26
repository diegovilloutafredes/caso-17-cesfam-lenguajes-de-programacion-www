from fastapi import FastAPI
from services.medications.routers import medications
from services.common import db

app = FastAPI(title="Medications Service")
app.include_router(medications.router)


@app.on_event("startup")
def startup():
	db.create_tables()
