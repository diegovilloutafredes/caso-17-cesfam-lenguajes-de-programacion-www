"""Adapter pattern para proveedores externos de envío.

En **producción** estos adapters se conectan a:
- **Twilio** (SMS) — `from twilio.rest import Client`
- **SendGrid** (Email) — `from sendgrid import SendGridAPIClient`

En este **sandbox** solo se logueam los envíos. No se requieren credenciales
reales para correrlo.

Para activar implementación real:
1. Agregar `twilio>=9.0` y `sendgrid>=6.11` a requirements.txt
2. Setear env vars: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER,
   SENDGRID_API_KEY, SENDGRID_FROM_EMAIL
3. Descomentar el bloque marcado `# PROD` en cada provider
"""

import logging
import os
from abc import ABC, abstractmethod

# uvicorn ya configura el root logger; acá solo obtenemos un logger nombrado.
logger = logging.getLogger("notifications.providers")


class SmsProvider(ABC):
    @abstractmethod
    def send(self, to: str, message: str) -> bool:
        ...


class EmailProvider(ABC):
    @abstractmethod
    def send(self, to: str, subject: str, body: str) -> bool:
        ...


class TwilioSmsProvider(SmsProvider):
    """Stub local de envío SMS vía Twilio."""

    def __init__(self) -> None:
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER", "+1234567890")

    def send(self, to: str, message: str) -> bool:
        # PROD:
        # from twilio.rest import Client
        # client = Client(self.account_sid, self.auth_token)
        # msg = client.messages.create(to=to, from_=self.from_number, body=message)
        # return msg.sid is not None
        logger.info(f"[TWILIO STUB] SMS → {to}: {message}")
        return True


class SendGridEmailProvider(EmailProvider):
    """Stub local de envío email vía SendGrid."""

    def __init__(self) -> None:
        self.api_key = os.getenv("SENDGRID_API_KEY", "")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@cesfam.cl")

    def send(self, to: str, subject: str, body: str) -> bool:
        # PROD:
        # from sendgrid import SendGridAPIClient
        # from sendgrid.helpers.mail import Mail
        # message = Mail(from_email=self.from_email, to_emails=to,
        #                subject=subject, html_content=body)
        # response = SendGridAPIClient(self.api_key).send(message)
        # return 200 <= response.status_code < 300
        logger.info(f"[SENDGRID STUB] Email → {to} | {subject}: {body}")
        return True


# Singletons usados por el router
sms_provider: SmsProvider = TwilioSmsProvider()
email_provider: EmailProvider = SendGridEmailProvider()
