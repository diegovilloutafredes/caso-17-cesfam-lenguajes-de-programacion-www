from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class WriteOffStatus(str, Enum):
    DEDUCTED_FROM_AVAILABLE = "DEDUCTED_FROM_AVAILABLE"
    DISCARDED = "DISCARDED"


class WriteOffReason(str, Enum):
    EXPIRATION = "EXPIRATION"
    DAMAGED = "DAMAGED"
    BROKEN_PACKAGE = "BROKEN_PACKAGE"
    OTHER = "OTHER"


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
    discard: bool = False
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


# --- Inter-service operations (llamadas por PrescriptionService) ---

class StockReserveRequest(BaseModel):
    quantity: int = Field(gt=0)


class StockReleaseRequest(BaseModel):
    quantity: int = Field(gt=0)


class BatchAllocation(BaseModel):
    batchId: str
    quantity: int = Field(gt=0)


class ConsumeRequest(BaseModel):
    allocations: List[BatchAllocation] = Field(min_length=1)
