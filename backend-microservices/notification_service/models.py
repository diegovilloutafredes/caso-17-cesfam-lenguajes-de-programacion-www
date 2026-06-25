"""Modelos SQLAlchemy de NotificationService.

Solo la tabla `notifications`. Columnas en camelCase para igualar las claves JSON
del seed/contrato. `type`/`event`/`status` se almacenan como String (mismas cadenas
del contrato); `sentAt` como DateTime real (se emite `.isoformat()` al serializar).
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # "NTF-001"
    type: Mapped[str] = mapped_column(String)  # SMS | EMAIL
    event: Mapped[str] = mapped_column(String)  # STOCK_ARRIVED | RESERVATION_AVAILABLE | PICKUP_REMINDER
    recipientPatientId: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    recipientGuardianId: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    recipientAddress: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(String)
    sentAt: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # None si falla envío
    status: Mapped[str] = mapped_column(String)  # PENDING | SENT | ERROR
    prescriptionId: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
