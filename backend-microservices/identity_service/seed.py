"""Seed local de IdentityService. Solo conoce sus propios users."""

from sqlalchemy import select

from identity_service.db import SessionLocal
from identity_service.models import User

USERS = [
    {
        "id": "USR-001",
        "username": "drperez",
        "rut": "11.111.111-1",
        "fullName": "Dr. Juan Pérez",
        "email": "juan.perez@cesfam.cl",
        "role": "doctor",
    },
    {
        "id": "USR-002",
        "username": "mgonzalez",
        "rut": "22.222.222-2",
        "fullName": "María González",
        "email": "maria.gonzalez@cesfam.cl",
        "role": "pharmacy_staff",
    },
    {
        "id": "USR-003",
        "username": "dralopez",
        "rut": "13.555.444-3",
        "fullName": "Dra. Ana López",
        "email": "ana.lopez@cesfam.cl",
        "role": "doctor",
    },
]


def seed() -> None:
    """Inserta los usuarios del seed solo si la tabla está vacía (idempotente)."""
    db = SessionLocal()
    try:
        if db.execute(select(User.id).limit(1)).first() is not None:
            return
        for u in USERS:
            db.add(User(**u))
        db.commit()
    finally:
        db.close()
