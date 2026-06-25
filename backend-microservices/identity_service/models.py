"""Modelos SQLAlchemy de IdentityService. Única tabla: users."""

from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from identity_service.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)            # "USR-001", PK natural
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    rut: Mapped[str] = mapped_column(String)
    fullName: Mapped[str] = mapped_column(String)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String)                           # "doctor" / "pharmacy_staff"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "rut": self.rut,
            "fullName": self.fullName,
            "email": self.email,
            "role": self.role,
        }
