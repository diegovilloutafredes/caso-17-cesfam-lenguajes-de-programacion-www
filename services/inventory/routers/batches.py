from datetime import date
from fastapi import APIRouter, Depends, HTTPException

from services.inventory.schemas.inventory import Batch, BatchWriteOff
from data import STATE, next_id
from services.common.deps import current_user

router = APIRouter(prefix="/api/v1/batches", tags=["Partidas"])


@router.post("/{batch_id}/write-off", response_model=Batch)
def write_off(batch_id: str, body: BatchWriteOff, user: dict = Depends(current_user)):
    """Da de baja unidades de una partida. Descuenta availableQuantity siempre;
    descuenta physicalQuantity solo cuando discard=true (requerimiento de auditoría).
    Persiste un registro WriteOff con motivo, cantidad, partida, medicamento y staff."""
    batch = STATE["batches"].get(batch_id)
    if not batch:
        raise HTTPException(404, detail={"error": {"code": "NOT_FOUND", "message": "Partida no encontrada"}})
    if body.quantity > batch["availableQuantity"]:
        raise HTTPException(
            409,
            detail={"error": {"code": "INSUFFICIENT_STOCK",
                              "message": f"Cantidad solicitada ({body.quantity}) excede disponible ({batch['availableQuantity']})"}},
        )
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
        "expiredAt": today,
        "discardDate": today if body.discard else None,
        "notes": body.notes,
    }
    return batch
