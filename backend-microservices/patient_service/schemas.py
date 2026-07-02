from datetime import date
from typing import Optional

from pydantic import BaseModel


class GuardianCreate(BaseModel):
    rut: str
    firstName: str
    lastName: str
    phone: Optional[str] = None
    email: Optional[str] = None
    relationship: str
    authorizationDate: Optional[date] = None


class PatientUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
