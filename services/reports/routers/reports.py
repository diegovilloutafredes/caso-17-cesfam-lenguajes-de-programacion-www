from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from services.common.enums import ReportType
from services.reports.schemas.report import ReportRead as Report
from services.reports.schemas.notification import NotificationRead as Notification, NotificationCreate
from services.patients.schemas.common import MessageResponse
from data import STATE
from services.common.deps import current_user

router = APIRouter(prefix="/api/v1/reports", tags=["Informes"])


class ReportRequest(BaseModel):
    reportType: ReportType
    dateFrom: Optional[date] = None
    dateTo: Optional[date] = None


@router.post("", response_class=PlainTextResponse)
def generate_report(body: ReportRequest, _: dict = Depends(current_user)):
    """Genera un informe en formato CSV. La respuesta es text/csv."""
    rows: list[list[str]] = []

    if body.reportType == ReportType.STOCK:
        rows.append(["code", "description", "manufacturer", "availableStock", "reservedStock", "physicalStock", "minStock"])
        for m in STATE["medications"].values():
            rows.append([
                m["code"], m["description"], m["manufacturer"],
                str(m["stock"]["availableQuantity"]),
                str(m["stock"]["reservedQuantity"]),
                str(m["stock"]["physicalQuantity"]),
                str(m["minStock"]),
            ])
    elif body.reportType == ReportType.RESERVED:
        rows.append(["prescriptionId", "patientId", "medication", "quantity", "emissionDate", "status"])
        for r in STATE["prescriptions"].values():
            if r["status"] not in {"RESERVED", "READY_FOR_PICKUP"}:
                continue
            for line in r["lines"]:
                med = STATE["medications"].get(line["medicationId"], {})
                rows.append([
                    r["id"], r["patientId"], med.get("description", line["medicationId"]),
                    str(line["totalQuantity"]), str(r["emissionDate"]), r["status"],
                ])
    elif body.reportType == ReportType.EXPIRED:
        rows.append(["batchId", "medication", "batchNumber", "expirationDate", "availableQuantity"])
        for b in STATE["batches"].values():
            if b["expirationDate"] <= date.today():
                med = STATE["medications"].get(b["medicationId"], {})
                rows.append([
                    b["id"], med.get("description", ""), b["batchNumber"],
                    str(b["expirationDate"]), str(b["availableQuantity"]),
                ])

    csv = "\n".join(",".join(r) for r in rows)
    return csv
