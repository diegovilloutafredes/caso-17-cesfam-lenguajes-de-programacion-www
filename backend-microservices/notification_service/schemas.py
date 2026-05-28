from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class NotificationType(str, Enum):
    SMS = "SMS"
    EMAIL = "EMAIL"


class DeliveryStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    ERROR = "ERROR"


class NotificationEvent(str, Enum):
    STOCK_ARRIVED = "STOCK_ARRIVED"
    RESERVATION_AVAILABLE = "RESERVATION_AVAILABLE"
    PICKUP_REMINDER = "PICKUP_REMINDER"


class Notification(BaseModel):
    id: str
    type: NotificationType
    event: NotificationEvent
    recipientPatientId: Optional[str] = None
    recipientGuardianId: Optional[str] = None
    recipientAddress: str  # phone (SMS) o email (EMAIL)
    message: str
    sentAt: Optional[str] = None
    status: DeliveryStatus
    prescriptionId: Optional[str] = None


class NotificationCreate(BaseModel):
    type: NotificationType
    event: NotificationEvent
    recipientPatientId: Optional[str] = None
    recipientGuardianId: Optional[str] = None
    recipientAddress: str  # phone o email; caller (PrescriptionService) lo resuelve via PatientService
    message: str
    prescriptionId: Optional[str] = None
