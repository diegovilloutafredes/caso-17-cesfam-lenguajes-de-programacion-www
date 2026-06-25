"""Seed de NotificationService (PostgreSQL).

Inserta los mismos datos del seed in-memory original, solo si la tabla está vacía.
El helper `next_id` calcula el próximo sufijo consultando el MAX en la BD.
"""

from datetime import datetime

from sqlalchemy import func, select

from .db import SessionLocal
from .models import Notification


def next_id(db, prefix: str) -> str:
    """Próximo ID `PREFIX-NNN` calculando el MAX del sufijo numérico en la tabla."""
    rows = db.execute(select(Notification.id)).scalars().all()
    existing = [
        int(k.split("-")[-1])
        for k in rows
        if isinstance(k, str) and k.startswith(prefix + "-") and k.split("-")[-1].isdigit()
    ]
    nxt = (max(existing) + 1) if existing else 1
    return f"{prefix}-{nxt:03d}"


def seed() -> None:
    db = SessionLocal()
    try:
        if db.execute(select(func.count()).select_from(Notification)).scalar_one() > 0:
            return
        db.add(
            Notification(
                id="NTF-001",
                type="EMAIL",
                event="RESERVATION_AVAILABLE",
                recipientPatientId="PAT-001",
                recipientGuardianId=None,
                recipientAddress="maria70@gmail.com",
                message="Su medicamento Paracetamol 500mg está disponible para retiro.",
                sentAt=datetime.fromisoformat("2026-05-19T10:23:00"),
                status="SENT",
                prescriptionId="R001",
            )
        )
        db.commit()
    finally:
        db.close()
