from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from inventory_service.schemas import BatchWriteOff
from inventory_service.seed import STATE, next_id
from shared.auth import current_user
from shared.envelope import ok

router = APIRouter(prefix="/api/v1/batches", tags=["Partidas"])


@router.post("/{batch_id}/write-off")
def write_off(batch_id: str, body: BatchWriteOff, user: dict = Depends(current_user)):
    """Da de baja unidades de una partida + persiste WriteOff con motivo, qty y staff."""
    batch = STATE["batches"].get(batch_id)
    if not batch:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Partida no encontrada"})
    if body.quantity > batch["availableQuantity"]:
        raise HTTPException(409, detail={
            "code": "INSUFFICIENT_STOCK",
            "message": f"Cantidad solicitada ({body.quantity}) excede disponible ({batch['availableQuantity']})",
        })

    med = STATE["medications"].get(batch["medicationId"])
    batch["availableQuantity"] -= body.quantity
    if med:
        med["stock"]["availableQuantity"] -= body.quantity
        if body.discard:
            med["stock"]["physicalQuantity"] -= body.quantity

    today = date.today()
    wof_id = next_id("WOF")
    STATE["writeOffs"][wof_id] = {
        "id": wof_id,
        "batchId": batch_id,
        "medicationId": batch["medicationId"],
        "staffId": user["id"],
        "reason": body.reason.value if hasattr(body.reason, "value") else body.reason,
        "quantity": body.quantity,
        "status": "DISCARDED" if body.discard else "DEDUCTED_FROM_AVAILABLE",
        "expiredAt": today.isoformat(),
        "discardDate": today.isoformat() if body.discard else None,
        "notes": body.notes,
    }
    return ok(batch)
