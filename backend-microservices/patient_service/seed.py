"""Seed local de PatientService (PostgreSQL). Solo conoce patients + guardians."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from patient_service.db import SessionLocal
from patient_service.models import Guardian, Patient


def seed() -> None:
    db: Session = SessionLocal()
    try:
        if db.execute(select(func.count()).select_from(Patient)).scalar_one() > 0:
            return

        patients = [
            Patient(
                id="PAT-001", rut="12.345.678-9",
                firstName="María", lastName="González González",
                birthDate=date(1955, 8, 12), address="Calle BKN 1543, Limache",
                phone="+56 9 1234 9300", email="maria70@gmail.com",
                patientCardNumber="CP-2024-12345", patientCardIssueDate=date(2024, 3, 15),
            ),
            Patient(
                id="PAT-002", rut="23.456.789-0",
                firstName="Carlos", lastName="Ramírez",
                birthDate=date(1968, 2, 4), address="Av. Central 234, Limache",
                phone="+56 9 8888 7777", email="carlos.ramirez@correo.cl",
                patientCardNumber="CP-2024-23456", patientCardIssueDate=date(2024, 4, 2),
            ),
            Patient(
                id="PAT-003", rut="34.567.890-1",
                firstName="Ana", lastName="Martínez",
                birthDate=date(1972, 11, 23), address="Pasaje 12 #43, Quillota",
                phone="+56 9 7777 6666", email="ana.martinez@correo.cl",
                patientCardNumber="CP-2024-34567", patientCardIssueDate=date(2024, 5, 10),
            ),
            Patient(
                id="PAT-004", rut="45.678.901-2",
                firstName="Pedro", lastName="Silva",
                birthDate=date(1980, 7, 17), address="Calle Los Olivos 88, Limache",
                phone="+56 9 6666 5555", email="pedro.silva@correo.cl",
                patientCardNumber="CP-2024-45678", patientCardIssueDate=date(2024, 6, 1),
            ),
            Patient(
                id="PAT-005", rut="13.464.215-7",
                firstName="Gustavo", lastName="González González",
                birthDate=date(1958, 4, 22), address="Calle BKN 1543, Limache",
                phone="+56 9 1234 9301", email="gustavo@correo.cl",
                patientCardNumber="CP-2024-13464", patientCardIssueDate=date(2024, 3, 15),
            ),
        ]
        db.add_all(patients)

        guardians = [
            Guardian(
                id="GRD-001", patientId="PAT-001",
                rut="18.434.915-K", firstName="Pedri", lastName="González",
                phone="+56 9 2222 1111", email="pedri@correo.cl",
                relationship_="Hijo", authorizationDate=date(2024, 9, 12),
            ),
            Guardian(
                id="GRD-002", patientId="PAT-001",
                rut="13.464.215-7", firstName="Gustavo", lastName="González",
                phone="+56 9 1234 9301", email="gustavo@correo.cl",
                relationship_="Esposo", authorizationDate=date(2023, 5, 4),
            ),
        ]
        db.add_all(guardians)
        db.commit()
    finally:
        db.close()
