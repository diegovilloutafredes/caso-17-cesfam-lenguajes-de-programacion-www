from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from patient_service.clients.prescription import PrescriptionServiceClient
from patient_service.db import get_session
from patient_service.models import Guardian, Patient
from patient_service.schemas import GuardianCreate, PatientUpdate
from patient_service.seed import next_id
from shared.auth import current_token, current_user
from shared.envelope import created, ok

prescription_client = PrescriptionServiceClient()

router = APIRouter(prefix="/api/v1/patients", tags=["Pacientes"])


def _serialize_guardian(g: Guardian) -> dict:
    return {
        "id": g.id,
        "patientId": g.patientId,
        "rut": g.rut,
        "firstName": g.firstName,
        "lastName": g.lastName,
        "phone": g.phone,
        "email": g.email,
        "relationship": g.relationship_,
        "authorizationDate": g.authorizationDate,
    }


def _serialize_patient(p: Patient) -> dict:
    """Paciente SIN guardians (lista). PatientCard embebido → objeto anidado."""
    out = {
        "id": p.id,
        "rut": p.rut,
        "firstName": p.firstName,
        "lastName": p.lastName,
        "birthDate": p.birthDate,
        "address": p.address,
        "phone": p.phone,
        "email": p.email,
    }
    if p.patientCardNumber is not None:
        out["patientCard"] = {
            "number": p.patientCardNumber,
            "issueDate": p.patientCardIssueDate,
        }
    else:
        out["patientCard"] = None
    return out


def _hydrate(p: Patient) -> dict:
    out = _serialize_patient(p)
    out["guardians"] = [_serialize_guardian(g) for g in p.guardians]
    return out


@router.get("")
def list_patients(
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    _: dict = Depends(current_user),
    db: Session = Depends(get_session),
):
    items = list(db.execute(select(Patient)).scalars().all())
    if search:
        q = search.lower()
        items = [
            p for p in items
            if q in p.firstName.lower()
            or q in p.lastName.lower()
            or q in p.rut
        ]
    items = sorted(items, key=lambda p: (p.lastName, p.firstName))
    total = len(items)
    start = max(0, (page - 1) * limit)
    page_items = items[start : start + limit]
    return ok({
        "data": [_serialize_patient(p) for p in page_items],
        "pagination": {
            "page": page, "limit": limit, "total": total,
            "totalPages": (total + limit - 1) // limit if total else 0,
        },
    })


@router.get("/recent")
def recent_patients(
    limit: int = 5,
    _: dict = Depends(current_user),
    db: Session = Depends(get_session),
):
    items = list(db.execute(select(Patient)).scalars().all())
    items = sorted(items, key=lambda p: p.id, reverse=True)[:limit]
    return ok([
        {"id": p.id, "rut": p.rut, "firstName": p.firstName, "lastName": p.lastName}
        for p in items
    ])


@router.get("/{patient_id}")
def get_patient(
    patient_id: str,
    _: dict = Depends(current_user),
    db: Session = Depends(get_session),
):
    p = db.get(Patient, patient_id)
    if not p:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Paciente no encontrado"})
    return ok(_hydrate(p))


@router.put("/{patient_id}")
def update_patient(
    patient_id: str,
    body: PatientUpdate,
    _: dict = Depends(current_user),
    db: Session = Depends(get_session),
):
    p = db.get(Patient, patient_id)
    if not p:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Paciente no encontrado"})
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    return ok(_hydrate(p))


@router.get("/{patient_id}/history")
def get_history(
    patient_id: str,
    _user: dict = Depends(current_user),
    token: str = Depends(current_token),
    db: Session = Depends(get_session),
):
    """Historial de medicamentos del paciente (la "Libreta de medicamentos" virtual).

    Cross-service: combina datos locales del paciente con prescripciones que viven
    en prescription_service. Si prescription_service está caído, retorna patient
    con listas vacías (degradación graceful via best-effort).
    """
    p = db.get(Patient, patient_id)
    if not p:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Paciente no encontrado"})

    presc_resp = prescription_client.list_for_patient(patient_id, token=token)
    prescriptions: list = []
    if not presc_resp.get("error"):
        data = presc_resp.get("data") or {}
        prescriptions = data.get("data", []) if isinstance(data, dict) else (data or [])

    active_states = {"SUBMITTED", "RESERVED", "READY_FOR_PICKUP"}
    return ok({
        "patient": _hydrate(p),
        "activePrescriptions": [r for r in prescriptions if r.get("status") in active_states],
        "fullHistory": sorted(prescriptions, key=lambda r: r.get("emissionDate", ""), reverse=True),
    })


@router.get("/{patient_id}/guardians")
def list_guardians(
    patient_id: str,
    _: dict = Depends(current_user),
    db: Session = Depends(get_session),
):
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Paciente no encontrado"})
    rows = db.execute(
        select(Guardian).where(Guardian.patientId == patient_id)
    ).scalars().all()
    return ok([_serialize_guardian(g) for g in rows])


@router.post("/{patient_id}/guardians", status_code=status.HTTP_201_CREATED)
def add_guardian(
    patient_id: str,
    body: GuardianCreate,
    _: dict = Depends(current_user),
    db: Session = Depends(get_session),
):
    if not db.get(Patient, patient_id):
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Paciente no encontrado"})
    new_id = next_id(db, "GRD")
    payload = body.model_dump(mode="json")
    g = Guardian(
        id=new_id,
        patientId=patient_id,
        rut=body.rut,
        firstName=body.firstName,
        lastName=body.lastName,
        phone=body.phone,
        email=body.email,
        relationship_=body.relationship,
        authorizationDate=body.authorizationDate,
    )
    db.add(g)
    db.commit()
    rec = {"id": new_id, "patientId": patient_id, **payload}
    return created(rec)


@router.delete("/{patient_id}/guardians/{guardian_id}")
def remove_guardian(
    patient_id: str,
    guardian_id: str,
    _: dict = Depends(current_user),
    db: Session = Depends(get_session),
):
    g = db.get(Guardian, guardian_id)
    if not g or g.patientId != patient_id:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Apoderado no encontrado"})
    db.delete(g)
    db.commit()
    return ok({"message": f"Apoderado {guardian_id} eliminado"})
