from fastapi import FastAPI
from services.reports.routers import reports
from services.common import db

app = FastAPI(title="Reports Service")
app.include_router(reports.router)


@app.on_event("startup")
def startup():
	db.create_tables()
