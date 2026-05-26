from typing import Optional
from pydantic import BaseModel
from services.common.enums import UserRole


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
