from __future__ import annotations
from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from .enums import TreatmentType, PrescriptionStatus


class PrescriptionLine(BaseModel):
    id: Optional[int] = None
    medicationId: str
    dosesPerInterval: Optional[int] = None
    intervalHours: Optional[int] = None
    doseDescription: Optional[str] = None
    durationDays: Optional[int] = None
    totalQuantity: Optional[int] = None


class PrescriptionBase(BaseModel):
    emissionDate: Optional[date] = None
    pickupDeadline: Optional[date] = None
    treatmentType: Optional[TreatmentType] = None
    durationDays: Optional[int] = None
    status: Optional[PrescriptionStatus] = None
    nextScheduledDelivery: Optional[date] = None


class PrescriptionCreate(PrescriptionBase):
    patientId: str
    lines: List[PrescriptionLine]


class PrescriptionRead(PrescriptionBase):
    id: int
    patientId: str
    lines: List[PrescriptionLine]


class Prescription(PrescriptionRead):
    pass


class PrescriptionDetail(PrescriptionRead):
    pass


class BatchAllocation(BaseModel):
    batchId: str
    quantity: int


class DeliverRequest(BaseModel):
    pickerType: str
    guardianId: Optional[str] = None
    thirdPartyRut: Optional[str] = None
    thirdPartyName: Optional[str] = None
    batches: List[BatchAllocation] = []


class ExternalPurchaseRequest(BaseModel):
    notes: Optional[str] = None


class CancelRequest(BaseModel):
    reason: Optional[str] = None
from datetime import date
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from services.common.enums import PrescriptionStatus, TreatmentType


class PrescriptionLine(BaseModel):
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


class PrescriptionDetail(Prescription):
    patientFullName: str
    patientRut: str
    doctorFullName: str
    lines: List[PrescriptionLine]


class PrescriptionCreate(BaseModel):
    patientId: str
    treatmentType: TreatmentType
    durationDays: int = Field(gt=0)
    pickupDeadline: date
    lines: List[PrescriptionLine] = Field(min_length=1)


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
