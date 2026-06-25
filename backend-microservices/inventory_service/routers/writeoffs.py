from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from inventory_service.db import get_session
from inventory_service.models import WriteOff
from shared.auth import current_user
from shared.envelope import ok

router = APIRouter(prefix="/api/v1/write-offs", tags=["Bajas"])


def _serialize_write_off(w: WriteOff) -> dict:
    return {
        "id": w.id,
        "batchId": w.batchId,
        "medicationId": w.medicationId,
        "staffId": w.staffId,
        "reason": w.reason,
        "quantity": w.quantity,
        "status": w.status,
        "expiredAt": w.expiredAt,
        "discardDate": w.discardDate,
        "notes": w.notes,
    }


@router.get("")
def list_write_offs(
    medicationId: Optional[str] = None,
    batchId: Optional[str] = None,
    status_filter: Optional[str] = None,
    dateFrom: Optional[date] = None,
    dateTo: Optional[date] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_session),
    _: dict = Depends(current_user),
):
    items = [_serialize_write_off(w) for w in db.execute(select(WriteOff)).scalars().all()]
    if medicationId:
        items = [w for w in items if w["medicationId"] == medicationId]
    if batchId:
        items = [w for w in items if w["batchId"] == batchId]
    if status_filter:
        wanted = {s.strip() for s in status_filter.split(",")}
        items = [w for w in items if w["status"] in wanted]
    if dateFrom:
        items = [w for w in items if w["expiredAt"] >= dateFrom.isoformat()]
    if dateTo:
        items = [w for w in items if w["expiredAt"] <= dateTo.isoformat()]
    items = sorted(items, key=lambda w: w["expiredAt"], reverse=True)
    total = len(items)
    start = max(0, (page - 1) * limit)
    return ok({
        "data": items[start : start + limit],
        "pagination": {
            "page": page, "limit": limit, "total": total,
            "totalPages": (total + limit - 1) // limit if total else 0,
        },
    })


@router.get("/{write_off_id}")
def get_write_off(
    write_off_id: str,
    db: Session = Depends(get_session),
    _: dict = Depends(current_user),
):
    w = db.get(WriteOff, write_off_id)
    if not w:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Baja no encontrada"})
    return ok(_serialize_write_off(w))
