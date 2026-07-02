from contextlib import asynccontextmanager

from fastapi import FastAPI

from identity_service.db import init_db
from identity_service.routers import auth
from identity_service.seed import seed
from shared.errors import register_envelope_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed()
    yield


app = FastAPI(title="IdentityService", version="1.0.0", lifespan=lifespan)
register_envelope_handler(app)

app.include_router(auth.router)


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "service": "identity_service"}


@app.get("/", include_in_schema=False)
def root():
    return {"service": "IdentityService", "port": 8001}
