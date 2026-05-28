from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, status

from notification_service.providers import email_provider, sms_provider
from notification_service.schemas import NotificationCreate, NotificationType
from notification_service.seed import STATE, next_id
from shared.auth import current_user
from shared.envelope import created, ok

router = APIRouter(prefix="/api/v1/notifications", tags=["Notificaciones"])


@router.post("", status_code=status.HTTP_201_CREATED)
def send_notification(body: NotificationCreate, _: dict = Depends(current_user)):
    """Envía notificación (SMS o email) usando el provider correspondiente + persiste registro."""
    if body.type == NotificationType.SMS:
        success = sms_provider.send(to=body.recipientAddress, message=body.message)
    else:
        success = email_provider.send(
            to=body.recipientAddress,
            subject="CESFAM — Aviso de medicamentos",
            body=body.message,
        )

    new_id = next_id("NTF")
    record = {
        "id": new_id,
        "type": body.type.value if hasattr(body.type, "value") else body.type,
        "event": body.event.value if hasattr(body.event, "value") else body.event,
        "recipientPatientId": body.recipientPatientId,
        "recipientGuardianId": body.recipientGuardianId,
        "recipientAddress": body.recipientAddress,
        "message": body.message,
        "sentAt": datetime.utcnow().isoformat() if success else None,
        "status": "SENT" if success else "ERROR",
        "prescriptionId": body.prescriptionId,
    }
    STATE["notifications"][new_id] = record
    return created(record)


@router.get("")
def list_notifications(
    patientId: Optional[str] = None,
    prescriptionId: Optional[str] = None,
    _: dict = Depends(current_user),
):
    items = list(STATE["notifications"].values())
    if patientId:
        items = [n for n in items if n.get("recipientPatientId") == patientId]
    if prescriptionId:
        items = [n for n in items if n.get("prescriptionId") == prescriptionId]
    items = sorted(items, key=lambda n: n.get("sentAt") or "", reverse=True)
    return ok(items)


@router.get("/{notification_id}")
def get_notification(notification_id: str, _: dict = Depends(current_user)):
    n = STATE["notifications"].get(notification_id)
    if not n:
        from fastapi import HTTPException
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Notificación no encontrada"})
    return ok(n)
