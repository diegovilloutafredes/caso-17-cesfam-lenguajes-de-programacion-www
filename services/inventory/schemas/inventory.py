from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

from services.common.enums import WriteOffReason, WriteOffStatus


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
