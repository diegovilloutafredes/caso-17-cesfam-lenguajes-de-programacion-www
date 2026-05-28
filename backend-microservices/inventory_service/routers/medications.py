from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from inventory_service.schemas import (
    BatchCreate, ConsumeRequest, StockReleaseRequest, StockReserveRequest,
)
from inventory_service.seed import STATE, next_id
from shared.auth import current_user
from shared.envelope import created, ok

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
    page: int = 1,
    limit: int = 20,
    _: dict = Depends(current_user),
):
    items = list(STATE["medications"].values())
    if search:
        q = search.lower()
        items = [m for m in items
                 if q in m["description"].lower()
                 or q in m["manufacturer"].lower()
                 or q in m["code"].lower()]
    total = len(items)
    start = max(0, (page - 1) * limit)
    return ok({
        "data": items[start : start + limit],
        "pagination": {
            "page": page, "limit": limit, "total": total,
            "totalPages": (total + limit - 1) // limit if total else 0,
        },
    })


@router.get("/stock-summary")
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
    return ok({
        "available": available, "lowStock": low,
        "outOfStock": out, "totalMedications": len(STATE["medications"]),
    })


@router.get("/low-stock")
def low_stock(_: dict = Depends(current_user)):
    return ok([
        {**m, "status": _stock_status(m)}
        for m in STATE["medications"].values()
        if _stock_status(m) != "AVAILABLE"
    ])


@router.get("/{medication_id}")
def get_medication(medication_id: str, _: dict = Depends(current_user)):
    m = STATE["medications"].get(medication_id)
    if not m:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Medicamento no encontrado"})
    batches = [b for b in STATE["batches"].values() if b["medicationId"] == medication_id]
    return ok({**m, "batches": batches})


@router.get("/{medication_id}/batches")
def list_batches(medication_id: str, _: dict = Depends(current_user)):
    if medication_id not in STATE["medications"]:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Medicamento no encontrado"})
    return ok([b for b in STATE["batches"].values() if b["medicationId"] == medication_id])


@router.post("/{medication_id}/batches", status_code=status.HTTP_201_CREATED)
def add_batch(medication_id: str, body: BatchCreate, _: dict = Depends(current_user)):
    med = STATE["medications"].get(medication_id)
    if not med:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Medicamento no encontrado"})
    new_id = next_id("BCH")
    rec = {
        "id": new_id, "medicationId": medication_id,
        "arrivalDate": date.today().isoformat(),
        "availableQuantity": body.initialQuantity,
        **body.model_dump(mode="json"),
    }
    STATE["batches"][new_id] = rec
    med["stock"]["availableQuantity"] += body.initialQuantity
    med["stock"]["physicalQuantity"] += body.initialQuantity
    return created(rec)


# --- Inter-service operations ---

@router.post("/{medication_id}/reserve")
def reserve_stock(medication_id: str, body: StockReserveRequest, _: dict = Depends(current_user)):
    """Mueve `quantity` de available → reserved. Llamado por PrescriptionService."""
    med = STATE["medications"].get(medication_id)
    if not med:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Medicamento no encontrado"})
    if med["stock"]["availableQuantity"] < body.quantity:
        raise HTTPException(409, detail={
            "code": "INSUFFICIENT_STOCK",
            "message": f"Stock disponible ({med['stock']['availableQuantity']}) menor a solicitado ({body.quantity})",
        })
    med["stock"]["availableQuantity"] -= body.quantity
    med["stock"]["reservedQuantity"] += body.quantity
    return ok({"medicationId": medication_id, "reservedQuantity": body.quantity})


@router.post("/{medication_id}/release")
def release_stock(medication_id: str, body: StockReleaseRequest, _: dict = Depends(current_user)):
    """Mueve `quantity` de reserved → available. Llamado por PrescriptionService al cancelar."""
    med = STATE["medications"].get(medication_id)
    if not med:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Medicamento no encontrado"})
    qty = min(body.quantity, med["stock"]["reservedQuantity"])
    med["stock"]["reservedQuantity"] -= qty
    med["stock"]["availableQuantity"] += qty
    return ok({"medicationId": medication_id, "releasedQuantity": qty})


@router.post("/consume")
def consume_physical(body: ConsumeRequest, _: dict = Depends(current_user)):
    """Decrementa physicalQuantity por asignaciones de batch. Llamado al entregar.

    **Atómico**: valida TODAS las partidas antes de mutar nada. Si alguna no existe,
    falla sin haber tocado ningún contador — previene corrupción parcial de stock.
    """
    # Fase 1: validación previa, ningún side-effect aún
    for alloc in body.allocations:
        if alloc.batchId not in STATE["batches"]:
            raise HTTPException(404, detail={
                "code": "BATCH_NOT_FOUND",
                "message": f"Partida no encontrada: {alloc.batchId}",
            })
    # Fase 2: mutación — ya tenemos garantía de que todas las partidas existen
    for alloc in body.allocations:
        batch = STATE["batches"][alloc.batchId]
        med = STATE["medications"].get(batch["medicationId"])
        if med:
            med["stock"]["physicalQuantity"] -= alloc.quantity
            med["stock"]["reservedQuantity"] = max(0, med["stock"]["reservedQuantity"] - alloc.quantity)
        batch["availableQuantity"] = max(0, batch["availableQuantity"] - alloc.quantity)
    return ok({"consumed": len(body.allocations)})
