from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class MedicationBase(BaseModel):
    code: str
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    type: Optional[str] = None
    components: Optional[str] = None
    content: Optional[str] = None
    packaging: Optional[str] = None
    minStock: Optional[int] = None


class MedicationCreate(MedicationBase):
    pass


class MedicationRead(MedicationBase):
    id: int
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

from services.common.enums import WriteOffReason, WriteOffStatus


class Stock(BaseModel):
    availableQuantity: int
    reservedQuantity: int
    physicalQuantity: int


class Batch(BaseModel):
    id: str
    medicationId: str
    batchNumber: str
    arrivalDate: date
    expirationDate: date
    initialQuantity: int
    availableQuantity: int


class BatchCreate(BaseModel):
    batchNumber: str
    expirationDate: date
    initialQuantity: int = Field(gt=0)


class BatchWriteOff(BaseModel):
    reason: WriteOffReason
    quantity: int = Field(gt=0)
    discard: bool = False  # si True, también descuenta physicalQuantity
    notes: Optional[str] = None


class WriteOff(BaseModel):
    id: str
    batchId: str
    medicationId: str
    staffId: str
    reason: WriteOffReason
    quantity: int
    status: WriteOffStatus
    expiredAt: date
    discardDate: Optional[date] = None
    notes: Optional[str] = None


class Medication(BaseModel):
    id: str
    code: str
    description: str
    manufacturer: str
    type: str
    components: str
    content: str
    packaging: str
    minStock: int
    stock: Stock


class MedicationDetail(Medication):
    batches: List[Batch]


class StockSummary(BaseModel):
    available: int
    lowStock: int
    outOfStock: int
    totalMedications: int
