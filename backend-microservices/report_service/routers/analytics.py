"""reserve queda en 0: RESERVED no tiene timestamp."""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from report_service.clients.prescription import PrescriptionServiceClient
from shared.auth import current_token, current_user
from shared.envelope import ok

router = APIRouter(prefix="/api/v1/analytics", tags=["Analítica"])

prescription_client = PrescriptionServiceClient()


def _parse_day(value) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


@router.get("/prescription-trend")
def prescription_trend(
    dateFrom: date = Query(...),
    dateTo: date = Query(...),
    eventType: Optional[str] = None,
    _user: dict = Depends(current_user),
    token: str = Depends(current_token),
):
    if dateFrom > dateTo:
        raise HTTPException(422, detail={
            "code": "INVALID_RANGE", "message": "dateFrom no puede ser mayor que dateTo",
        })

    resp = prescription_client.list_all(token=token)
    rows = resp.get("data") or []

    emission: dict[date, int] = {}
    delivery: dict[date, int] = {}
    for r in rows:
        ed = _parse_day(r.get("emissionDate"))
        if ed and dateFrom <= ed <= dateTo:
            emission[ed] = emission.get(ed, 0) + 1
        dd = _parse_day((r.get("delivery") or {}).get("deliveryDate"))
        if dd and dateFrom <= dd <= dateTo:
            delivery[dd] = delivery.get(dd, 0) + 1

    series = []
    cursor = dateFrom
    while cursor <= dateTo:
        series.append({
            "date": cursor.isoformat(),
            "emission": emission.get(cursor, 0),
            "reserve": 0,
            "delivery": delivery.get(cursor, 0),
        })
        cursor += timedelta(days=1)

    return ok({
        "from": dateFrom.isoformat(),
        "to": dateTo.isoformat(),
        "series": series,
        "totals": {
            "emission": sum(emission.values()),
            "reserve": 0,
            "delivery": sum(delivery.values()),
        },
    })
