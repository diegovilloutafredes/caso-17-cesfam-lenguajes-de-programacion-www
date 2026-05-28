"""Seed local de PatientService. Solo conoce patients + guardians."""

from datetime import date
from itertools import count
from typing import Any, Dict

STATE: Dict[str, Dict[str, Any]] = {
    "patients": {
        "PAT-001": {
            "id": "PAT-001", "rut": "12.345.678-9",
            "firstName": "María", "lastName": "González González",
            "birthDate": date(1955, 8, 12), "address": "Calle BKN 1543, Limache",
            "phone": "+56 9 1234 9300", "email": "maria70@gmail.com",
            "patientCard": {"number": "CP-2024-12345", "issueDate": date(2024, 3, 15)},
        },
        "PAT-002": {
            "id": "PAT-002", "rut": "23.456.789-0",
            "firstName": "Carlos", "lastName": "Ramírez",
            "birthDate": date(1968, 2, 4), "address": "Av. Central 234, Limache",
            "phone": "+56 9 8888 7777", "email": "carlos.ramirez@correo.cl",
            "patientCard": {"number": "CP-2024-23456", "issueDate": date(2024, 4, 2)},
        },
        "PAT-003": {
            "id": "PAT-003", "rut": "34.567.890-1",
            "firstName": "Ana", "lastName": "Martínez",
            "birthDate": date(1972, 11, 23), "address": "Pasaje 12 #43, Quillota",
            "phone": "+56 9 7777 6666", "email": "ana.martinez@correo.cl",
            "patientCard": {"number": "CP-2024-34567", "issueDate": date(2024, 5, 10)},
        },
        "PAT-004": {
            "id": "PAT-004", "rut": "45.678.901-2",
            "firstName": "Pedro", "lastName": "Silva",
            "birthDate": date(1980, 7, 17), "address": "Calle Los Olivos 88, Limache",
            "phone": "+56 9 6666 5555", "email": "pedro.silva@correo.cl",
            "patientCard": {"number": "CP-2024-45678", "issueDate": date(2024, 6, 1)},
        },
        "PAT-005": {
            "id": "PAT-005", "rut": "13.464.215-7",
            "firstName": "Gustavo", "lastName": "González González",
            "birthDate": date(1958, 4, 22), "address": "Calle BKN 1543, Limache",
            "phone": "+56 9 1234 9301", "email": "gustavo@correo.cl",
            "patientCard": {"number": "CP-2024-13464", "issueDate": date(2024, 3, 15)},
        },
    },
    "guardians": {
        "GRD-001": {
            "id": "GRD-001", "patientId": "PAT-001",
            "rut": "18.434.915-K", "firstName": "Pedri", "lastName": "González",
            "phone": "+56 9 2222 1111", "email": "pedri@correo.cl",
            "relationship": "Hijo", "authorizationDate": date(2024, 9, 12),
        },
        "GRD-002": {
            "id": "GRD-002", "patientId": "PAT-001",
            "rut": "13.464.215-7", "firstName": "Gustavo", "lastName": "González",
            "phone": "+56 9 1234 9301", "email": "gustavo@correo.cl",
            "relationship": "Esposo", "authorizationDate": date(2023, 5, 4),
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
