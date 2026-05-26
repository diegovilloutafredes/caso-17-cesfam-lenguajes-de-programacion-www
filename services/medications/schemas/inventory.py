from __future__ import annotations
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field

from .enums import WriteOffReason, WriteOffStatus


class Batch(BaseModel):
    id: str
    medicationId: str
    lotNumber: Optional[str] = None
    expiryDate: Optional[date] = None
    quantity: int = Field(ge=0)
    available: int = Field(ge=0)


class InventoryItem(BaseModel):
    medicationId: str
    name: Optional[str] = None
    totalQuantity: int = Field(ge=0)
    totalAvailable: int = Field(ge=0)
    batches: List[Batch] = []


class StockSummary(BaseModel):
    items: List[InventoryItem]
    totalMedications: int = Field(ge=0)


class WriteOffRequest(BaseModel):
    batchId: str
    quantity: int = Field(gt=0)
    reason: WriteOffReason


class WriteOffResult(BaseModel):
    batchId: str
    quantity: int
    status: WriteOffStatus
    message: Optional[str] = None
