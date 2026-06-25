"""Seed local de InventoryService: medicamentos, partidas y bajas (idempotente)."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from inventory_service.db import SessionLocal
from inventory_service.models import Batch, Medication, WriteOff

# Invariante por medicamento: physicalQuantity = availableQuantity + reservedQuantity,
# y physicalQuantity = Σ batch.availableQuantity (el available del medicamento descuenta el
# reservado; el de la partida rastrea el físico). Los reservedQuantity de abajo calzan con la
# suma de items de recetas RESERVED/READY del seed de PrescriptionService.
_MEDICATIONS = [
    {
        "id": "MED-0001", "code": "MED-0001", "description": "Paracetamol 500mg",
        "manufacturer": "Laboratorio Chile S.A.", "type": "Genérico — Analgésico",
        "components": "Paracetamol (acetaminofén)",
        "content": "500 mg por comprimido", "packaging": "Caja x 30 comprimidos",
        "minStock": 200,
        "availableQuantity": 429, "reservedQuantity": 21, "physicalQuantity": 450,
    },
    {
        "id": "MED-0002", "code": "MED-0002", "description": "Ibuprofeno 400mg",
        "manufacturer": "Saval", "type": "Genérico — Antiinflamatorio",
        "components": "Ibuprofeno",
        "content": "400 mg por comprimido", "packaging": "Caja x 20 comprimidos",
        "minStock": 200,
        "availableQuantity": 180, "reservedQuantity": 0, "physicalQuantity": 180,
    },
    {
        "id": "MED-0003", "code": "MED-0003", "description": "Amoxicilina 500mg",
        "manufacturer": "Andrómaco", "type": "Genérico — Antibiótico",
        "components": "Amoxicilina trihidrato",
        "content": "500 mg por cápsula", "packaging": "Caja x 21 cápsulas",
        "minStock": 150,
        "availableQuantity": 0, "reservedQuantity": 0, "physicalQuantity": 0,
    },
    {
        "id": "MED-0004", "code": "MED-0004", "description": "Omeprazol 20mg",
        "manufacturer": "Laboratorio Chile S.A.", "type": "Genérico — Inhibidor protones",
        "components": "Omeprazol",
        "content": "20 mg por cápsula", "packaging": "Caja x 28 cápsulas",
        "minStock": 200,
        "availableQuantity": 606, "reservedQuantity": 14, "physicalQuantity": 620,
    },
    {
        "id": "MED-0005", "code": "MED-0005", "description": "Enalapril 10mg",
        "manufacturer": "Saval", "type": "Genérico — Antihipertensivo",
        "components": "Enalapril maleato",
        "content": "10 mg por comprimido", "packaging": "Caja x 30 comprimidos",
        "minStock": 100,
        "availableQuantity": 180, "reservedQuantity": 60, "physicalQuantity": 240,
    },
    {
        "id": "MED-0006", "code": "MED-0006", "description": "Aspirina 500mg",
        "manufacturer": "Bayer", "type": "Marca — Analgésico",
        "components": "Ácido acetilsalicílico",
        "content": "500 mg por comprimido", "packaging": "Caja x 30 comprimidos",
        "minStock": 100,
        "availableQuantity": 120, "reservedQuantity": 0, "physicalQuantity": 120,
    },
    {
        "id": "MED-0007", "code": "MED-0007", "description": "Losartán 50mg",
        "manufacturer": "Andrómaco", "type": "Genérico — Antihipertensivo",
        "components": "Losartán potásico",
        "content": "50 mg por comprimido", "packaging": "Caja x 30 comprimidos",
        "minStock": 150,
        "availableQuantity": 320, "reservedQuantity": 30, "physicalQuantity": 350,
    },
    {
        "id": "MED-0008", "code": "MED-0008", "description": "Metformina 850mg",
        "manufacturer": "Laboratorio Chile S.A.", "type": "Genérico — Antidiabético",
        "components": "Metformina clorhidrato",
        "content": "850 mg por comprimido", "packaging": "Caja x 30 comprimidos recubiertos",
        "minStock": 200,
        "availableQuantity": 380, "reservedQuantity": 120, "physicalQuantity": 500,
    },
    {
        "id": "MED-0009", "code": "MED-0009", "description": "Atorvastatina 20mg",
        "manufacturer": "Saval", "type": "Genérico — Hipolipemiante",
        "components": "Atorvastatina cálcica",
        "content": "20 mg por comprimido", "packaging": "Caja x 30 comprimidos",
        "minStock": 150,
        "availableQuantity": 270, "reservedQuantity": 30, "physicalQuantity": 300,
    },
    {
        "id": "MED-0010", "code": "MED-0010", "description": "Amlodipino 5mg",
        "manufacturer": "Laboratorio Chile S.A.", "type": "Genérico — Antihipertensivo",
        "components": "Amlodipino besilato",
        "content": "5 mg por comprimido", "packaging": "Caja x 30 comprimidos",
        "minStock": 150,
        "availableQuantity": 200, "reservedQuantity": 0, "physicalQuantity": 200,
    },
    {
        "id": "MED-0011", "code": "MED-0011", "description": "Levotiroxina 100mcg",
        "manufacturer": "Merck", "type": "Marca — Hormona tiroidea",
        "components": "Levotiroxina sódica",
        "content": "100 mcg por comprimido", "packaging": "Caja x 30 comprimidos",
        "minStock": 100,
        "availableQuantity": 170, "reservedQuantity": 30, "physicalQuantity": 200,
    },
    {
        "id": "MED-0012", "code": "MED-0012", "description": "Hidroclorotiazida 25mg",
        "manufacturer": "Saval", "type": "Genérico — Diurético",
        "components": "Hidroclorotiazida",
        "content": "25 mg por comprimido", "packaging": "Caja x 30 comprimidos",
        "minStock": 100,
        "availableQuantity": 60, "reservedQuantity": 0, "physicalQuantity": 60,
    },
    {
        "id": "MED-0013", "code": "MED-0013", "description": "Sertralina 50mg",
        "manufacturer": "Andrómaco", "type": "Genérico — Antidepresivo",
        "components": "Sertralina clorhidrato",
        "content": "50 mg por comprimido", "packaging": "Caja x 30 comprimidos recubiertos",
        "minStock": 60,
        "availableQuantity": 0, "reservedQuantity": 0, "physicalQuantity": 0,
    },
    {
        "id": "MED-0014", "code": "MED-0014", "description": "Furosemida 40mg",
        "manufacturer": "Laboratorio Chile S.A.", "type": "Genérico — Diurético",
        "components": "Furosemida",
        "content": "40 mg por comprimido", "packaging": "Caja x 30 comprimidos",
        "minStock": 80,
        "availableQuantity": 140, "reservedQuantity": 0, "physicalQuantity": 140,
    },
]

_BATCHES = [
    {
        "id": "BCH-001", "medicationId": "MED-0001",
        "batchNumber": "P-2026-001", "arrivalDate": date(2025, 12, 1),
        "expirationDate": date(2026, 12, 15),
        "initialQuantity": 450, "availableQuantity": 450,
    },
    {
        "id": "BCH-002", "medicationId": "MED-0002",
        "batchNumber": "P-2026-003", "arrivalDate": date(2026, 3, 15),
        "expirationDate": date(2027, 9, 22),
        "initialQuantity": 200, "availableQuantity": 180,
    },
    {
        "id": "BCH-003", "medicationId": "MED-0004",
        "batchNumber": "P-2025-045", "arrivalDate": date(2025, 11, 20),
        "expirationDate": date(2026, 6, 30),
        "initialQuantity": 350, "availableQuantity": 350,
    },
    {
        "id": "BCH-004", "medicationId": "MED-0004",
        "batchNumber": "P-2026-012", "arrivalDate": date(2026, 4, 5),
        "expirationDate": date(2027, 1, 15),
        "initialQuantity": 280, "availableQuantity": 270,
    },
    {
        "id": "BCH-005", "medicationId": "MED-0005",
        "batchNumber": "P-2026-008", "arrivalDate": date(2026, 2, 14),
        "expirationDate": date(2027, 2, 14),
        "initialQuantity": 240, "availableQuantity": 240,
    },
    {
        "id": "BCH-006", "medicationId": "MED-0007",
        "batchNumber": "P-2026-015", "arrivalDate": date(2026, 4, 22),
        "expirationDate": date(2027, 4, 22),
        "initialQuantity": 350, "availableQuantity": 350,
    },
    {
        "id": "BCH-007", "medicationId": "MED-0006",
        "batchNumber": "P-2026-019", "arrivalDate": date(2026, 5, 1),
        "expirationDate": date(2027, 5, 1),
        "initialQuantity": 120, "availableQuantity": 120,
    },
    {
        "id": "BCH-008", "medicationId": "MED-0008",
        "batchNumber": "P-2026-021", "arrivalDate": date(2026, 5, 10),
        "expirationDate": date(2027, 11, 10),
        "initialQuantity": 500, "availableQuantity": 500,
    },
    {
        "id": "BCH-009", "medicationId": "MED-0009",
        "batchNumber": "P-2026-022", "arrivalDate": date(2026, 5, 12),
        "expirationDate": date(2027, 12, 12),
        "initialQuantity": 300, "availableQuantity": 300,
    },
    {
        "id": "BCH-010", "medicationId": "MED-0010",
        "batchNumber": "P-2026-023", "arrivalDate": date(2026, 5, 15),
        "expirationDate": date(2028, 1, 15),
        "initialQuantity": 200, "availableQuantity": 200,
    },
    {
        "id": "BCH-011", "medicationId": "MED-0011",
        "batchNumber": "P-2026-024", "arrivalDate": date(2026, 5, 18),
        "expirationDate": date(2027, 10, 18),
        "initialQuantity": 200, "availableQuantity": 200,
    },
    {
        "id": "BCH-012", "medicationId": "MED-0012",
        "batchNumber": "P-2026-025", "arrivalDate": date(2026, 4, 20),
        "expirationDate": date(2027, 8, 20),
        "initialQuantity": 60, "availableQuantity": 60,
    },
    {
        "id": "BCH-013", "medicationId": "MED-0014",
        "batchNumber": "P-2026-026", "arrivalDate": date(2026, 5, 22),
        "expirationDate": date(2027, 9, 22),
        "initialQuantity": 80, "availableQuantity": 80,
    },
    {
        "id": "BCH-014", "medicationId": "MED-0014",
        "batchNumber": "P-2026-027", "arrivalDate": date(2026, 6, 1),
        "expirationDate": date(2027, 12, 1),
        "initialQuantity": 60, "availableQuantity": 60,
    },
]

# Bajas que documentan las mermas de partidas (BCH-002 −20, BCH-004 −10): las cantidades de
# arriba ya reflejan el estado posterior; estas filas dejan el registro de la baja.
_WRITE_OFFS = [
    {
        "id": "WOF-001", "batchId": "BCH-002", "medicationId": "MED-0002",
        "staffId": "USR-002", "reason": "EXPIRATION", "quantity": 20,
        "status": "DISCARDED", "expiredAt": "2026-03-20", "discardDate": "2026-03-20",
        "notes": "Unidades vencidas retiradas en control de inventario.",
    },
    {
        "id": "WOF-002", "batchId": "BCH-004", "medicationId": "MED-0004",
        "staffId": "USR-002", "reason": "DAMAGED", "quantity": 10,
        "status": "DISCARDED", "expiredAt": "2026-04-10", "discardDate": "2026-04-10",
        "notes": "Merma por manipulación.",
    },
]

# Mapea cada prefijo de ID a su columna PK para el cálculo de next_id desde la BD.
_ID_SOURCES = {
    "MED": Medication.id,
    "BCH": Batch.id,
    "WOF": WriteOff.id,
}


def next_id(db: Session, prefix: str) -> str:
    """Próximo ID `<prefix>-NNN` calculado desde el MAX del sufijo numérico en la BD."""
    column = _ID_SOURCES[prefix]
    rows = db.execute(select(column).where(column.like(f"{prefix}-%"))).scalars().all()
    existing = [
        int(value.split("-")[-1])
        for value in rows
        if isinstance(value, str) and value.split("-")[-1].isdigit()
    ]
    nxt = max(existing) + 1 if existing else 1
    return f"{prefix}-{nxt:03d}"


def seed() -> None:
    """Inserta el seed solo si las tablas están vacías (idempotente)."""
    db: Session = SessionLocal()
    try:
        if db.execute(select(func.count()).select_from(Medication)).scalar_one() == 0:
            for m in _MEDICATIONS:
                db.add(Medication(**m))
        if db.execute(select(func.count()).select_from(Batch)).scalar_one() == 0:
            for b in _BATCHES:
                db.add(Batch(**b))
        if db.execute(select(func.count()).select_from(WriteOff)).scalar_one() == 0:
            for w in _WRITE_OFFS:
                db.add(WriteOff(**w))
        db.commit()
    finally:
        db.close()
