"""Columnas en camelCase para calzar con el JSON; USR-*/PAT-*/MED-* son ids externos."""

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from prescription_service.db import Base


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # "R001"
    doctorId: Mapped[str] = mapped_column(String)
    patientId: Mapped[str] = mapped_column(String, index=True)
    emissionDate: Mapped[date] = mapped_column(Date)
    pickupDeadline: Mapped[date] = mapped_column(Date)
    treatmentType: Mapped[str] = mapped_column(String)
    durationDays: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String, index=True)
    nextScheduledDelivery: Mapped[date | None] = mapped_column(Date, nullable=True)
    # fecha en que se emitió el recordatorio de próximo retiro, para no repetirlo
    reminderSentAt: Mapped[date | None] = mapped_column(Date, nullable=True)
    externalPurchaseNotes: Mapped[str | None] = mapped_column(String, nullable=True)
    cancelReason: Mapped[str | None] = mapped_column(String, nullable=True)
    delivery: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    items: Mapped[list["PrescriptionItem"]] = relationship(
        back_populates="prescription",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PrescriptionItem.id",
    )


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prescriptionId: Mapped[str] = mapped_column(ForeignKey("prescriptions.id"))
    medicationId: Mapped[str] = mapped_column(String)
    dosesPerInterval: Mapped[int] = mapped_column(Integer)
    intervalHours: Mapped[int] = mapped_column(Integer)
    doseDescription: Mapped[str] = mapped_column(String)
    durationDays: Mapped[int] = mapped_column(Integer)
    totalQuantity: Mapped[int] = mapped_column(Integer)

    prescription: Mapped["Prescription"] = relationship(back_populates="items")
