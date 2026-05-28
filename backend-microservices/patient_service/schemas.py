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


class PatientSummary(BaseModel):
    id: str
    rut: str
    firstName: str
    lastName: str
