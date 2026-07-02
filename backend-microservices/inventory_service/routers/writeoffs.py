from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from inventory_service.db import get_session
from inventory_service.models import Medication, WriteOff
from shared.auth import current_user, require_role
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
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_session),
    _: dict = Depends(current_user),
):
    stmt = select(WriteOff)
    if medicationId:
        stmt = stmt.where(WriteOff.medicationId == medicationId)
    if batchId:
        stmt = stmt.where(WriteOff.batchId == batchId)
    if status_filter:
        stmt = stmt.where(WriteOff.status.in_({s.strip() for s in status_filter.split(",")}))
    if dateFrom:
        stmt = stmt.where(WriteOff.expiredAt >= dateFrom.isoformat())
    if dateTo:
        stmt = stmt.where(WriteOff.expiredAt <= dateTo.isoformat())
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = db.execute(
        stmt.order_by(WriteOff.expiredAt.desc(), WriteOff.id.desc())
        .offset(max(0, (page - 1) * limit)).limit(limit)
    ).scalars().all()
    return ok({
        "data": [_serialize_write_off(w) for w in rows],
        "pagination": {
            "page": page, "limit": limit, "total": total,
            "totalPages": (total + limit - 1) // limit if total else 0,
        },
    })


@router.post("/{write_off_id}/discard")
def discard_write_off(
    write_off_id: str,
    db: Session = Depends(get_session),
    _: dict = Depends(require_role("pharmacy_staff")),
):
    """Desecha unidades aisladas por una baja: recién aquí se descuenta el físico (RF4)."""
    w = db.execute(
        select(WriteOff).where(WriteOff.id == write_off_id).with_for_update()
    ).scalar_one_or_none()
    if not w:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Baja no encontrada"})
    if w.status == "DISCARDED":
        raise HTTPException(409, detail={
            "code": "INVALID_STATE",
            "message": "Las unidades de esta baja ya fueron desechadas",
        })
    med = db.execute(
        select(Medication).where(Medication.id == w.medicationId).with_for_update()
    ).scalar_one_or_none()
    if med:
        if w.quantity > med.isolatedQuantity:
            raise HTTPException(409, detail={
                "code": "INVALID_STATE",
                "message": f"La baja ({w.quantity}) excede lo aislado ({med.isolatedQuantity})",
            })
        med.isolatedQuantity -= w.quantity
        med.physicalQuantity -= w.quantity
    w.status = "DISCARDED"
    w.discardDate = date.today().isoformat()
    db.commit()
    return ok(_serialize_write_off(w))


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
