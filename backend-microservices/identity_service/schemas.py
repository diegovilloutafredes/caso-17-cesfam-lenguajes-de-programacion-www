from enum import Enum
from typing import Optional

from pydantic import BaseModel


class UserRole(str, Enum):
    DOCTOR = "doctor"
    PHARMACY_STAFF = "pharmacy_staff"


class LoginRequest(BaseModel):
    username: str
    password: str


class User(BaseModel):
    id: str
    username: str
    rut: str
    fullName: str
    email: Optional[str] = None
    role: UserRole


class LoginResponse(BaseModel):
    token: str
    user: User
