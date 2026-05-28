"""Seed local de IdentityService. Solo conoce sus propios users."""

from typing import Dict

USERS: Dict[str, dict] = {
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
