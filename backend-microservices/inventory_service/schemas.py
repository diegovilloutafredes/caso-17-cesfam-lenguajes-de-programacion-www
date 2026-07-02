from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class WriteOffReason(str, Enum):
    EXPIRATION = "EXPIRATION"
    DAMAGED = "DAMAGED"
    BROKEN_PACKAGE = "BROKEN_PACKAGE"
    OTHER = "OTHER"


class BatchCreate(BaseModel):
    batchNumber: str
    expirationDate: date
    initialQuantity: int = Field(gt=0)


class BatchWriteOff(BaseModel):
    reason: WriteOffReason
    quantity: int = Field(gt=0)
    discard: bool = False
    notes: Optional[str] = None


class StockReserveRequest(BaseModel):
    quantity: int = Field(gt=0)


class StockReleaseRequest(BaseModel):
    quantity: int = Field(gt=0)


class BatchAllocation(BaseModel):
    batchId: str
    quantity: int = Field(gt=0)


class ExpectedItem(BaseModel):
    medicationId: str
    quantity: int = Field(gt=0)


class ConsumeRequest(BaseModel):
    allocations: List[BatchAllocation] = Field(min_length=1)
    expectedItems: List[ExpectedItem] = Field(min_length=1)
