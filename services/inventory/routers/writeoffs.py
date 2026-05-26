from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from services.inventory.schemas.inventory import WriteOff
from data import STATE
from services.common.deps import current_user, pagination_params, paginate

router = APIRouter(prefix="/api/v1/write-offs", tags=["Bajas"])


@router.get("")
def list_write_offs(
    medicationId: Optional[str] = None,
    batchId: Optional[str] = None,
    status_filter: Optional[str] = None,
    dateFrom: Optional[date] = None,
    dateTo: Optional[date] = None,
    page_limit: tuple[int, int] = Depends(pagination_params),
    _: dict = Depends(current_user),
):
    """Lista bajas registradas. Soporta filtros por medicamento, partida, estado y rango de fechas."""
    page, limit = page_limit
    items = list(STATE["writeOffs"].values())
    if medicationId:
        items = [w for w in items if w["medicationId"] == medicationId]
    if batchId:
        items = [w for w in items if w["batchId"] == batchId]
    if status_filter:
        wanted = {s.strip() for s in status_filter.split(",")}
        items = [w for w in items if w["status"] in wanted]
    if dateFrom:
        items = [w for w in items if w["expiredAt"] >= dateFrom]
    if dateTo:
        items = [w for w in items if w["expiredAt"] <= dateTo]
    items = sorted(items, key=lambda w: w["expiredAt"], reverse=True)
    return paginate(items, page, limit)


@router.get("/{write_off_id}", response_model=WriteOff)
def get_write_off(write_off_id: str, _: dict = Depends(current_user)):
    w = STATE["writeOffs"].get(write_off_id)
    if not w:
        raise HTTPException(404, detail={"error": {"code": "NOT_FOUND", "message": "Baja no encontrada"}})
    return w
