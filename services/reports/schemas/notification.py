from __future__ import annotations
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .enums import NotificationType, NotificationEvent, DeliveryStatus


class NotificationBase(BaseModel):
    type: NotificationType
    event: NotificationEvent
    message: Optional[str] = None


class NotificationCreate(NotificationBase):
    destination: Optional[str] = None


class NotificationRead(NotificationBase):
    id: int
    sentAt: Optional[datetime] = None
    status: DeliveryStatus
