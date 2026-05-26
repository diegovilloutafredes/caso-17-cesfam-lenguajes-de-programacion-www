"""Almacén de datos en memoria. La seed se carga al importar. Refleja los datos mock del prototipo."""

from datetime import date
from typing import Any, Dict
from itertools import count

STATE: Dict[str, Dict[str, Any]] = {
    "users": {},
    "patients": {},
    "guardians": {},
    "medications": {},
    "batches": {},
    "prescriptions": {},
    "notifications": {},
    "writeOffs": {},
}

_id_counters: Dict[str, count] = {}


def next_id(prefix: str) -> str:
    """Genera el siguiente id para un prefijo de recurso (ej: 'BCH', 'PAT')."""
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


def _seed() -> None:
 
    
    STATE["users"] = {
        "USR-001": {
            "id": "USR-001",
            "username": "drperez",
            "rut": "11.111.111-1",
            "fullName": "Dr. Juan Pérez",
            "email": "juan.perez@cesfam.cl",
            "role": "doctor",
        },
        "USR-002": {
            "id": "USR-002",
            "username": "mgonzalez",
            "rut": "22.222.222-2",
            "fullName": "María González",
            "email": "maria.gonzalez@cesfam.cl",
            "role": "pharmacy_staff",
        },
        "USR-003": {
            "id": "USR-003",
            "username": "dralopez",
            "rut": "13.555.444-3",
            "fullName": "Dra. Ana López",
            "email": "ana.lopez@cesfam.cl",
            "role": "doctor",
        },
    }

    
    STATE["patients"] = {
        "PAT-001": {
            "id": "PAT-001",
            "rut": "12.345.678-9",
            "firstName": "María",
            "lastName": "González González",
            "birthDate": date(1955, 8, 12),
            "address": "Calle BKN 1543, Limache",
            "phone": "+56 9 1234 9300",
            "email": "maria70@gmail.com",
            "patientCard": {"number": "CP-2024-12345", "issueDate": date(2024, 3, 15)},
        },
        "PAT-002": {
            "id": "PAT-002",
            "rut": "23.456.789-0",
            "firstName": "Carlos",
            "lastName": "Ramírez",
            "birthDate": date(1968, 2, 4),
            "address": "Av. Central 234, Limache",
            "phone": "+56 9 8888 7777",
            "email": "carlos.ramirez@correo.cl",
            "patientCard": {"number": "CP-2024-23456", "issueDate": date(2024, 4, 2)},
        },
        "PAT-003": {
            "id": "PAT-003",
            "rut": "34.567.890-1",
            "firstName": "Ana",
            "lastName": "Martínez",
            "birthDate": date(1972, 11, 23),
            "address": "Pasaje 12 #43, Quillota",
            "phone": "+56 9 7777 6666",
            "email": "ana.martinez@correo.cl",
            "patientCard": {"number": "CP-2024-34567", "issueDate": date(2024, 5, 10)},
        },
        "PAT-004": {
            "id": "PAT-004",
            "rut": "45.678.901-2",
            "firstName": "Pedro",
            "lastName": "Silva",
            "birthDate": date(1980, 7, 17),
            "address": "Calle Los Olivos 88, Limache",
            "phone": "+56 9 6666 5555",
            "email": "pedro.silva@correo.cl",
            "patientCard": {"number": "CP-2024-45678", "issueDate": date(2024, 6, 1)},
        },
        "PAT-005": {
            "id": "PAT-005",
            "rut": "13.464.215-7",
            "firstName": "Gustavo",
            "lastName": "González González",
            "birthDate": date(1958, 4, 22),
            "address": "Calle BKN 1543, Limache",
            "phone": "+56 9 1234 9301",
            "email": "gustavo@correo.cl",
            "patientCard": {"number": "CP-2024-13464", "issueDate": date(2024, 3, 15)},
        },
        "PAT-006": {
            "id": "PAT-006", "rut": "17.893.242-K", "firstName": "Lamine", "lastName": "Yamal",
            "birthDate": date(1992, 1, 15), "address": "Av. Brasil 100",
            "phone": "+56 9 5555 4444", "email": "lyamal@correo.cl",
            "patientCard": {"number": "CP-2024-17893", "issueDate": date(2024, 7, 8)},
        },
        "PAT-007": {
            "id": "PAT-007", "rut": "18.991.490-5", "firstName": "Cristian", "lastName": "Zapata",
            "birthDate": date(1990, 9, 9), "address": "Calle Sur 45",
            "phone": "+56 9 4444 3333", "email": "czapata@correo.cl",
            "patientCard": {"number": "CP-2024-18991", "issueDate": date(2024, 7, 15)},
        },
        "PAT-008": {
            "id": "PAT-008", "rut": "20.064.015-2", "firstName": "Lucas", "lastName": "Vergara",
            "birthDate": date(1995, 12, 1), "address": "Calle Norte 21",
            "phone": "+56 9 3333 2222", "email": "lvergara@correo.cl",
            "patientCard": {"number": "CP-2024-20064", "issueDate": date(2024, 8, 3)},
        },
    }

    
    STATE["guardians"] = {
        "GRD-001": {
            "id": "GRD-001", "patientId": "PAT-001",
            "rut": "18.434.915-K", "firstName": "Pedri", "lastName": "González",
            "phone": "+56 9 2222 1111", "email": "pedri@correo.cl",
            "relationship": "Hijo",
            "authorizationDate": date(2024, 9, 12),
        },
        "GRD-002": {
            "id": "GRD-002", "patientId": "PAT-001",
            "rut": "13.464.215-7", "firstName": "Gustavo", "lastName": "González",
            "phone": "+56 9 1234 9301", "email": "gustavo@correo.cl",
            "relationship": "Esposo",
            "authorizationDate": date(2023, 5, 4),
        },
    }

    
    STATE["medications"] = {
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
            "content": "500 mg por comprimido", "packaging": "Caja x 20 comprimidos",
            "minStock": 500,
            "stock": {"availableQuantity": 50, "reservedQuantity": 0, "physicalQuantity": 50},
        },
        "MED-0007": {
            "id": "MED-0007", "code": "MED-0007", "description": "Atorvastatina 20mg",
            "manufacturer": "Andrómaco", "type": "Genérico — Estatina",
            "components": "Atorvastatina cálcica",
            "content": "20 mg por comprimido", "packaging": "Caja x 30 comprimidos",
            "minStock": 150,
            "stock": {"availableQuantity": 350, "reservedQuantity": 0, "physicalQuantity": 350},
        },
    }

    
    STATE["batches"] = {
        "BCH-001": {
            "id": "BCH-001", "medicationId": "MED-0001",
            "batchNumber": "P-2026-001", "arrivalDate": date(2025, 12, 1),
            "expirationDate": date(2026, 12, 15),
            "initialQuantity": 500, "availableQuantity": 200,
        },
        "BCH-002": {
            "id": "BCH-002", "medicationId": "MED-0001",
            "batchNumber": "P-2026-003", "arrivalDate": date(2026, 3, 15),
            "expirationDate": date(2027, 9, 22),
            "initialQuantity": 300, "availableQuantity": 250,
        },
        "BCH-003": {
            "id": "BCH-003", "medicationId": "MED-0002",
            "batchNumber": "P-2025-045", "arrivalDate": date(2025, 11, 20),
            "expirationDate": date(2026, 11, 30),
            "initialQuantity": 300, "availableQuantity": 180,
        },
        "BCH-004": {
            "id": "BCH-004", "medicationId": "MED-0004",
            "batchNumber": "P-2025-099", "arrivalDate": date(2025, 10, 5),
            "expirationDate": date(2027, 4, 30),
            "initialQuantity": 700, "availableQuantity": 620,
        },
        "BCH-005": {
            "id": "BCH-005", "medicationId": "MED-0005",
            "batchNumber": "P-2026-007", "arrivalDate": date(2026, 2, 1),
            "expirationDate": date(2027, 6, 1),
            "initialQuantity": 300, "availableQuantity": 240,
        },
        "BCH-006": {
            "id": "BCH-006", "medicationId": "MED-0007",
            "batchNumber": "P-2025-112", "arrivalDate": date(2025, 9, 15),
            "expirationDate": date(2027, 1, 31),
            "initialQuantity": 400, "availableQuantity": 350,
        },
        "BCH-007": {
            "id": "BCH-007", "medicationId": "MED-0006",
            "batchNumber": "P-2025-130", "arrivalDate": date(2025, 8, 10),
            "expirationDate": date(2026, 8, 10),
            "initialQuantity": 200, "availableQuantity": 50,
        },
    }

    
    STATE["prescriptions"] = {
        "R001": {
            "id": "R001", "doctorId": "USR-001", "patientId": "PAT-001",
            "emissionDate": date(2026, 4, 15),
            "pickupDeadline": date(2026, 6, 15),
            "treatmentType": "SHORT", "durationDays": 7,
            "status": "READY_FOR_PICKUP",
            "nextScheduledDelivery": None,
            "lines": [
                {"medicationId": "MED-0001", "dosesPerInterval": 1, "intervalHours": 8,
                 "doseDescription": "1 cápsula c/8h", "durationDays": 7, "totalQuantity": 21},
            ],
        },
        "R002": {
            "id": "R002", "doctorId": "USR-001", "patientId": "PAT-002",
            "emissionDate": date(2026, 5, 10),
            "pickupDeadline": date(2026, 7, 10),
            "treatmentType": "SHORT", "durationDays": 10,
            "status": "SUBMITTED",
            "lines": [
                {"medicationId": "MED-0003", "dosesPerInterval": 1, "intervalHours": 12,
                 "doseDescription": "1 cápsula c/12h", "durationDays": 10, "totalQuantity": 20},
            ],
        },
        "R003": {
            "id": "R003", "doctorId": "USR-001", "patientId": "PAT-003",
            "emissionDate": date(2026, 5, 5),
            "pickupDeadline": date(2026, 7, 5),
            "treatmentType": "SHORT", "durationDays": 14,
            "status": "READY_FOR_PICKUP",
            "lines": [
                {"medicationId": "MED-0004", "dosesPerInterval": 1, "intervalHours": 24,
                 "doseDescription": "1 cápsula c/24h", "durationDays": 14, "totalQuantity": 14},
            ],
        },
        "R004": {
            "id": "R004", "doctorId": "USR-001", "patientId": "PAT-004",
            "emissionDate": date(2026, 5, 12),
            "pickupDeadline": date(2026, 7, 12),
            "treatmentType": "LONG", "durationDays": 90,
            "status": "SUBMITTED",
            "nextScheduledDelivery": date(2026, 6, 12),
            "lines": [
                {"medicationId": "MED-0007", "dosesPerInterval": 1, "intervalHours": 24,
                 "doseDescription": "1 comp c/24h", "durationDays": 30, "totalQuantity": 30},
            ],
        },
        "R045": {
            "id": "R045", "doctorId": "USR-001", "patientId": "PAT-001",
            "emissionDate": date(2026, 5, 2),
            "pickupDeadline": date(2026, 7, 2),
            "treatmentType": "LONG", "durationDays": 90,
            "status": "RESERVED",
            "nextScheduledDelivery": date(2026, 6, 2),
            "lines": [
                {"medicationId": "MED-0005", "dosesPerInterval": 1, "intervalHours": 12,
                 "doseDescription": "1 comp c/12h", "durationDays": 30, "totalQuantity": 60},
            ],
        },
        "R012": {
            "id": "R012", "doctorId": "USR-001", "patientId": "PAT-001",
            "emissionDate": date(2026, 4, 15),
            "pickupDeadline": date(2026, 5, 15),
            "treatmentType": "SHORT", "durationDays": 5,
            "status": "PICKED_UP",
            "lines": [
                {"medicationId": "MED-0002", "dosesPerInterval": 1, "intervalHours": 8,
                 "doseDescription": "1 comp c/8h", "durationDays": 5, "totalQuantity": 15},
            ],
        },
        "R987": {
            "id": "R987", "doctorId": "USR-003", "patientId": "PAT-001",
            "emissionDate": date(2025, 12, 10),
            "pickupDeadline": date(2026, 1, 10),
            "treatmentType": "SHORT", "durationDays": 7,
            "status": "PICKED_UP",
            "lines": [
                {"medicationId": "MED-0003", "dosesPerInterval": 1, "intervalHours": 12,
                 "doseDescription": "1 cápsula c/12h", "durationDays": 7, "totalQuantity": 14},
            ],
        },
    }

    
    STATE["notifications"] = {
        "NTF-001": {
            "id": "NTF-001", "type": "EMAIL", "event": "RESERVATION_AVAILABLE",
            "recipientPatientId": "PAT-001", "recipientGuardianId": None,
            "message": "Su medicamento Paracetamol 500mg está disponible para retiro.",
            "sentAt": "2026-05-19T10:23:00", "status": "SENT",
            "prescriptionId": "R001",
        },
    }

    
_seed()


