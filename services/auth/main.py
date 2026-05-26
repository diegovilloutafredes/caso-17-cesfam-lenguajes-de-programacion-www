from fastapi import FastAPI
from services.auth.routers import auth
from services.common import db

app = FastAPI(title="Auth Service")
app.include_router(auth.router)


@app.on_event("startup")
def startup():
	db.create_tables()
