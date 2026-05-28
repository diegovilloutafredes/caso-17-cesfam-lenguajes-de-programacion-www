"""NotificationService — envío de SMS/email a pacientes y apoderados.

Integración real con Twilio/SendGrid en producción; en sandbox los envíos
son stubs que solo loguean. Ver `providers.py`.
"""

from fastapi import FastAPI

from notification_service.routers import notifications
from shared.errors import register_envelope_handler

app = FastAPI(title="NotificationService", version="1.0.0")
register_envelope_handler(app)

app.include_router(notifications.router)


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "service": "notification_service"}


@app.get("/", include_in_schema=False)
def root():
    return {"service": "NotificationService", "port": 8005}
