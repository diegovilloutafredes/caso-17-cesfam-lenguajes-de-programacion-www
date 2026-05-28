from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from patient_service.clients.prescription import PrescriptionServiceClient
from patient_service.schemas import (
    Guardian, GuardianCreate, Patient, PatientSummary, PatientUpdate,
)
from patient_service.seed import STATE, next_id
from shared.auth import current_token, current_user
from shared.envelope import created, ok

prescription_client = PrescriptionServiceClient()

router = APIRouter(prefix="/api/v1/patients", tags=["Pacientes"])


def _hydrate(p: dict) -> dict:
    out = dict(p)
    out["guardians"] = [g for g in STATE["guardians"].values() if g["patientId"] == p["id"]]
    return out


@router.get("")
def list_patients(
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    _: dict = Depends(current_user),
):
    items = list(STATE["patients"].values())
    if search:
        q = search.lower()
        items = [
            p for p in items
            if q in p["firstName"].lower()
            or q in p["lastName"].lower()
            or q in p["rut"]
        ]
    items = sorted(items, key=lambda p: (p["lastName"], p["firstName"]))
    total = len(items)
    start = max(0, (page - 1) * limit)
    page_items = items[start : start + limit]
    return ok({
        "data": page_items,
        "pagination": {
            "page": page, "limit": limit, "total": total,
            "totalPages": (total + limit - 1) // limit if total else 0,
        },
    })


@router.get("/recent")
def recent_patients(limit: int = 5, _: dict = Depends(current_user)):
    items = sorted(STATE["patients"].values(), key=lambda p: p["id"], reverse=True)[:limit]
    return ok([
        {"id": p["id"], "rut": p["rut"], "firstName": p["firstName"], "lastName": p["lastName"]}
        for p in items
    ])


@router.get("/{patient_id}")
def get_patient(patient_id: str, _: dict = Depends(current_user)):
    p = STATE["patients"].get(patient_id)
    if not p:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Paciente no encontrado"})
    return ok(_hydrate(p))


@router.put("/{patient_id}")
def update_patient(patient_id: str, body: PatientUpdate, _: dict = Depends(current_user)):
    p = STATE["patients"].get(patient_id)
    if not p:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Paciente no encontrado"})
    for k, v in body.model_dump(exclude_unset=True).items():
        p[k] = v
    return ok(_hydrate(p))


@router.get("/{patient_id}/history")
def get_history(
    patient_id: str,
    _user: dict = Depends(current_user),
    token: str = Depends(current_token),
):
    """Historial de medicamentos del paciente (la "Libreta de medicamentos" virtual).

    Cross-service: combina datos locales del paciente con prescripciones que viven
    en prescription_service. Si prescription_service está caído, retorna patient
    con listas vacías (degradación graceful via best-effort).
    """
    p = STATE["patients"].get(patient_id)
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
def list_guardians(patient_id: str, _: dict = Depends(current_user)):
    if patient_id not in STATE["patients"]:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Paciente no encontrado"})
    return ok([g for g in STATE["guardians"].values() if g["patientId"] == patient_id])


@router.post("/{patient_id}/guardians", status_code=status.HTTP_201_CREATED)
def add_guardian(patient_id: str, body: GuardianCreate, _: dict = Depends(current_user)):
    if patient_id not in STATE["patients"]:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Paciente no encontrado"})
    new_id = next_id("GRD")
    rec = {"id": new_id, "patientId": patient_id, **body.model_dump(mode="json")}
    STATE["guardians"][new_id] = rec
    return created(rec)


@router.delete("/{patient_id}/guardians/{guardian_id}")
def remove_guardian(patient_id: str, guardian_id: str, _: dict = Depends(current_user)):
    g = STATE["guardians"].get(guardian_id)
    if not g or g["patientId"] != patient_id:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Apoderado no encontrado"})
    del STATE["guardians"][guardian_id]
    return ok({"message": f"Apoderado {guardian_id} eliminado"})
