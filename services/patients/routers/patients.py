from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from services.patients.schemas.patient import (
    Patient,
    PatientUpdate,
    PatientSummary,
    Guardian,
    GuardianCreate,
    PatientHistory,
)
from services.patients.schemas.common import MessageResponse
from data import STATE, next_id
from services.common.deps import current_user, pagination_params, paginate

router = APIRouter(prefix="/api/v1/patients", tags=["Pacientes"])


def _hydrate_patient(p: dict) -> dict:
    """Devuelve el paciente con su lista de apoderados embebida."""
    out = dict(p)
    out["guardians"] = [g for g in STATE["guardians"].values() if g["patientId"] == p["id"]]
    return out


@router.get("")
def list_patients(
    search: Optional[str] = None,
    page_limit: tuple[int, int] = Depends(pagination_params),
    _: dict = Depends(current_user),
):
    page, limit = page_limit
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
    return paginate(items, page, limit)


@router.get("/recent", response_model=list[PatientSummary])
def recent_patients(limit: int = 5, _: dict = Depends(current_user)):
    """Pacientes recientes (heurística por id — los más nuevos primero)."""
    items = sorted(STATE["patients"].values(), key=lambda p: p["id"], reverse=True)[:limit]
    return items


@router.get("/{patient_id}", response_model=Patient)
def get_patient(patient_id: str, _: dict = Depends(current_user)):
    p = STATE["patients"].get(patient_id)
    if not p:
        raise HTTPException(404, detail={"error": {"code": "NOT_FOUND", "message": "Paciente no encontrado"}})
    return _hydrate_patient(p)


@router.put("/{patient_id}", response_model=Patient)
def update_patient(patient_id: str, body: PatientUpdate, _: dict = Depends(current_user)):
    p = STATE["patients"].get(patient_id)
    if not p:
        raise HTTPException(404, detail={"error": {"code": "NOT_FOUND", "message": "Paciente no encontrado"}})
    for k, v in body.model_dump(exclude_unset=True).items():
        p[k] = v
    return _hydrate_patient(p)


@router.get("/{patient_id}/history", response_model=PatientHistory)
def patient_history(patient_id: str, _: dict = Depends(current_user)):
    p = STATE["patients"].get(patient_id)
    if not p:
        raise HTTPException(404, detail={"error": {"code": "NOT_FOUND", "message": "Paciente no encontrado"}})
    prescriptions = [r for r in STATE["prescriptions"].values() if r["patientId"] == patient_id]
    active = {"SUBMITTED", "RESERVED", "READY_FOR_PICKUP"}
    return {
        "patient": _hydrate_patient(p),
        "activePrescriptions": [r for r in prescriptions if r["status"] in active],
        "fullHistory": sorted(prescriptions, key=lambda r: r["emissionDate"], reverse=True),
    }


 
@router.get("/{patient_id}/guardians", response_model=list[Guardian])
def list_guardians(patient_id: str, _: dict = Depends(current_user)):
    if patient_id not in STATE["patients"]:
        raise HTTPException(404, detail={"error": {"code": "NOT_FOUND", "message": "Paciente no encontrado"}})
    return [g for g in STATE["guardians"].values() if g["patientId"] == patient_id]


@router.post("/{patient_id}/guardians", response_model=Guardian, status_code=status.HTTP_201_CREATED)
def add_guardian(patient_id: str, body: GuardianCreate, _: dict = Depends(current_user)):
    if patient_id not in STATE["patients"]:
        raise HTTPException(404, detail={"error": {"code": "NOT_FOUND", "message": "Paciente no encontrado"}})
    new_id = next_id("GRD")
    rec = {"id": new_id, "patientId": patient_id, **body.model_dump()}
    STATE["guardians"][new_id] = rec
    return rec


@router.delete("/{patient_id}/guardians/{guardian_id}", response_model=MessageResponse)
def remove_guardian(patient_id: str, guardian_id: str, _: dict = Depends(current_user)):
    g = STATE["guardians"].get(guardian_id)
    if not g or g["patientId"] != patient_id:
        raise HTTPException(404, detail={"error": {"code": "NOT_FOUND", "message": "Apoderado no encontrado"}})
    del STATE["guardians"][guardian_id]
    return {"message": f"Apoderado {guardian_id} eliminado"}
