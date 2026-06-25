"""NotificationService — envío de SMS/email a pacientes y apoderados.

Integración real con Twilio/SendGrid en producción; en sandbox los envíos
son stubs que solo loguean. Ver `providers.py`.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from notification_service.db import init_db
from notification_service.routers import notifications
from notification_service.seed import seed
from shared.errors import register_envelope_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed()
    yield


app = FastAPI(title="NotificationService", version="1.0.0", lifespan=lifespan)
register_envelope_handler(app)

app.include_router(notifications.router)


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "service": "notification_service"}


@app.get("/", include_in_schema=False)
def root():
    return {"service": "NotificationService", "port": 8005}
