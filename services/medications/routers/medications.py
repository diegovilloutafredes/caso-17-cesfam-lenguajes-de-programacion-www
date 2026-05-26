from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from services.medications.schemas.medication import (
    Medication,
    MedicationDetail,
    Batch,
    BatchCreate,
    StockSummary,
)
from data import STATE, next_id
from services.common.deps import current_user, pagination_params, paginate

router = APIRouter(prefix="/api/v1/medications", tags=["Medicamentos"])


def _stock_status(med: dict) -> str:
    available = med["stock"]["availableQuantity"]
    if available == 0:
        return "OUT_OF_STOCK"
    if available < med["minStock"]:
        return "LOW_STOCK"
    return "AVAILABLE"


@router.get("")
def list_medications(
    search: Optional[str] = None,
    page_limit: tuple[int, int] = Depends(pagination_params),
    _: dict = Depends(current_user),
):
    page, limit = page_limit
    items = list(STATE["medications"].values())
    if search:
        q = search.lower()
        items = [
            m for m in items
            if q in m["description"].lower()
            or q in m["manufacturer"].lower()
            or q in m["code"].lower()
        ]
    return paginate(items, page, limit)


@router.get("/stock-summary", response_model=StockSummary)
def stock_summary(_: dict = Depends(current_user)):
    available = low = out = 0
    for m in STATE["medications"].values():
        s = _stock_status(m)
        if s == "AVAILABLE":
            available += 1
        elif s == "LOW_STOCK":
            low += 1
        else:
            out += 1
    return {
        "available": available,
        "lowStock": low,
        "outOfStock": out,
        "totalMedications": len(STATE["medications"]),
    }


@router.get("/low-stock", response_model=list[Medication])
def low_stock(_: dict = Depends(current_user)):
    return [m for m in STATE["medications"].values() if _stock_status(m) != "AVAILABLE"]


@router.get("/{medication_id}", response_model=MedicationDetail)
def get_medication(medication_id: str, _: dict = Depends(current_user)):
    m = STATE["medications"].get(medication_id)
    if not m:
        raise HTTPException(404, detail={"error": {"code": "NOT_FOUND", "message": "Medicamento no encontrado"}})
    batches = [b for b in STATE["batches"].values() if b["medicationId"] == medication_id]
    return {**m, "batches": batches}


@router.get("/{medication_id}/batches", response_model=list[Batch])
def list_batches(medication_id: str, _: dict = Depends(current_user)):
    if medication_id not in STATE["medications"]:
        raise HTTPException(404, detail={"error": {"code": "NOT_FOUND", "message": "Medicamento no encontrado"}})
    return [b for b in STATE["batches"].values() if b["medicationId"] == medication_id]


@router.post("/{medication_id}/batches", response_model=Batch, status_code=status.HTTP_201_CREATED)
def add_batch(medication_id: str, body: BatchCreate, _: dict = Depends(current_user)):
    med = STATE["medications"].get(medication_id)
    if not med:
        raise HTTPException(404, detail={"error": {"code": "NOT_FOUND", "message": "Medicamento no encontrado"}})
    new_id = next_id("BCH")
    rec = {
        "id": new_id,
        "medicationId": medication_id,
        "arrivalDate": date.today(),
        "availableQuantity": body.initialQuantity,
        **body.model_dump(),
    }
    STATE["batches"][new_id] = rec
    med["stock"]["availableQuantity"] += body.initialQuantity
    med["stock"]["physicalQuantity"] += body.initialQuantity
    return rec
