"""Seed local de InventoryService: medicamentos, partidas y write-offs."""

from datetime import date
from itertools import count
from typing import Any, Dict

STATE: Dict[str, Dict[str, Any]] = {
    "medications": {
        "MED-0001": {
            "id": "MED-0001", "code": "MED-0001", "description": "Paracetamol 500mg",
            "manufacturer": "Laboratorio Chile S.A.", "type": "Genérico — Analgésico",
            "components": "Paracetamol (acetaminofén)",
            "content": "500 mg por comprimido", "packaging": "Caja x 30 comprimidos",
            "minStock": 200,
            "stock": {"availableQuantity": 429, "reservedQuantity": 21, "physicalQuantity": 450},
        },
        "MED-0002": {
            "id": "MED-0002", "code": "MED-0002", "description": "Ibuprofeno 400mg",
            "manufacturer": "Saval", "type": "Genérico — Antiinflamatorio",
            "components": "Ibuprofeno",
            "content": "400 mg por comprimido", "packaging": "Caja x 20 comprimidos",
            "minStock": 200,
            "stock": {"availableQuantity": 180, "reservedQuantity": 0, "physicalQuantity": 180},
        },
        "MED-0003": {
            "id": "MED-0003", "code": "MED-0003", "description": "Amoxicilina 500mg",
            "manufacturer": "Andrómaco", "type": "Genérico — Antibiótico",
            "components": "Amoxicilina trihidrato",
            "content": "500 mg por cápsula", "packaging": "Caja x 21 cápsulas",
            "minStock": 150,
            "stock": {"availableQuantity": 0, "reservedQuantity": 0, "physicalQuantity": 0},
        },
        "MED-0004": {
            "id": "MED-0004", "code": "MED-0004", "description": "Omeprazol 20mg",
            "manufacturer": "Laboratorio Chile S.A.", "type": "Genérico — Inhibidor protones",
            "components": "Omeprazol",
            "content": "20 mg por cápsula", "packaging": "Caja x 28 cápsulas",
            "minStock": 200,
            "stock": {"availableQuantity": 606, "reservedQuantity": 14, "physicalQuantity": 620},
        },
        "MED-0005": {
            "id": "MED-0005", "code": "MED-0005", "description": "Enalapril 10mg",
            "manufacturer": "Saval", "type": "Genérico — Antihipertensivo",
            "components": "Enalapril maleato",
            "content": "10 mg por comprimido", "packaging": "Caja x 30 comprimidos",
            "minStock": 100,
            "stock": {"availableQuantity": 180, "reservedQuantity": 60, "physicalQuantity": 240},
        },
        "MED-0006": {
            "id": "MED-0006", "code": "MED-0006", "description": "Aspirina 500mg",
            "manufacturer": "Bayer", "type": "Marca — Analgésico",
            "components": "Ácido acetilsalicílico",
            "content": "500 mg por comprimido", "packaging": "Caja x 30 comprimidos",
            "minStock": 100,
            "stock": {"availableQuantity": 120, "reservedQuantity": 0, "physicalQuantity": 120},
        },
        "MED-0007": {
            "id": "MED-0007", "code": "MED-0007", "description": "Losartán 50mg",
            "manufacturer": "Andrómaco", "type": "Genérico — Antihipertensivo",
            "components": "Losartán potásico",
            "content": "50 mg por comprimido", "packaging": "Caja x 30 comprimidos",
            "minStock": 150,
            "stock": {"availableQuantity": 350, "reservedQuantity": 0, "physicalQuantity": 350},
        },
    },
    "batches": {
        "BCH-001": {
            "id": "BCH-001", "medicationId": "MED-0001",
            "batchNumber": "P-2026-001", "arrivalDate": date(2025, 12, 1),
            "expirationDate": date(2026, 12, 15),
            "initialQuantity": 450, "availableQuantity": 450,
        },
        "BCH-002": {
            "id": "BCH-002", "medicationId": "MED-0002",
            "batchNumber": "P-2026-003", "arrivalDate": date(2026, 3, 15),
            "expirationDate": date(2027, 9, 22),
            "initialQuantity": 200, "availableQuantity": 180,
        },
        "BCH-003": {
            "id": "BCH-003", "medicationId": "MED-0004",
            "batchNumber": "P-2025-045", "arrivalDate": date(2025, 11, 20),
            "expirationDate": date(2026, 6, 30),
            "initialQuantity": 350, "availableQuantity": 350,
        },
        "BCH-004": {
            "id": "BCH-004", "medicationId": "MED-0004",
            "batchNumber": "P-2026-012", "arrivalDate": date(2026, 4, 5),
            "expirationDate": date(2027, 1, 15),
            "initialQuantity": 280, "availableQuantity": 270,
        },
        "BCH-005": {
            "id": "BCH-005", "medicationId": "MED-0005",
            "batchNumber": "P-2026-008", "arrivalDate": date(2026, 2, 14),
            "expirationDate": date(2027, 2, 14),
            "initialQuantity": 240, "availableQuantity": 240,
        },
        "BCH-006": {
            "id": "BCH-006", "medicationId": "MED-0007",
            "batchNumber": "P-2026-015", "arrivalDate": date(2026, 4, 22),
            "expirationDate": date(2027, 4, 22),
            "initialQuantity": 350, "availableQuantity": 350,
        },
        "BCH-007": {
            "id": "BCH-007", "medicationId": "MED-0006",
            "batchNumber": "P-2026-019", "arrivalDate": date(2026, 5, 1),
            "expirationDate": date(2027, 5, 1),
            "initialQuantity": 120, "availableQuantity": 120,
        },
    },
    "writeOffs": {},
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
