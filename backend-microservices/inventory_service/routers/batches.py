from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from inventory_service.db import get_session
from inventory_service.models import Batch, Medication, WriteOff
from inventory_service.schemas import BatchWriteOff
from inventory_service.seed import next_id
from shared.auth import current_user
from shared.envelope import ok

router = APIRouter(prefix="/api/v1/batches", tags=["Partidas"])


def _serialize_batch(batch: Batch) -> dict:
    return {
        "id": batch.id,
        "medicationId": batch.medicationId,
        "batchNumber": batch.batchNumber,
        "arrivalDate": batch.arrivalDate,
        "expirationDate": batch.expirationDate,
        "initialQuantity": batch.initialQuantity,
        "availableQuantity": batch.availableQuantity,
    }


@router.post("/{batch_id}/write-off")
def write_off(
    batch_id: str,
    body: BatchWriteOff,
    db: Session = Depends(get_session),
    user: dict = Depends(current_user),
):
    """Da de baja unidades de una partida + persiste WriteOff con motivo, qty y staff."""
    batch = db.execute(
        select(Batch).where(Batch.id == batch_id).with_for_update()
    ).scalar_one_or_none()
    if not batch:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Partida no encontrada"})
    if body.quantity > batch.availableQuantity:
        raise HTTPException(409, detail={
            "code": "INSUFFICIENT_STOCK",
            "message": f"Cantidad solicitada ({body.quantity}) excede disponible ({batch.availableQuantity})",
        })

    med = db.execute(
        select(Medication).where(Medication.id == batch.medicationId).with_for_update()
    ).scalar_one_or_none()
    batch.availableQuantity -= body.quantity
    if med:
        med.availableQuantity -= body.quantity
        if body.discard:
            med.physicalQuantity -= body.quantity

    today = date.today()
    wof_id = next_id(db, "WOF")
    db.add(WriteOff(
        id=wof_id,
        batchId=batch_id,
        medicationId=batch.medicationId,
        staffId=user["id"],
        reason=body.reason.value if hasattr(body.reason, "value") else body.reason,
        quantity=body.quantity,
        status="DISCARDED" if body.discard else "DEDUCTED_FROM_AVAILABLE",
        expiredAt=today.isoformat(),
        discardDate=today.isoformat() if body.discard else None,
        notes=body.notes,
    ))
    db.commit()
    return ok(_serialize_batch(batch))
