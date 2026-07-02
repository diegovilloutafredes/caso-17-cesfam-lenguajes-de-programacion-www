from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
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
    """Produce la misma forma JSON que el almacén in-memory original."""
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
    """Envía notificación (SMS o email) usando el provider correspondiente + persiste registro."""
    if body.type == NotificationType.SMS:
        success = sms_provider.send(to=body.recipientAddress, message=body.message)
    else:
        success = email_provider.send(
            to=body.recipientAddress,
            subject="CESFAM — Aviso de medicamentos",
            body=body.message,
        )

    new_id = next_id(db, Notification.id, "NTF-")
    record = Notification(
        id=new_id,
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
    db.commit()
    return created(_serialize(record))


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
        from fastapi import HTTPException
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Notificación no encontrada"})
    return ok(_serialize(n))
