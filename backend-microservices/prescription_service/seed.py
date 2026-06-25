"""Seed local de PrescriptionService. Solo conoce recetas.
Referencias a USR-* y PAT-* y MED-* son IDs externos (live en otros servicios).
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from prescription_service.db import SessionLocal
from prescription_service.models import Prescription, PrescriptionItem

_SEED_PRESCRIPTIONS = [
    {
        "id": "R001", "doctorId": "USR-001", "patientId": "PAT-001",
        "emissionDate": date(2026, 4, 15), "pickupDeadline": date(2026, 6, 15),
        "treatmentType": "SHORT", "durationDays": 7,
        "status": "READY_FOR_PICKUP", "nextScheduledDelivery": None,
        "items": [
            {"medicationId": "MED-0001", "dosesPerInterval": 1, "intervalHours": 8,
             "doseDescription": "1 cápsula c/8h", "durationDays": 7, "totalQuantity": 21},
        ],
    },
    {
        "id": "R002", "doctorId": "USR-001", "patientId": "PAT-002",
        "emissionDate": date(2026, 5, 10), "pickupDeadline": date(2026, 7, 10),
        "treatmentType": "SHORT", "durationDays": 10,
        "status": "SUBMITTED", "nextScheduledDelivery": None,
        "items": [
            {"medicationId": "MED-0003", "dosesPerInterval": 1, "intervalHours": 12,
             "doseDescription": "1 cápsula c/12h", "durationDays": 10, "totalQuantity": 20},
        ],
    },
    {
        "id": "R003", "doctorId": "USR-001", "patientId": "PAT-003",
        "emissionDate": date(2026, 5, 5), "pickupDeadline": date(2026, 7, 5),
        "treatmentType": "SHORT", "durationDays": 14,
        "status": "READY_FOR_PICKUP", "nextScheduledDelivery": None,
        "items": [
            {"medicationId": "MED-0004", "dosesPerInterval": 1, "intervalHours": 24,
             "doseDescription": "1 cápsula c/24h", "durationDays": 14, "totalQuantity": 14},
        ],
    },
    {
        "id": "R004", "doctorId": "USR-001", "patientId": "PAT-004",
        "emissionDate": date(2026, 5, 12), "pickupDeadline": date(2026, 7, 12),
        "treatmentType": "LONG", "durationDays": 90,
        "status": "SUBMITTED", "nextScheduledDelivery": date(2026, 6, 12),
        "items": [
            {"medicationId": "MED-0007", "dosesPerInterval": 1, "intervalHours": 24,
             "doseDescription": "1 comp c/24h", "durationDays": 30, "totalQuantity": 30},
        ],
    },
    {
        "id": "R045", "doctorId": "USR-001", "patientId": "PAT-001",
        "emissionDate": date(2026, 5, 2), "pickupDeadline": date(2026, 7, 2),
        "treatmentType": "LONG", "durationDays": 90,
        "status": "RESERVED", "nextScheduledDelivery": date(2026, 6, 2),
        "items": [
            {"medicationId": "MED-0005", "dosesPerInterval": 1, "intervalHours": 12,
             "doseDescription": "1 comp c/12h", "durationDays": 30, "totalQuantity": 60},
        ],
    },
    {
        "id": "R012", "doctorId": "USR-001", "patientId": "PAT-001",
        "emissionDate": date(2026, 4, 15), "pickupDeadline": date(2026, 5, 15),
        "treatmentType": "SHORT", "durationDays": 5,
        "status": "PICKED_UP", "nextScheduledDelivery": None,
        "items": [
            {"medicationId": "MED-0002", "dosesPerInterval": 1, "intervalHours": 8,
             "doseDescription": "1 comp c/8h", "durationDays": 5, "totalQuantity": 15},
        ],
    },
]


def seed() -> None:
    """Inserta las recetas del seed solo si la tabla está vacía (idempotente)."""
    db: Session = SessionLocal()
    try:
        if db.execute(select(Prescription.id).limit(1)).first() is not None:
            return
        for data in _SEED_PRESCRIPTIONS:
            items = [PrescriptionItem(**it) for it in data["items"]]
            rec = Prescription(
                id=data["id"],
                doctorId=data["doctorId"],
                patientId=data["patientId"],
                emissionDate=data["emissionDate"],
                pickupDeadline=data["pickupDeadline"],
                treatmentType=data["treatmentType"],
                durationDays=data["durationDays"],
                status=data["status"],
                nextScheduledDelivery=data["nextScheduledDelivery"],
                items=items,
            )
            db.add(rec)
        db.commit()
    finally:
        db.close()


def next_id(db: Session, prefix: str) -> str:
    """Próximo ID consultando el MAX del sufijo numérico en la BD.

    Para R: el seed llega hasta R045 → próximo R046. Si no hay filas, parte en 100.
    """
    pattern = f"{prefix}%"
    rows = db.execute(
        select(Prescription.id).where(Prescription.id.like(pattern))
    ).scalars().all()
    existing = [
        int(k[len(prefix):])
        for k in rows
        if k[len(prefix):].isdigit()
    ]
    nxt = (max(existing) + 1) if existing else 100
    return f"{prefix}{nxt:03d}"
