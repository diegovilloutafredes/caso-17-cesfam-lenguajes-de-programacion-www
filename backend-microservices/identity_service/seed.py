from sqlalchemy import select

from identity_service.db import SessionLocal
from identity_service.models import User
from identity_service.security import hash_password

# credenciales de demostración; también figuran en el README
USERS = [
    {
        "id": "USR-001",
        "username": "drperez",
        "password": "medico2026",
        "rut": "11.111.111-1",
        "fullName": "Dr. Juan Pérez",
        "email": "juan.perez@cesfam.cl",
        "role": "doctor",
    },
    {
        "id": "USR-002",
        "username": "mgonzalez",
        "password": "farmacia2026",
        "rut": "22.222.222-2",
        "fullName": "María González",
        "email": "maria.gonzalez@cesfam.cl",
        "role": "pharmacy_staff",
    },
    {
        "id": "USR-003",
        "username": "dralopez",
        "password": "medico2026",
        "rut": "13.555.444-8",
        "fullName": "Dra. Ana López",
        "email": "ana.lopez@cesfam.cl",
        "role": "doctor",
    },
]


def seed() -> None:
    db = SessionLocal()
    try:
        if db.execute(select(User.id).limit(1)).first() is not None:
            return
        for u in USERS:
            data = {k: v for k, v in u.items() if k != "password"}
            db.add(User(**data, passwordHash=hash_password(u["password"])))
        db.commit()
    finally:
        db.close()
