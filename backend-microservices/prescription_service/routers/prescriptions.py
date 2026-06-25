from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from prescription_service.clients.inventory import InventoryServiceClient
from prescription_service.clients.notification import NotificationServiceClient
from prescription_service.clients.patient import PatientServiceClient
from prescription_service.db import get_session
from prescription_service.models import Prescription, PrescriptionItem
from prescription_service.schemas import (
    CancelRequest, DeliverRequest, ExternalPurchaseRequest, PrescriptionCreate,
)
from prescription_service.seed import next_id
from shared.auth import current_token, current_user
from shared.envelope import created, ok

router = APIRouter(prefix="/api/v1/prescriptions", tags=["Recetas"])

ACTIVE_STATES = {"SUBMITTED", "RESERVED", "READY_FOR_PICKUP"}
TERMINAL_STATES = {"PICKED_UP", "CANCELLED", "EXPIRED", "EXTERNAL_PURCHASE"}

patient_client = PatientServiceClient()
inventory_client = InventoryServiceClient()
notification_client = NotificationServiceClient()


def _serialize(r: Prescription) -> dict:
    """Serializa al contrato JSON. Los campos condicionales (`delivery`,
    `externalPurchaseNotes`, `cancelReason`) solo se incluyen en su estado."""
    out = {
        "id": r.id,
        "doctorId": r.doctorId,
        "patientId": r.patientId,
        "emissionDate": r.emissionDate.isoformat(),
        "pickupDeadline": r.pickupDeadline.isoformat(),
        "treatmentType": r.treatmentType,
        "durationDays": r.durationDays,
        "status": r.status,
        "nextScheduledDelivery": (
            r.nextScheduledDelivery.isoformat()
            if r.nextScheduledDelivery is not None else None
        ),
        "items": [
            {
                "medicationId": it.medicationId,
                "dosesPerInterval": it.dosesPerInterval,
                "intervalHours": it.intervalHours,
                "doseDescription": it.doseDescription,
                "durationDays": it.durationDays,
                "totalQuantity": it.totalQuantity,
            }
            for it in r.items
        ],
    }
    if r.status == "EXTERNAL_PURCHASE":
        out["externalPurchaseNotes"] = r.externalPurchaseNotes
    if r.status == "CANCELLED":
        out["cancelReason"] = r.cancelReason
    if r.delivery is not None:
        out["delivery"] = r.delivery
    return out


def _ensure_status(r: Prescription, allowed: set, action: str) -> None:
    if r.status not in allowed:
        raise HTTPException(409, detail={
            "code": "INVALID_STATE",
            "message": f"No se puede '{action}' en estado {r.status}",
        })


def _has_error(response: dict) -> bool:
    return response.get("error") is not None


def _get_locked(db: Session, prescription_id: str) -> Optional[Prescription]:
    """Carga la receta con bloqueo de fila para serializar transiciones concurrentes."""
    return db.execute(
        select(Prescription)
        .where(Prescription.id == prescription_id)
        .with_for_update()
    ).scalar_one_or_none()


@router.get("")
def list_prescriptions(
    status_filter: Optional[str] = None,
    patientId: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    _: dict = Depends(current_user),
    db: Session = Depends(get_session),
):
    items = list(db.execute(select(Prescription)).scalars().all())
    if status_filter:
        wanted = {s.strip() for s in status_filter.split(",")}
        items = [r for r in items if r.status in wanted]
    if patientId:
        items = [r for r in items if r.patientId == patientId]
    items = sorted(items, key=lambda r: r.emissionDate, reverse=True)
    total = len(items)
    start = max(0, (page - 1) * limit)
    return ok({
        "data": [_serialize(r) for r in items[start : start + limit]],
        "pagination": {
            "page": page, "limit": limit, "total": total,
            "totalPages": (total + limit - 1) // limit if total else 0,
        },
    })


@router.get("/queue")
def queue(_: dict = Depends(current_user), db: Session = Depends(get_session)):
    items = [
        r for r in db.execute(select(Prescription)).scalars().all()
        if r.status in {"SUBMITTED", "RESERVED"}
    ]
    items = sorted(items, key=lambda r: r.emissionDate)
    return ok([_serialize(r) for r in items])


@router.get("/{prescription_id}")
def get_prescription(
    prescription_id: str,
    _: dict = Depends(current_user),
    db: Session = Depends(get_session),
):
    r = db.get(Prescription, prescription_id)
    if not r:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Receta no encontrada"})
    return ok(_serialize(r))


@router.post("", status_code=status.HTTP_201_CREATED)
def create_prescription(
    body: PrescriptionCreate,
    user: dict = Depends(current_user),
    token: str = Depends(current_token),
    db: Session = Depends(get_session),
):
    """Crea receta. Valida que el paciente exista vía PatientService (cross-service)."""
    response = patient_client.get_patient(body.patientId, token=token)
    if _has_error(response):
        err = response["error"]
        code = err.get("code", "DOWNSTREAM_ERROR")
        if code == "NOT_FOUND":
            raise HTTPException(404, detail={
                "code": "PATIENT_NOT_FOUND",
                "message": f"Paciente {body.patientId} no encontrado",
            })
        raise HTTPException(response.get("statusCode", 503), detail={
            "code": "PATIENT_SERVICE_ERROR",
            "message": err.get("message", "Error consultando paciente"),
        })

    new_id = next_id(db, "R")
    rec = Prescription(
        id=new_id,
        doctorId=user["id"],
        patientId=body.patientId,
        emissionDate=date.today(),
        pickupDeadline=body.pickupDeadline,
        treatmentType=body.treatmentType.value,
        durationDays=body.durationDays,
        status="SUBMITTED",
        nextScheduledDelivery=None,
        items=[
            PrescriptionItem(
                medicationId=i.medicationId,
                dosesPerInterval=i.dosesPerInterval,
                intervalHours=i.intervalHours,
                doseDescription=i.doseDescription,
                durationDays=i.durationDays,
                totalQuantity=i.totalQuantity,
            )
            for i in body.items
        ],
    )
    db.add(rec)
    db.commit()
    return created(_serialize(rec))


@router.post("/{prescription_id}/prepare")
def prepare(
    prescription_id: str,
    user: dict = Depends(current_user),
    token: str = Depends(current_token),
    db: Session = Depends(get_session),
):
    """SUBMITTED → READY_FOR_PICKUP. Reserva stock vía InventoryService; si una
    línea falla, libera (compensa) las ya reservadas."""
    r = _get_locked(db, prescription_id)
    if not r:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Receta no encontrada"})
    _ensure_status(r, {"SUBMITTED"}, "prepare")

    reserved: list[tuple[str, int]] = []
    for item in r.items:
        response = inventory_client.reserve_stock(
            item.medicationId, item.totalQuantity, token=token
        )
        if _has_error(response):
            # Compensa: libera lo ya reservado
            for med_id, qty in reserved:
                inventory_client.release_stock(med_id, qty, token=token)
            err = response["error"]
            if err.get("code") == "INSUFFICIENT_STOCK":
                raise HTTPException(409, detail={
                    "code": "INSUFFICIENT_STOCK",
                    "message": err.get("message"),
                    "details": {"medicationId": item.medicationId},
                })
            raise HTTPException(response.get("statusCode", 503), detail={
                "code": "INVENTORY_SERVICE_ERROR",
                "message": err.get("message"),
            })
        reserved.append((item.medicationId, item.totalQuantity))

    r.status = "READY_FOR_PICKUP"
    db.commit()
    return ok(_serialize(r))


@router.post("/{prescription_id}/reserve")
def reserve(
    prescription_id: str,
    _: dict = Depends(current_user),
    db: Session = Depends(get_session),
):
    """SUBMITTED → RESERVED. Sin movimiento de stock (no hay disponible aún)."""
    r = _get_locked(db, prescription_id)
    if not r:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Receta no encontrada"})
    _ensure_status(r, {"SUBMITTED"}, "reserve")
    r.status = "RESERVED"
    db.commit()
    return ok(_serialize(r))


@router.post("/{prescription_id}/mark-available")
def mark_available(
    prescription_id: str,
    user: dict = Depends(current_user),
    token: str = Depends(current_token),
    db: Session = Depends(get_session),
):
    """RESERVED → READY_FOR_PICKUP. Reserva stock + notifica al paciente vía NotificationService."""
    r = _get_locked(db, prescription_id)
    if not r:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Receta no encontrada"})
    _ensure_status(r, {"RESERVED"}, "mark-available")

    reserved: list[tuple[str, int]] = []
    for item in r.items:
        response = inventory_client.reserve_stock(
            item.medicationId, item.totalQuantity, token=token
        )
        if _has_error(response):
            for med_id, qty in reserved:
                inventory_client.release_stock(med_id, qty, token=token)
            err = response["error"]
            raise HTTPException(409, detail={
                "code": err.get("code", "RESERVE_FAILED"),
                "message": err.get("message"),
            })
        reserved.append((item.medicationId, item.totalQuantity))

    r.status = "READY_FOR_PICKUP"
    db.commit()

    # notificación opcional: no bloquea el cambio de estado
    try:
        patient_resp = patient_client.get_patient(r.patientId, token=token)
        patient = (patient_resp or {}).get("data") or {}
        recipient_email = patient.get("email")
        if recipient_email:
            notification_client.send({
                "type": "EMAIL",
                "event": "RESERVATION_AVAILABLE",
                "recipientPatientId": r.patientId,
                "recipientAddress": recipient_email,
                "message": f"Su medicamento está disponible para retiro. Receta {r.id}.",
                "prescriptionId": r.id,
            }, token=token)
    except Exception:
        pass

    return ok(_serialize(r))


@router.post("/{prescription_id}/external-purchase")
def external_purchase(
    prescription_id: str, body: ExternalPurchaseRequest,
    _: dict = Depends(current_user),
    db: Session = Depends(get_session),
):
    r = _get_locked(db, prescription_id)
    if not r:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Receta no encontrada"})
    _ensure_status(r, {"SUBMITTED"}, "external-purchase")
    r.status = "EXTERNAL_PURCHASE"
    r.externalPurchaseNotes = body.notes
    db.commit()
    return ok(_serialize(r))


@router.post("/{prescription_id}/cancel")
def cancel(
    prescription_id: str, body: CancelRequest,
    _user: dict = Depends(current_user),
    token: str = Depends(current_token),
    db: Session = Depends(get_session),
):
    """Estado activo → CANCELLED. Si tenía stock reservado (READY), lo libera.

    Si la liberación falla (InventoryService caído) no cancela, para no romper la
    invariante de stock; se reintenta cuando el servicio vuelva.
    """
    r = _get_locked(db, prescription_id)
    if not r:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Receta no encontrada"})
    if r.status in TERMINAL_STATES:
        raise HTTPException(409, detail={
            "code": "INVALID_STATE",
            "message": f"Receta ya en estado terminal: {r.status}",
        })

    # libera el stock reservado; si falla, no cancela
    if r.status == "READY_FOR_PICKUP":
        for item in r.items:
            resp = inventory_client.release_stock(
                item.medicationId, item.totalQuantity, token=token,
            )
            if _has_error(resp):
                err = resp["error"]
                raise HTTPException(
                    resp.get("statusCode", 503),
                    detail={
                        "code": "RELEASE_FAILED",
                        "message": (
                            f"No se pudo liberar stock de {item.medicationId}. "
                            f"Receta NO cancelada para preservar invariante de stock. "
                            f"Reintenta luego. Detalle: {err.get('message')}"
                        ),
                    },
                )

    r.status = "CANCELLED"
    r.cancelReason = body.reason
    db.commit()
    return ok(_serialize(r))


@router.post("/{prescription_id}/deliver")
def deliver(
    prescription_id: str, body: DeliverRequest,
    _user: dict = Depends(current_user),
    token: str = Depends(current_token),
    db: Session = Depends(get_session),
):
    """READY_FOR_PICKUP → PICKED_UP. Consume physical stock vía InventoryService."""
    r = _get_locked(db, prescription_id)
    if not r:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Receta no encontrada"})
    _ensure_status(r, {"READY_FOR_PICKUP"}, "deliver")

    if body.pickerType == "guardian" and not body.guardianId:
        raise HTTPException(400, detail={
            "code": "INVALID_GUARDIAN", "message": "guardianId requerido"})
    if body.pickerType == "third_party" and (not body.thirdPartyRut or not body.thirdPartyName):
        raise HTTPException(400, detail={
            "code": "MISSING_THIRD_PARTY",
            "message": "thirdPartyRut y thirdPartyName requeridos",
        })

    # Las partidas entregadas deben sumar lo recetado (entrega completa, no parcial).
    required = sum(it.totalQuantity for it in r.items)
    provided = sum(b.quantity for b in body.batches)
    if provided != required:
        raise HTTPException(400, detail={
            "code": "QUANTITY_MISMATCH",
            "message": f"Las partidas ({provided}) no calzan con lo recetado ({required})",
        })

    response = inventory_client.consume(
        [b.model_dump() for b in body.batches], token=token,
    )
    if _has_error(response):
        err = response["error"]
        raise HTTPException(response.get("statusCode", 409), detail={
            "code": err.get("code", "CONSUME_FAILED"),
            "message": err.get("message"),
        })

    r.status = "PICKED_UP"
    r.delivery = {
        "pickerType": body.pickerType,
        "guardianId": body.guardianId,
        "thirdPartyRut": body.thirdPartyRut,
        "thirdPartyName": body.thirdPartyName,
        "batches": [b.model_dump() for b in body.batches],
        "deliveryDate": date.today().isoformat(),
    }
    db.commit()
    return ok(_serialize(r))
