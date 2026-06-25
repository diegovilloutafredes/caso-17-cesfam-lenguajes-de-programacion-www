"""Adapters de envío (SMS/Email). Stubs locales que loguean en vez de llamar a
Twilio/SendGrid; en producción se reemplaza el cuerpo de `send()` por el SDK real.
"""

import logging
import os
from abc import ABC, abstractmethod

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
        logger.info(f"[TWILIO STUB] SMS → {to}: {message}")
        return True


class SendGridEmailProvider(EmailProvider):
    """Stub local de envío email vía SendGrid."""

    def __init__(self) -> None:
        self.api_key = os.getenv("SENDGRID_API_KEY", "")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@cesfam.cl")

    def send(self, to: str, subject: str, body: str) -> bool:
        logger.info(f"[SENDGRID STUB] Email → {to} | {subject}: {body}")
        return True


# Singletons usados por el router
sms_provider: SmsProvider = TwilioSmsProvider()
email_provider: EmailProvider = SendGridEmailProvider()
