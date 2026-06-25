"""Modelos SQLAlchemy 2.0 de InventoryService (tablas: medications, batches, write_offs)."""

from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from inventory_service.db import Base


class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # "MED-0001"
    code: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    manufacturer: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    components: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(String)
    packaging: Mapped[str] = mapped_column(String)
    minStock: Mapped[int] = mapped_column(Integer)
    # Stock embebido (3 columnas) -> invariante atómico
    availableQuantity: Mapped[int] = mapped_column(Integer, default=0)
    reservedQuantity: Mapped[int] = mapped_column(Integer, default=0)
    physicalQuantity: Mapped[int] = mapped_column(Integer, default=0)


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # "BCH-001"
    medicationId: Mapped[str] = mapped_column(ForeignKey("medications.id"))
    batchNumber: Mapped[str] = mapped_column(String)
    arrivalDate: Mapped[date] = mapped_column(Date)
    expirationDate: Mapped[date] = mapped_column(Date)
    initialQuantity: Mapped[int] = mapped_column(Integer)
    # ⚠️ rastrea el FÍSICO del lote (NO el available del stock del medicamento)
    availableQuantity: Mapped[int] = mapped_column(Integer)


class WriteOff(Base):
    __tablename__ = "write_offs"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # "WOF-001"
    batchId: Mapped[str] = mapped_column(ForeignKey("batches.id"))
    medicationId: Mapped[str] = mapped_column(String)  # copiado del batch
    staffId: Mapped[str] = mapped_column(String)  # user['id'] del token, sin FK cruzada
    reason: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String)
    expiredAt: Mapped[str] = mapped_column(String)  # fecha de la baja (ISO string, mal nombrado)
    discardDate: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
