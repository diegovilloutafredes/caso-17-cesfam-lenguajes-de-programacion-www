from typing import Optional
from pydantic import BaseModel, EmailStr
from .enums import UserRole


class UserBase(BaseModel):
    username: str
    rut: str
    fullName: Optional[str] = None
    email: Optional[EmailStr] = None
    role: UserRole


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
