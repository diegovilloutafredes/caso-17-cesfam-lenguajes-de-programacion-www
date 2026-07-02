from datetime import date
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class TreatmentType(str, Enum):
    SHORT = "SHORT"
    LONG = "LONG"


class PrescriptionItem(BaseModel):
    medicationId: str
    dosesPerInterval: int = Field(gt=0)
    intervalHours: int = Field(gt=0)
    doseDescription: str
    durationDays: int = Field(gt=0)
    totalQuantity: int = Field(gt=0)


class PrescriptionCreate(BaseModel):
    patientId: str
    treatmentType: TreatmentType
    durationDays: int = Field(gt=0)
    pickupDeadline: date
    items: List[PrescriptionItem] = Field(min_length=1)


class BatchAllocation(BaseModel):
    batchId: str
    quantity: int = Field(gt=0)


class DeliverRequest(BaseModel):
    pickerType: Literal["patient", "guardian", "third_party"]
    guardianId: Optional[str] = None
    thirdPartyRut: Optional[str] = None
    thirdPartyName: Optional[str] = None
    batches: List[BatchAllocation] = Field(min_length=1)


class ExternalPurchaseRequest(BaseModel):
    notes: Optional[str] = None


class CancelRequest(BaseModel):
    reason: Optional[str] = None
