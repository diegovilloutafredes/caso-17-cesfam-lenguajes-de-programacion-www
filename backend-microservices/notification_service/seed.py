"""Seed local de NotificationService."""

from itertools import count
from typing import Any, Dict

STATE: Dict[str, Dict[str, Any]] = {
    "notifications": {
        "NTF-001": {
            "id": "NTF-001",
            "type": "EMAIL",
            "event": "RESERVATION_AVAILABLE",
            "recipientPatientId": "PAT-001",
            "recipientGuardianId": None,
            "recipientAddress": "maria70@gmail.com",
            "message": "Su medicamento Paracetamol 500mg está disponible para retiro.",
            "sentAt": "2026-05-19T10:23:00",
            "status": "SENT",
            "prescriptionId": "R001",
        },
    },
}

_id_counters: Dict[str, count] = {}


def next_id(prefix: str) -> str:
    if prefix not in _id_counters:
        existing = [
            int(k.split("-")[-1])
            for store in STATE.values()
            for k in store.keys()
            if isinstance(k, str) and k.startswith(prefix + "-") and k.split("-")[-1].isdigit()
        ]
        start = max(existing) + 1 if existing else 1
        _id_counters[prefix] = count(start)
    return f"{prefix}-{next(_id_counters[prefix]):03d}"
