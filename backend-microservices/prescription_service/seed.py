"""Seed local de PrescriptionService. Solo conoce recetas.
Referencias a USR-* y PAT-* y MED-* son IDs externos (live en otros servicios).

Las recetas READY_FOR_PICKUP retienen stock reservado en InventoryService (MED-0001=21,
MED-0004=14, MED-0008=120, MED-0009=30). Las RESERVED no reservan stock: la reserva real
ocurre al pasar a READY (mark-available).
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from prescription_service.db import SessionLocal
from prescription_service.models import Prescription, PrescriptionItem

_SEED_PRESCRIPTIONS = [
    {
        "id": "R001", "doctorId": "USR-001", "patientId": "PAT-001",
        "emissionDate": date(2026, 6, 1), "pickupDeadline": date(2026, 8, 1),
        "treatmentType": "SHORT", "durationDays": 7,
        "status": "READY_FOR_PICKUP", "nextScheduledDelivery": None,
        "items": [
            {"medicationId": "MED-0001", "dosesPerInterval": 1, "intervalHours": 8,
             "doseDescription": "1 comprimido c/8h", "durationDays": 7, "totalQuantity": 21},
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
             "doseDescription": "1 comprimido c/24h", "durationDays": 30, "totalQuantity": 30},
        ],
    },
    {
        "id": "R045", "doctorId": "USR-001", "patientId": "PAT-001",
        "emissionDate": date(2026, 5, 2), "pickupDeadline": date(2026, 7, 2),
        "treatmentType": "LONG", "durationDays": 90,
        "status": "RESERVED", "nextScheduledDelivery": date(2026, 6, 2),
        "items": [
            {"medicationId": "MED-0005", "dosesPerInterval": 1, "intervalHours": 12,
             "doseDescription": "1 comprimido c/12h", "durationDays": 30, "totalQuantity": 60},
        ],
    },
    {
        "id": "R012", "doctorId": "USR-001", "patientId": "PAT-001",
        "emissionDate": date(2026, 4, 15), "pickupDeadline": date(2026, 5, 15),
        "treatmentType": "SHORT", "durationDays": 5,
        "status": "PICKED_UP", "nextScheduledDelivery": None,
        "items": [
            {"medicationId": "MED-0002", "dosesPerInterval": 1, "intervalHours": 8,
             "doseDescription": "1 comprimido c/8h", "durationDays": 5, "totalQuantity": 15},
        ],
    },
    {
        "id": "R050", "doctorId": "USR-001", "patientId": "PAT-002",
        "emissionDate": date(2026, 6, 20), "pickupDeadline": date(2026, 8, 20),
        "treatmentType": "LONG", "durationDays": 90,
        "status": "READY_FOR_PICKUP", "nextScheduledDelivery": date(2026, 7, 20),
        "items": [
            {"medicationId": "MED-0008", "dosesPerInterval": 2, "intervalHours": 12,
             "doseDescription": "2 comprimidos c/12h", "durationDays": 30, "totalQuantity": 120},
        ],
    },
    {
        "id": "R051", "doctorId": "USR-003", "patientId": "PAT-003",
        "emissionDate": date(2026, 6, 18), "pickupDeadline": date(2026, 8, 18),
        "treatmentType": "LONG", "durationDays": 90,
        "status": "SUBMITTED", "nextScheduledDelivery": date(2026, 7, 18),
        "items": [
            {"medicationId": "MED-0008", "dosesPerInterval": 1, "intervalHours": 12,
             "doseDescription": "1 comprimido c/12h", "durationDays": 30, "totalQuantity": 60},
        ],
    },
    {
        "id": "R052", "doctorId": "USR-001", "patientId": "PAT-004",
        "emissionDate": date(2026, 6, 22), "pickupDeadline": date(2026, 8, 22),
        "treatmentType": "LONG", "durationDays": 90,
        "status": "RESERVED", "nextScheduledDelivery": date(2026, 7, 22),
        "items": [
            {"medicationId": "MED-0007", "dosesPerInterval": 1, "intervalHours": 24,
             "doseDescription": "1 comprimido c/24h", "durationDays": 30, "totalQuantity": 30},
        ],
    },
    {
        "id": "R053", "doctorId": "USR-003", "patientId": "PAT-002",
        "emissionDate": date(2026, 6, 15), "pickupDeadline": date(2026, 8, 15),
        "treatmentType": "LONG", "durationDays": 90,
        "status": "SUBMITTED", "nextScheduledDelivery": date(2026, 7, 15),
        "items": [
            {"medicationId": "MED-0005", "dosesPerInterval": 1, "intervalHours": 12,
             "doseDescription": "1 comprimido c/12h", "durationDays": 30, "totalQuantity": 60},
        ],
    },
    {
        "id": "R054", "doctorId": "USR-001", "patientId": "PAT-003",
        "emissionDate": date(2026, 6, 21), "pickupDeadline": date(2026, 8, 21),
        "treatmentType": "LONG", "durationDays": 90,
        "status": "READY_FOR_PICKUP", "nextScheduledDelivery": date(2026, 7, 21),
        "items": [
            {"medicationId": "MED-0009", "dosesPerInterval": 1, "intervalHours": 24,
             "doseDescription": "1 comprimido c/24h", "durationDays": 30, "totalQuantity": 30},
        ],
    },
    {
        "id": "R055", "doctorId": "USR-003", "patientId": "PAT-004",
        "emissionDate": date(2026, 6, 10), "pickupDeadline": date(2026, 8, 10),
        "treatmentType": "LONG", "durationDays": 90,
        "status": "PICKED_UP", "nextScheduledDelivery": None,
        "items": [
            {"medicationId": "MED-0009", "dosesPerInterval": 1, "intervalHours": 24,
             "doseDescription": "1 comprimido c/24h", "durationDays": 30, "totalQuantity": 30},
        ],
    },
    {
        "id": "R056", "doctorId": "USR-001", "patientId": "PAT-002",
        "emissionDate": date(2026, 6, 23), "pickupDeadline": date(2026, 8, 23),
        "treatmentType": "SHORT", "durationDays": 7,
        "status": "SUBMITTED", "nextScheduledDelivery": None,
        "items": [
            {"medicationId": "MED-0001", "dosesPerInterval": 1, "intervalHours": 8,
             "doseDescription": "1 comprimido c/8h", "durationDays": 7, "totalQuantity": 21},
        ],
    },
    {
        "id": "R057", "doctorId": "USR-003", "patientId": "PAT-003",
        "emissionDate": date(2026, 6, 19), "pickupDeadline": date(2026, 8, 19),
        "treatmentType": "LONG", "durationDays": 90,
        "status": "SUBMITTED", "nextScheduledDelivery": date(2026, 7, 19),
        "items": [
            {"medicationId": "MED-0010", "dosesPerInterval": 1, "intervalHours": 24,
             "doseDescription": "1 comprimido c/24h", "durationDays": 30, "totalQuantity": 30},
        ],
    },
    {
        "id": "R058", "doctorId": "USR-001", "patientId": "PAT-004",
        "emissionDate": date(2026, 6, 24), "pickupDeadline": date(2026, 8, 24),
        "treatmentType": "LONG", "durationDays": 90,
        "status": "RESERVED", "nextScheduledDelivery": date(2026, 7, 24),
        "items": [
            {"medicationId": "MED-0011", "dosesPerInterval": 1, "intervalHours": 24,
             "doseDescription": "1 comprimido c/24h", "durationDays": 30, "totalQuantity": 30},
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
