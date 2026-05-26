from __future__ import annotations
from datetime import date
from typing import Optional

from pydantic import BaseModel


class PatientBase(BaseModel):
    rut: str
    firstName: str
    lastName: str
    birthDate: Optional[date] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientRead(PatientBase):
    id: int


class Patient(PatientRead):
    pass


class PatientSummary(BaseModel):
    id: int
    firstName: str
    lastName: str


class PatientUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class PatientHistory(BaseModel):
    patient: Patient
    activePrescriptions: list = []
    fullHistory: list = []


class Guardian(BaseModel):
    rut: str
    firstName: str
    lastName: str
    phone: Optional[str] = None
    email: Optional[str] = None
    relationship: Optional[str] = None
    authorizationDate: Optional[date] = None


class PatientCard(BaseModel):
    number: str
    issueDate: Optional[date] = None
from datetime import date
from typing import List, Optional
from pydantic import BaseModel


class PatientCard(BaseModel):
    number: str
    issueDate: date


class Guardian(BaseModel):
    id: str
    patientId: str
    rut: str
    firstName: str
    lastName: str
    phone: Optional[str] = None
    email: Optional[str] = None
    relationship: str
    authorizationDate: Optional[date] = None


class GuardianCreate(BaseModel):
    rut: str
    firstName: str
    lastName: str
    phone: Optional[str] = None
    email: Optional[str] = None
    relationship: str
    authorizationDate: Optional[date] = None


class PatientSummary(BaseModel):
    id: str
    rut: str
    firstName: str
    lastName: str


class Patient(BaseModel):
    id: str
    rut: str
    firstName: str
    lastName: str
    birthDate: Optional[date] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    patientCard: Optional[PatientCard] = None
    guardians: List[Guardian] = []


class PatientUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class PatientHistory(BaseModel):
    patient: Patient
    activePrescriptions: List[dict]  # List[Prescription], sin tipar para evitar importación circular
    fullHistory: List[dict]
