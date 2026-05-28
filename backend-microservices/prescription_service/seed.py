"""Seed local de PrescriptionService. Solo conoce recetas.
Referencias a USR-* y PAT-* y MED-* son IDs externos (live en otros servicios).
"""

from itertools import count
from typing import Any, Dict

STATE: Dict[str, Dict[str, Any]] = {
    "prescriptions": {
        "R001": {
            "id": "R001", "doctorId": "USR-001", "patientId": "PAT-001",
            "emissionDate": "2026-04-15", "pickupDeadline": "2026-06-15",
            "treatmentType": "SHORT", "durationDays": 7,
            "status": "READY_FOR_PICKUP", "nextScheduledDelivery": None,
            "items": [
                {"medicationId": "MED-0001", "dosesPerInterval": 1, "intervalHours": 8,
                 "doseDescription": "1 cápsula c/8h", "durationDays": 7, "totalQuantity": 21},
            ],
        },
        "R002": {
            "id": "R002", "doctorId": "USR-001", "patientId": "PAT-002",
            "emissionDate": "2026-05-10", "pickupDeadline": "2026-07-10",
            "treatmentType": "SHORT", "durationDays": 10,
            "status": "SUBMITTED", "nextScheduledDelivery": None,
            "items": [
                {"medicationId": "MED-0003", "dosesPerInterval": 1, "intervalHours": 12,
                 "doseDescription": "1 cápsula c/12h", "durationDays": 10, "totalQuantity": 20},
            ],
        },
        "R003": {
            "id": "R003", "doctorId": "USR-001", "patientId": "PAT-003",
            "emissionDate": "2026-05-05", "pickupDeadline": "2026-07-05",
            "treatmentType": "SHORT", "durationDays": 14,
            "status": "READY_FOR_PICKUP", "nextScheduledDelivery": None,
            "items": [
                {"medicationId": "MED-0004", "dosesPerInterval": 1, "intervalHours": 24,
                 "doseDescription": "1 cápsula c/24h", "durationDays": 14, "totalQuantity": 14},
            ],
        },
        "R004": {
            "id": "R004", "doctorId": "USR-001", "patientId": "PAT-004",
            "emissionDate": "2026-05-12", "pickupDeadline": "2026-07-12",
            "treatmentType": "LONG", "durationDays": 90,
            "status": "SUBMITTED", "nextScheduledDelivery": "2026-06-12",
            "items": [
                {"medicationId": "MED-0007", "dosesPerInterval": 1, "intervalHours": 24,
                 "doseDescription": "1 comp c/24h", "durationDays": 30, "totalQuantity": 30},
            ],
        },
        "R045": {
            "id": "R045", "doctorId": "USR-001", "patientId": "PAT-001",
            "emissionDate": "2026-05-02", "pickupDeadline": "2026-07-02",
            "treatmentType": "LONG", "durationDays": 90,
            "status": "RESERVED", "nextScheduledDelivery": "2026-06-02",
            "items": [
                {"medicationId": "MED-0005", "dosesPerInterval": 1, "intervalHours": 12,
                 "doseDescription": "1 comp c/12h", "durationDays": 30, "totalQuantity": 60},
            ],
        },
        "R012": {
            "id": "R012", "doctorId": "USR-001", "patientId": "PAT-001",
            "emissionDate": "2026-04-15", "pickupDeadline": "2026-05-15",
            "treatmentType": "SHORT", "durationDays": 5,
            "status": "PICKED_UP", "nextScheduledDelivery": None,
            "items": [
                {"medicationId": "MED-0002", "dosesPerInterval": 1, "intervalHours": 8,
                 "doseDescription": "1 comp c/8h", "durationDays": 5, "totalQuantity": 15},
            ],
        },
    },
}

_id_counters: Dict[str, count] = {}


def next_id(prefix: str) -> str:
    if prefix not in _id_counters:
        existing = [
            int(k[1:]) if k[1:].isdigit() else 0
            for store in STATE.values()
            for k in store.keys()
            if isinstance(k, str) and k.startswith(prefix)
        ]
        start = max(existing) + 1 if existing else 100
        _id_counters[prefix] = count(start)
    return f"{prefix}{next(_id_counters[prefix]):03d}"
