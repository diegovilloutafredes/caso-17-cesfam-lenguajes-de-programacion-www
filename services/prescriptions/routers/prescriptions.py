from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from services.prescriptions.schemas.prescription import (
    Prescription,
    PrescriptionDetail,
    PrescriptionCreate,
    DeliverRequest,
    ExternalPurchaseRequest,
    CancelRequest,
)
from data import STATE, next_id
from services.common.deps import current_user, pagination_params, paginate

router = APIRouter(prefix="/api/v1/prescriptions", tags=["Recetas"])

ACTIVE_STATES = {"SUBMITTED", "RESERVED", "READY_FOR_PICKUP"}
TERMINAL_STATES = {"PICKED_UP", "CANCELLED", "EXPIRED", "EXTERNAL_PURCHASE"}


def _hydrate(r: dict) -> dict:
    """Agrega nombres de paciente y médico al detalle de la receta."""
    pat = STATE["patients"].get(r["patientId"], {})
    doc = STATE["users"].get(r["doctorId"], {})
    return {
        **r,
        "patientFullName": f"{pat.get('firstName','')} {pat.get('lastName','')}".strip(),
        "patientRut": pat.get("rut", ""),
        "doctorFullName": doc.get("fullName", ""),
    }


def _ensure_status(r: dict, allowed: set[str], action: str) -> None:
    if r["status"] not in allowed:
        raise HTTPException(
            409,
            detail={"error": {"code": "INVALID_STATE",
                              "message": f"No se puede {action} la receta en estado {r['status']}"}},
        )


@router.get("")
def list_prescriptions(
    status_filter: Optional[str] = None,
    patientId: Optional[str] = None,
    page_limit: tuple[int, int] = Depends(pagination_params),
    _: dict = Depends(current_user),
):
    """Lista recetas. status_filter acepta valores separados por coma: ?status_filter=SUBMITTED,RESERVED"""
    page, limit = page_limit
    items = list(STATE["prescriptions"].values())
    if status_filter:
        wanted = {s.strip() for s in status_filter.split(",")}
        items = [r for r in items if r["status"] in wanted]
    if patientId:
        items = [r for r in items if r["patientId"] == patientId]
    items = sorted(items, key=lambda r: r["emissionDate"], reverse=True)
    return paginate(items, page, limit)


@router.get("/queue", response_model=list[Prescription])
def queue(_: dict = Depends(current_user)):
    """Recetas pendientes de preparación (SUBMITTED + RESERVED)."""
    items = [r for r in STATE["prescriptions"].values() if r["status"] in {"SUBMITTED", "RESERVED"}]
    return sorted(items, key=lambda r: r["emissionDate"])


@router.get("/{prescription_id}", response_model=PrescriptionDetail)
def get_prescription(prescription_id: str, _: dict = Depends(current_user)):
    r = STATE["prescriptions"].get(prescription_id)
    if not r:
        raise HTTPException(404, detail={"error": {"code": "NOT_FOUND", "message": "Receta no encontrada"}})
    return _hydrate(r)


@router.post("", response_model=PrescriptionDetail, status_code=status.HTTP_201_CREATED)
def create_prescription(body: PrescriptionCreate, user: dict = Depends(current_user)):
    if body.patientId not in STATE["patients"]:
        raise HTTPException(404, detail={"error": {"code": "NOT_FOUND", "message": "Paciente no encontrado"}})
    new_id = next_id("R")
    rec = {
        "id": new_id,
        "doctorId": user["id"],
        "patientId": body.patientId,
        "emissionDate": date.today(),
        "pickupDeadline": body.pickupDeadline,
        "treatmentType": body.treatmentType.value if hasattr(body.treatmentType, "value") else body.treatmentType,
        "durationDays": body.durationDays,
        "status": "SUBMITTED",
        "nextScheduledDelivery": None,
        "lines": [d.model_dump() for d in body.lines],
    }
    STATE["prescriptions"][new_id] = rec
    return _hydrate(rec)


 
@router.post("/{prescription_id}/prepare", response_model=Prescription)
def prepare(prescription_id: str, _: dict = Depends(current_user)):
    """Mueve SUBMITTED → READY_FOR_PICKUP si hay stock disponible."""
    r = STATE["prescriptions"].get(prescription_id)
    if not r:
        raise HTTPException(404, detail={"error": {"code": "NOT_FOUND", "message": "Receta no encontrada"}})
    _ensure_status(r, {"SUBMITTED"}, "prepare")

    insufficient = []
    for line in r["lines"]:
        med = STATE["medications"].get(line["medicationId"])
        if not med or med["stock"]["availableQuantity"] < line["totalQuantity"]:
            insufficient.append(line["medicationId"])

    if insufficient:
        raise HTTPException(
            409,
            detail={"error": {"code": "INSUFFICIENT_STOCK",
                              "message": "Stock insuficiente. Usar /reserve o /external-purchase.",
                              "details": {"medicationIds": insufficient}}},
        )

    for line in r["lines"]:
        med = STATE["medications"][line["medicationId"]]
        med["stock"]["availableQuantity"] -= line["totalQuantity"]
        med["stock"]["reservedQuantity"] += line["totalQuantity"]
    r["status"] = "READY_FOR_PICKUP"
    return r


@router.post("/{prescription_id}/reserve", response_model=Prescription)
def reserve(prescription_id: str, _: dict = Depends(current_user)):
    r = STATE["prescriptions"].get(prescription_id)
    if not r:
        raise HTTPException(404, detail={"error": {"code": "NOT_FOUND", "message": "Receta no encontrada"}})
    _ensure_status(r, {"SUBMITTED"}, "reserve")
    r["status"] = "RESERVED"
    return r


@router.post("/{prescription_id}/mark-available", response_model=Prescription)
def mark_available(prescription_id: str, _: dict = Depends(current_user)):
    """RESERVED → READY_FOR_PICKUP (se dispara cuando llega stock)."""
    r = STATE["prescriptions"].get(prescription_id)
    if not r:
        raise HTTPException(404, detail={"error": {"code": "NOT_FOUND", "message": "Receta no encontrada"}})
    _ensure_status(r, {"RESERVED"}, "mark-available")
    r["status"] = "READY_FOR_PICKUP"
    return r


@router.post("/{prescription_id}/external-purchase", response_model=Prescription)
def external_purchase(prescription_id: str, body: ExternalPurchaseRequest, _: dict = Depends(current_user)):
    r = STATE["prescriptions"].get(prescription_id)
    if not r:
        raise HTTPException(404, detail={"error": {"code": "NOT_FOUND", "message": "Receta no encontrada"}})
    _ensure_status(r, {"SUBMITTED"}, "external-purchase")
    r["status"] = "EXTERNAL_PURCHASE"
    r["externalPurchaseNotes"] = body.notes
    return r


@router.post("/{prescription_id}/cancel", response_model=Prescription)
def cancel(prescription_id: str, body: CancelRequest, _: dict = Depends(current_user)):
    r = STATE["prescriptions"].get(prescription_id)
    if not r:
        raise HTTPException(404, detail={"error": {"code": "NOT_FOUND", "message": "Receta no encontrada"}})
    if r["status"] in TERMINAL_STATES:
        raise HTTPException(
            409,
            detail={"error": {"code": "INVALID_STATE", "message": f"Receta ya en estado terminal: {r['status']}"}},
        )
    if r["status"] in {"RESERVED", "READY_FOR_PICKUP"}:
        for line in r["lines"]:
            med = STATE["medications"].get(line["medicationId"])
            if med and r["status"] == "READY_FOR_PICKUP":
                med["stock"]["availableQuantity"] += line["totalQuantity"]
                med["stock"]["reservedQuantity"] -= line["totalQuantity"]
    r["status"] = "CANCELLED"
    r["cancelReason"] = body.reason
    return r


@router.post("/{prescription_id}/deliver", response_model=Prescription)
def deliver(prescription_id: str, body: DeliverRequest, _: dict = Depends(current_user)):
    """Registra la entrega: quién retira + qué partidas se usan."""
    r = STATE["prescriptions"].get(prescription_id)
    if not r:
        raise HTTPException(404, detail={"error": {"code": "NOT_FOUND", "message": "Receta no encontrada"}})
    _ensure_status(r, {"READY_FOR_PICKUP"}, "deliver")

    if body.pickerType == "guardian":
        if not body.guardianId or body.guardianId not in STATE["guardians"]:
            raise HTTPException(400, detail={"error": {"code": "INVALID_GUARDIAN", "message": "Apoderado inválido"}})
    elif body.pickerType == "third_party":
        if not body.thirdPartyRut or not body.thirdPartyName:
            raise HTTPException(400, detail={"error": {"code": "MISSING_THIRD_PARTY",
                                                       "message": "thirdPartyRut y thirdPartyName son requeridos"}})

    for alloc in body.batches:
        b = STATE["batches"].get(alloc.batchId)
        if not b:
            raise HTTPException(404, detail={"error": {"code": "BATCH_NOT_FOUND", "message": f"Partida no encontrada: {alloc.batchId}"}})
        med = STATE["medications"].get(b["medicationId"])
        if med:
            med["stock"]["physicalQuantity"] -= alloc.quantity
            med["stock"]["reservedQuantity"] = max(0, med["stock"]["reservedQuantity"] - alloc.quantity)
        b["availableQuantity"] = max(0, b["availableQuantity"] - alloc.quantity)

    r["status"] = "PICKED_UP"
    r["delivery"] = {
        "pickerType": body.pickerType,
        "guardianId": body.guardianId,
        "thirdPartyRut": body.thirdPartyRut,
        "thirdPartyName": body.thirdPartyName,
        "batches": [a.model_dump() for a in body.batches],
        "deliveryDate": date.today().isoformat(),
    }
    return r
