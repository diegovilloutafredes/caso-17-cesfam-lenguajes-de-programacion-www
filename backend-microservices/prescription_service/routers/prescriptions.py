import logging
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from prescription_service.clients.inventory import InventoryServiceClient
from prescription_service.clients.notification import NotificationServiceClient
from prescription_service.clients.patient import PatientServiceClient
from prescription_service.db import get_session
from prescription_service.models import Prescription, PrescriptionItem
from prescription_service.schemas import (
    CancelRequest, DeliverRequest, ExternalPurchaseRequest, PrescriptionCreate,
)
from shared.auth import current_token, current_user, require_role
from shared.envelope import created, ok
from shared.ids import next_id

logger = logging.getLogger("prescription_service")

router = APIRouter(prefix="/api/v1/prescriptions", tags=["Recetas"])

ACTIVE_STATES = {"SUBMITTED", "RESERVED", "READY_FOR_PICKUP"}
TERMINAL_STATES = {"PICKED_UP", "CANCELLED", "EXPIRED", "EXTERNAL_PURCHASE"}

patient_client = PatientServiceClient()
inventory_client = InventoryServiceClient()
notification_client = NotificationServiceClient()


def _serialize(r: Prescription) -> dict:
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
            "message": f"No se puede {action} una receta en estado {r.status}",
        })


def _has_error(response: dict) -> bool:
    return response.get("error") is not None


def _get_locked(db: Session, prescription_id: str) -> Optional[Prescription]:
    return db.execute(
        select(Prescription)
        .where(Prescription.id == prescription_id)
        .with_for_update()
    ).scalar_one_or_none()


def _expire_overdue(db: Session, token: str) -> None:
    """Expira las recetas activas con la fecha límite vencida; una liberación fallida queda en el log."""
    today = date.today()
    overdue = db.execute(
        select(Prescription.id).where(
            Prescription.status.in_(ACTIVE_STATES),
            Prescription.pickupDeadline < today,
        )
    ).scalars().all()
    for rid in overdue:
        # skip_locked: si otra request ya está expirando esta receta, no se espera
        r = db.execute(
            select(Prescription)
            .where(Prescription.id == rid)
            .with_for_update(skip_locked=True)
        ).scalar_one_or_none()
        if not r or r.status not in ACTIVE_STATES or r.pickupDeadline >= today:
            db.rollback()
            continue
        if r.status == "READY_FOR_PICKUP":
            for item in r.items:
                resp = inventory_client.release_stock(
                    item.medicationId, item.totalQuantity, token=token,
                )
                if _has_error(resp):
                    logger.error(
                        "Expiración de %s: no se liberaron %s unidades de %s (%s)",
                        rid, item.totalQuantity, item.medicationId,
                        resp["error"].get("message"),
                    )
        r.status = "EXPIRED"
        db.commit()


def _notify_patient_or_guardian(r: Prescription, event: str, message: str, token: str) -> None:
    """Aviso por correo y SMS al paciente; sin contacto, cae al primer apoderado con datos (RF11)."""
    try:
        patient = (patient_client.get_patient(r.patientId, token=token) or {}).get("data") or {}
        email, phone, guardian_id = patient.get("email"), patient.get("phone"), None
        if not email and not phone:
            g_resp = patient_client.list_guardians(r.patientId, token=token)
            for g in (g_resp.get("data") or []):
                if g.get("email") or g.get("phone"):
                    email, phone, guardian_id = g.get("email"), g.get("phone"), g.get("id")
                    break
        base = {
            "event": event,
            "recipientPatientId": r.patientId,
            "recipientGuardianId": guardian_id,
            "message": message,
            "prescriptionId": r.id,
        }
        sent = False
        if email:
            resp = notification_client.send(
                {**base, "type": "EMAIL", "recipientAddress": email}, token=token)
            sent = sent or not _has_error(resp)
        if phone:
            resp = notification_client.send(
                {**base, "type": "SMS", "recipientAddress": phone}, token=token)
            sent = sent or not _has_error(resp)
        if not sent:
            logger.warning("Receta %s: aviso %s sin destinatario contactable", r.id, event)
    except Exception:
        logger.warning("Receta %s: falló el envío del aviso %s", r.id, event, exc_info=True)


REMINDER_DAYS = 3


def _remind_upcoming(db: Session, token: str) -> None:
    """Recordatorio de próximo retiro cuando el plazo está por vencer (RF13); se emite una sola vez."""
    today = date.today()
    due = db.execute(
        select(Prescription.id).where(
            Prescription.nextScheduledDelivery.is_not(None),
            Prescription.nextScheduledDelivery >= today,
            Prescription.nextScheduledDelivery <= today + timedelta(days=REMINDER_DAYS),
            Prescription.reminderSentAt.is_(None),
            Prescription.status.not_in(["CANCELLED", "EXPIRED", "EXTERNAL_PURCHASE"]),
        )
    ).scalars().all()
    for rid in due:
        r = db.execute(
            select(Prescription)
            .where(Prescription.id == rid)
            .with_for_update(skip_locked=True)
        ).scalar_one_or_none()
        if not r or r.reminderSentAt is not None:
            db.rollback()
            continue
        _notify_patient_or_guardian(
            r, "PICKUP_REMINDER",
            f"Su próximo retiro de medicamentos vence el {r.nextScheduledDelivery.isoformat()}. "
            f"Receta {r.id}.",
            token,
        )
        r.reminderSentAt = today
        db.commit()


@router.get("")
def list_prescriptions(
    status_filter: Optional[str] = None,
    patientId: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    _: dict = Depends(current_user),
    token: str = Depends(current_token),
    db: Session = Depends(get_session),
):
    _expire_overdue(db, token)
    _remind_upcoming(db, token)
    stmt = select(Prescription)
    if status_filter:
        stmt = stmt.where(
            Prescription.status.in_({s.strip() for s in status_filter.split(",")})
        )
    if patientId:
        stmt = stmt.where(Prescription.patientId == patientId)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = db.execute(
        stmt.order_by(Prescription.emissionDate.desc(), Prescription.id.desc())
        .offset(max(0, (page - 1) * limit)).limit(limit)
    ).scalars().all()
    return ok({
        "data": [_serialize(r) for r in rows],
        "pagination": {
            "page": page, "limit": limit, "total": total,
            "totalPages": (total + limit - 1) // limit if total else 0,
        },
    })


@router.get("/queue")
def queue(
    _: dict = Depends(current_user),
    token: str = Depends(current_token),
    db: Session = Depends(get_session),
):
    _expire_overdue(db, token)
    _remind_upcoming(db, token)
    items = db.execute(
        select(Prescription)
        .where(Prescription.status.in_(["SUBMITTED", "RESERVED"]))
        .order_by(Prescription.emissionDate, Prescription.id)
    ).scalars().all()
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
    user: dict = Depends(require_role("doctor")),
    token: str = Depends(current_token),
    db: Session = Depends(get_session),
):
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

    # dos creaciones concurrentes pueden calcular el mismo ID; se reintenta
    for _ in range(3):
        rec = Prescription(
            id=next_id(db, Prescription.id, "R", start=100),
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
        try:
            db.commit()
            return created(_serialize(rec))
        except IntegrityError:
            db.rollback()
    raise HTTPException(409, detail={
        "code": "CONFLICT",
        "message": "No se pudo asignar un ID de receta; reintenta la operación",
    })


def _release_reserved(reserved: list, prescription_id: str, token: str) -> None:
    """Compensación: libera las reservas ya aplicadas; una falla se registra en el log."""
    for med_id, qty in reserved:
        release = inventory_client.release_stock(med_id, qty, token=token)
        if _has_error(release):
            logger.error(
                "Compensación fallida en %s: %s unidades de %s quedaron reservadas (%s)",
                prescription_id, qty, med_id, release["error"].get("message"),
            )


@router.post("/{prescription_id}/prepare")
def prepare(
    prescription_id: str,
    _user: dict = Depends(require_role("pharmacy_staff")),
    token: str = Depends(current_token),
    db: Session = Depends(get_session),
):
    r = _get_locked(db, prescription_id)
    if not r:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Receta no encontrada"})
    _ensure_status(r, {"SUBMITTED"}, "preparar")

    reserved: list[tuple[str, int]] = []
    for item in r.items:
        response = inventory_client.reserve_stock(
            item.medicationId, item.totalQuantity, token=token
        )
        if _has_error(response):
            _release_reserved(reserved, prescription_id, token)
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
    _: dict = Depends(require_role("pharmacy_staff")),
    db: Session = Depends(get_session),
):
    """No mueve stock; la reserva ocurre al pasar a READY."""
    r = _get_locked(db, prescription_id)
    if not r:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Receta no encontrada"})
    _ensure_status(r, {"SUBMITTED"}, "reservar")
    r.status = "RESERVED"
    db.commit()
    return ok(_serialize(r))


@router.post("/{prescription_id}/mark-available")
def mark_available(
    prescription_id: str,
    _user: dict = Depends(require_role("pharmacy_staff")),
    token: str = Depends(current_token),
    db: Session = Depends(get_session),
):
    r = _get_locked(db, prescription_id)
    if not r:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Receta no encontrada"})
    _ensure_status(r, {"RESERVED"}, "marcar disponible")

    reserved: list[tuple[str, int]] = []
    for item in r.items:
        response = inventory_client.reserve_stock(
            item.medicationId, item.totalQuantity, token=token
        )
        if _has_error(response):
            _release_reserved(reserved, prescription_id, token)
            err = response["error"]
            raise HTTPException(409, detail={
                "code": err.get("code", "RESERVE_FAILED"),
                "message": err.get("message"),
            })
        reserved.append((item.medicationId, item.totalQuantity))

    r.status = "READY_FOR_PICKUP"
    db.commit()

    # notificación best-effort: no bloquea el cambio de estado
    _notify_patient_or_guardian(
        r, "RESERVATION_AVAILABLE",
        f"Su medicamento está disponible para retiro. Receta {r.id}.",
        token,
    )

    return ok(_serialize(r))


@router.post("/{prescription_id}/external-purchase")
def external_purchase(
    prescription_id: str, body: ExternalPurchaseRequest,
    _: dict = Depends(require_role("pharmacy_staff")),
    db: Session = Depends(get_session),
):
    r = _get_locked(db, prescription_id)
    if not r:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Receta no encontrada"})
    _ensure_status(r, {"SUBMITTED"}, "registrar compra externa para")
    r.status = "EXTERNAL_PURCHASE"
    r.externalPurchaseNotes = body.notes
    db.commit()
    return ok(_serialize(r))


@router.post("/{prescription_id}/cancel")
def cancel(
    prescription_id: str, body: CancelRequest,
    _user: dict = Depends(require_role("doctor", "pharmacy_staff")),
    token: str = Depends(current_token),
    db: Session = Depends(get_session),
):
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
    _user: dict = Depends(require_role("pharmacy_staff")),
    token: str = Depends(current_token),
    db: Session = Depends(get_session),
):
    r = _get_locked(db, prescription_id)
    if not r:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Receta no encontrada"})
    _ensure_status(r, {"READY_FOR_PICKUP"}, "entregar")
    if r.pickupDeadline < date.today():
        raise HTTPException(409, detail={
            "code": "INVALID_STATE",
            "message": f"La receta venció el {r.pickupDeadline.isoformat()}; no se puede entregar",
        })

    if body.pickerType == "guardian":
        if not body.guardianId:
            raise HTTPException(400, detail={
                "code": "INVALID_GUARDIAN", "message": "guardianId requerido"})
        g_resp = patient_client.list_guardians(r.patientId, token=token)
        if _has_error(g_resp):
            raise HTTPException(g_resp.get("statusCode", 503), detail={
                "code": "PATIENT_SERVICE_ERROR",
                "message": g_resp["error"].get("message", "Error consultando apoderados"),
            })
        if body.guardianId not in {g["id"] for g in (g_resp.get("data") or [])}:
            raise HTTPException(400, detail={
                "code": "INVALID_GUARDIAN",
                "message": f"El apoderado {body.guardianId} no está autorizado para este paciente",
            })
    if body.pickerType == "third_party" and (not body.thirdPartyRut or not body.thirdPartyName):
        raise HTTPException(400, detail={
            "code": "MISSING_THIRD_PARTY",
            "message": "thirdPartyRut y thirdPartyName requeridos",
        })

    # la entrega debe ser total
    required = sum(it.totalQuantity for it in r.items)
    provided = sum(b.quantity for b in body.batches)
    if provided != required:
        raise HTTPException(400, detail={
            "code": "QUANTITY_MISMATCH",
            "message": f"Las partidas ({provided}) no coinciden con lo recetado ({required})",
        })

    response = inventory_client.consume(
        [b.model_dump() for b in body.batches],
        [{"medicationId": it.medicationId, "quantity": it.totalQuantity} for it in r.items],
        token=token,
    )
    if _has_error(response):
        err = response["error"]
        raise HTTPException(response.get("statusCode", 409), detail={
            "code": err.get("code", "CONSUME_FAILED"),
            "message": err.get("message"),
            "details": err.get("details"),
        })

    r.status = "PICKED_UP"
    # tratamiento largo: la dotación cubre durationDays y ahí vence el próximo retiro
    if r.treatmentType == "LONG":
        r.nextScheduledDelivery = date.today() + timedelta(days=r.durationDays)
    r.delivery = {
        "pickerType": body.pickerType,
        "guardianId": body.guardianId,
        "thirdPartyRut": body.thirdPartyRut,
        "thirdPartyName": body.thirdPartyName,
        "batches": [b.model_dump() for b in body.batches],
        "deliveryDate": date.today().isoformat(),
    }
    try:
        db.commit()
    except Exception:
        logger.error(
            "Receta %s: stock consumido pero la entrega no quedó registrada; conciliar a mano",
            prescription_id,
        )
        raise
    return ok(_serialize(r))
