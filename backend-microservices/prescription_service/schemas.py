from datetime import date
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class PrescriptionStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    RESERVED = "RESERVED"
    READY_FOR_PICKUP = "READY_FOR_PICKUP"
    PICKED_UP = "PICKED_UP"
    EXTERNAL_PURCHASE = "EXTERNAL_PURCHASE"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


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


class Prescription(BaseModel):
    id: str
    doctorId: str
    patientId: str
    emissionDate: date
    pickupDeadline: date
    treatmentType: TreatmentType
    durationDays: int
    status: PrescriptionStatus
    nextScheduledDelivery: Optional[date] = None
    items: List[PrescriptionItem] = []


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
