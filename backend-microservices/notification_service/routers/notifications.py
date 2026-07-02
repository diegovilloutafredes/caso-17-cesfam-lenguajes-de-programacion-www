from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from notification_service.db import get_session
from notification_service.models import Notification
from notification_service.providers import email_provider, sms_provider
from notification_service.schemas import NotificationCreate, NotificationType
from shared.auth import current_user
from shared.envelope import created, ok
from shared.ids import next_id

router = APIRouter(prefix="/api/v1/notifications", tags=["Notificaciones"])


def _serialize(n: Notification) -> dict:
    return {
        "id": n.id,
        "type": n.type,
        "event": n.event,
        "recipientPatientId": n.recipientPatientId,
        "recipientGuardianId": n.recipientGuardianId,
        "recipientAddress": n.recipientAddress,
        "message": n.message,
        "sentAt": n.sentAt.isoformat() if n.sentAt else None,
        "status": n.status,
        "prescriptionId": n.prescriptionId,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def send_notification(
    body: NotificationCreate,
    db: Session = Depends(get_session),
    _: dict = Depends(current_user),
):
    if body.type == NotificationType.SMS:
        success = sms_provider.send(to=body.recipientAddress, message=body.message)
    else:
        success = email_provider.send(
            to=body.recipientAddress,
            subject="CESFAM — Aviso de medicamentos",
            body=body.message,
        )

    # dos envíos concurrentes pueden calcular el mismo ID; se reintenta el registro
    for _ in range(3):
        record = Notification(
            id=next_id(db, Notification.id, "NTF-"),
            type=body.type.value if hasattr(body.type, "value") else body.type,
            event=body.event.value if hasattr(body.event, "value") else body.event,
            recipientPatientId=body.recipientPatientId,
            recipientGuardianId=body.recipientGuardianId,
            recipientAddress=body.recipientAddress,
            message=body.message,
            sentAt=datetime.utcnow() if success else None,
            status="SENT" if success else "ERROR",
            prescriptionId=body.prescriptionId,
        )
        db.add(record)
        try:
            db.commit()
            return created(_serialize(record))
        except IntegrityError:
            db.rollback()
    raise HTTPException(409, detail={
        "code": "CONFLICT",
        "message": "No se pudo registrar la notificación; reintenta la operación",
    })


@router.get("")
def list_notifications(
    patientId: Optional[str] = None,
    prescriptionId: Optional[str] = None,
    db: Session = Depends(get_session),
    _: dict = Depends(current_user),
):
    rows = db.execute(select(Notification)).scalars().all()
    items = [_serialize(n) for n in rows]
    if patientId:
        items = [n for n in items if n.get("recipientPatientId") == patientId]
    if prescriptionId:
        items = [n for n in items if n.get("prescriptionId") == prescriptionId]
    items = sorted(items, key=lambda n: n.get("sentAt") or "", reverse=True)
    return ok(items)


@router.get("/{notification_id}")
def get_notification(
    notification_id: str,
    db: Session = Depends(get_session),
    _: dict = Depends(current_user),
):
    n = db.get(Notification, notification_id)
    if not n:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Notificación no encontrada"})
    return ok(_serialize(n))
