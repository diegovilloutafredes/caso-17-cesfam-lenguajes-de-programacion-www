from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from inventory_service.seed import STATE
from shared.auth import current_user
from shared.envelope import ok

router = APIRouter(prefix="/api/v1/write-offs", tags=["Bajas"])


@router.get("")
def list_write_offs(
    medicationId: Optional[str] = None,
    batchId: Optional[str] = None,
    status_filter: Optional[str] = None,
    dateFrom: Optional[date] = None,
    dateTo: Optional[date] = None,
    page: int = 1,
    limit: int = 20,
    _: dict = Depends(current_user),
):
    items = list(STATE["writeOffs"].values())
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
def get_write_off(write_off_id: str, _: dict = Depends(current_user)):
    w = STATE["writeOffs"].get(write_off_id)
    if not w:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Baja no encontrada"})
    return ok(w)
