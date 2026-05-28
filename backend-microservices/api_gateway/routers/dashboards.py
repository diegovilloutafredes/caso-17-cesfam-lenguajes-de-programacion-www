"""Endpoints BFF — agregación cross-context para las pantallas de médico y farmacia.

Estos endpoints reducen N round-trips del frontend a 1 sola llamada por dashboard,
combinando data de InventoryService, PatientService y PrescriptionService.
"""

from fastapi import APIRouter, Depends

from api_gateway.clients.inventory import InventoryServiceClient
from api_gateway.clients.patient import PatientServiceClient
from api_gateway.clients.prescription import PrescriptionServiceClient
from shared.auth import current_token, current_user
from shared.envelope import ok

router = APIRouter(prefix="/api/v1", tags=["Tableros (BFF)"])

inventory_client = InventoryServiceClient()
patient_client = PatientServiceClient()
prescription_client = PrescriptionServiceClient()


def _data(response: dict):
    return response.get("data") if isinstance(response, dict) else None


@router.get("/doctor/dashboard")
def doctor_dashboard(
    _user: dict = Depends(current_user),
    token: str = Depends(current_token),
):
    """Agrega: stockSummary + recentPatients + stockTop (3 calls cross-service)."""
    stock_resp = inventory_client.stock_summary(token=token)
    patients_resp = patient_client.list_recent(token=token, limit=3)
    meds_resp = inventory_client.list_medications(token=token, limit=6)

    meds_data = _data(meds_resp) or {}
    meds = meds_data.get("data", []) if isinstance(meds_data, dict) else (meds_data or [])

    def _stock_status(m: dict) -> str:
        available = m.get("stock", {}).get("availableQuantity", 0)
        if available == 0:
            return "OUT_OF_STOCK"
        if available < m.get("minStock", 0):
            return "LOW_STOCK"
        return "AVAILABLE"

    return ok({
        "stockSummary": _data(stock_resp) or {},
        "recentPatients": _data(patients_resp) or [],
        "stockTop": [
            {
                "id": m["id"],
                "description": m["description"],
                "available": m["stock"]["availableQuantity"],
                "status": _stock_status(m),
            }
            for m in meds[:6]
        ],
    })


@router.get("/pharmacy/dashboard")
def pharmacy_dashboard(
    _user: dict = Depends(current_user),
    token: str = Depends(current_token),
):
    """Agrega: KPIs de recetas + queue + stockAlerts (4 calls cross-service)."""
    queue_resp = prescription_client.queue(token=token)
    pending_resp = prescription_client.list_by_status("SUBMITTED", token=token)
    reserved_resp = prescription_client.list_by_status("RESERVED", token=token)
    ready_resp = prescription_client.list_by_status("READY_FOR_PICKUP", token=token)
    alerts_resp = inventory_client.low_stock(token=token)

    def _count(resp):
        d = _data(resp) or {}
        if isinstance(d, dict):
            return d.get("pagination", {}).get("total", len(d.get("data", [])))
        if isinstance(d, list):
            return len(d)
        return 0

    queue_data = _data(queue_resp) or []

    return ok({
        "kpis": {
            "pendingPrescriptions": _count(pending_resp),
            "activeReservations": _count(reserved_resp),
            "readyForPickup": _count(ready_resp),
        },
        "queue": [
            {"id": r["id"], "patientId": r["patientId"], "status": r["status"]}
            for r in (queue_data if isinstance(queue_data, list) else [])[:10]
        ],
        "stockAlerts": _data(alerts_resp) or [],
    })
