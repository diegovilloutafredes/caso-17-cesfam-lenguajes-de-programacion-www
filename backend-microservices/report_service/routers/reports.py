from datetime import date
from enum import Enum
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from report_service.clients.inventory import InventoryServiceClient
from report_service.clients.prescription import PrescriptionServiceClient
from shared.auth import current_token, current_user

router = APIRouter(prefix="/api/v1/reports", tags=["Informes"])

inventory_client = InventoryServiceClient()
prescription_client = PrescriptionServiceClient()


class ReportType(str, Enum):
    STOCK = "STOCK"
    RESERVED = "RESERVED"
    EXPIRED = "EXPIRED"


class ReportRequest(BaseModel):
    reportType: ReportType
    dateFrom: Optional[date] = None
    dateTo: Optional[date] = None


@router.post("", response_class=PlainTextResponse)
def generate_report(
    body: ReportRequest,
    _user: dict = Depends(current_user),
    token: str = Depends(current_token),
):
    """Genera informe CSV. Consulta InventoryService y PrescriptionService según tipo."""
    rows: list[list[str]] = []

    if body.reportType == ReportType.STOCK:
        rows.append(["code", "description", "manufacturer", "availableStock",
                     "reservedStock", "physicalStock", "minStock"])
        resp = inventory_client.list_medications(token=token)
        if resp.get("error"):
            return f"ERROR: {resp['error'].get('message')}"
        meds = (resp.get("data") or {}).get("data") or []
        for m in meds:
            stock = m.get("stock", {})
            rows.append([
                m.get("code", ""), m.get("description", ""),
                m.get("manufacturer", ""),
                str(stock.get("availableQuantity", 0)),
                str(stock.get("reservedQuantity", 0)),
                str(stock.get("physicalQuantity", 0)),
                str(m.get("minStock", 0)),
            ])

    elif body.reportType == ReportType.RESERVED:
        rows.append(["prescriptionId", "patientId", "medicationId",
                     "totalQuantity", "emissionDate", "status"])
        resp = prescription_client.list_by_status("RESERVED,READY_FOR_PICKUP", token=token)
        if resp.get("error"):
            return f"ERROR: {resp['error'].get('message')}"
        prescriptions = (resp.get("data") or {}).get("data") or []
        for r in prescriptions:
            for item in r.get("items", []):
                rows.append([
                    r["id"], r["patientId"], item["medicationId"],
                    str(item["totalQuantity"]), r["emissionDate"], r["status"],
                ])

    elif body.reportType == ReportType.EXPIRED:
        rows.append(["medicationId", "code", "batches"])
        meds_resp = inventory_client.list_medications(token=token)
        meds = (meds_resp.get("data") or {}).get("data") or []
        today = date.today().isoformat()
        for m in meds:
            batches_resp = inventory_client.list_batches(m["id"], token=token)
            batches = batches_resp.get("data") or []
            expired = [b for b in batches if b.get("expirationDate", "9999") <= today]
            if expired:
                rows.append([
                    m["id"], m.get("code", ""),
                    "; ".join(f"{b['batchNumber']}({b['availableQuantity']})" for b in expired),
                ])

    return "\n".join(",".join(r) for r in rows)
