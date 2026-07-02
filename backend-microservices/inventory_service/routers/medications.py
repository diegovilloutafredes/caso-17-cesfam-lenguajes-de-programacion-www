from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from inventory_service.db import get_session
from inventory_service.models import Batch, Medication
from inventory_service.schemas import (
    BatchCreate, ConsumeRequest, StockReleaseRequest, StockReserveRequest,
)
from shared.auth import current_user, require_role
from shared.envelope import created, ok
from shared.ids import next_id

router = APIRouter(prefix="/api/v1/medications", tags=["Medicamentos"])


def _serialize_med(med: Medication) -> dict:
    return {
        "id": med.id,
        "code": med.code,
        "description": med.description,
        "manufacturer": med.manufacturer,
        "type": med.type,
        "components": med.components,
        "content": med.content,
        "packaging": med.packaging,
        "minStock": med.minStock,
        "stock": {
            "availableQuantity": med.availableQuantity,
            "reservedQuantity": med.reservedQuantity,
            "physicalQuantity": med.physicalQuantity,
        },
    }


def _serialize_batch(batch: Batch) -> dict:
    return {
        "id": batch.id,
        "medicationId": batch.medicationId,
        "batchNumber": batch.batchNumber,
        "arrivalDate": batch.arrivalDate,
        "expirationDate": batch.expirationDate,
        "initialQuantity": batch.initialQuantity,
        "availableQuantity": batch.availableQuantity,
    }


def _stock_status(med: Medication) -> str:
    available = med.availableQuantity
    if available == 0:
        return "OUT_OF_STOCK"
    if available < med.minStock:
        return "LOW_STOCK"
    return "AVAILABLE"


@router.get("")
def list_medications(
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_session),
    _: dict = Depends(current_user),
):
    stmt = select(Medication)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(
            Medication.description.ilike(like),
            Medication.manufacturer.ilike(like),
            Medication.code.ilike(like),
        ))
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = db.execute(
        stmt.order_by(Medication.id).offset(max(0, (page - 1) * limit)).limit(limit)
    ).scalars().all()
    return ok({
        "data": [_serialize_med(m) for m in rows],
        "pagination": {
            "page": page, "limit": limit, "total": total,
            "totalPages": (total + limit - 1) // limit if total else 0,
        },
    })


@router.get("/stock-summary")
def stock_summary(
    db: Session = Depends(get_session),
    _: dict = Depends(current_user),
):
    meds = db.execute(select(Medication)).scalars().all()
    available = low = out = 0
    for m in meds:
        s = _stock_status(m)
        if s == "AVAILABLE":
            available += 1
        elif s == "LOW_STOCK":
            low += 1
        else:
            out += 1
    return ok({
        "available": available, "lowStock": low,
        "outOfStock": out, "totalMedications": len(meds),
    })


@router.get("/low-stock")
def low_stock(
    db: Session = Depends(get_session),
    _: dict = Depends(current_user),
):
    meds = db.execute(select(Medication)).scalars().all()
    return ok([
        {**_serialize_med(m), "status": _stock_status(m)}
        for m in meds
        if _stock_status(m) != "AVAILABLE"
    ])


@router.get("/{medication_id}")
def get_medication(
    medication_id: str,
    db: Session = Depends(get_session),
    _: dict = Depends(current_user),
):
    m = db.get(Medication, medication_id)
    if not m:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Medicamento no encontrado"})
    batches = db.execute(
        select(Batch).where(Batch.medicationId == medication_id)
    ).scalars().all()
    return ok({**_serialize_med(m), "batches": [_serialize_batch(b) for b in batches]})


@router.get("/{medication_id}/batches")
def list_batches(
    medication_id: str,
    db: Session = Depends(get_session),
    _: dict = Depends(current_user),
):
    if not db.get(Medication, medication_id):
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Medicamento no encontrado"})
    batches = db.execute(
        select(Batch).where(Batch.medicationId == medication_id)
    ).scalars().all()
    return ok([_serialize_batch(b) for b in batches])


@router.post("/{medication_id}/batches", status_code=status.HTTP_201_CREATED)
def add_batch(
    medication_id: str,
    body: BatchCreate,
    db: Session = Depends(get_session),
    _: dict = Depends(require_role("pharmacy_staff")),
):
    med = db.execute(
        select(Medication).where(Medication.id == medication_id).with_for_update()
    ).scalar_one_or_none()
    if not med:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Medicamento no encontrado"})
    new_id = next_id(db, Batch.id, "BCH-")
    batch = Batch(
        id=new_id,
        medicationId=medication_id,
        batchNumber=body.batchNumber,
        arrivalDate=date.today(),
        expirationDate=body.expirationDate,
        initialQuantity=body.initialQuantity,
        availableQuantity=body.initialQuantity,
    )
    db.add(batch)
    med.availableQuantity += body.initialQuantity
    med.physicalQuantity += body.initialQuantity
    db.commit()
    return created(_serialize_batch(batch))


# --- Inter-service operations ---

@router.post("/{medication_id}/reserve")
def reserve_stock(
    medication_id: str,
    body: StockReserveRequest,
    db: Session = Depends(get_session),
    _: dict = Depends(current_user),
):
    """Mueve `quantity` de available → reserved. Llamado por PrescriptionService."""
    med = db.execute(
        select(Medication).where(Medication.id == medication_id).with_for_update()
    ).scalar_one_or_none()
    if not med:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Medicamento no encontrado"})
    if med.availableQuantity < body.quantity:
        raise HTTPException(409, detail={
            "code": "INSUFFICIENT_STOCK",
            "message": f"Stock disponible ({med.availableQuantity}) menor a solicitado ({body.quantity})",
        })
    med.availableQuantity -= body.quantity
    med.reservedQuantity += body.quantity
    db.commit()
    return ok({"medicationId": medication_id, "reservedQuantity": body.quantity})


@router.post("/{medication_id}/release")
def release_stock(
    medication_id: str,
    body: StockReleaseRequest,
    db: Session = Depends(get_session),
    _: dict = Depends(current_user),
):
    """Mueve `quantity` de reserved → available. Llamado por PrescriptionService al cancelar."""
    med = db.execute(
        select(Medication).where(Medication.id == medication_id).with_for_update()
    ).scalar_one_or_none()
    if not med:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Medicamento no encontrado"})
    qty = min(body.quantity, med.reservedQuantity)
    med.reservedQuantity -= qty
    med.availableQuantity += qty
    db.commit()
    return ok({"medicationId": medication_id, "releasedQuantity": qty})


@router.post("/consume")
def consume_physical(
    body: ConsumeRequest,
    db: Session = Depends(get_session),
    _: dict = Depends(current_user),
):
    # valida todo antes de mutar, sobre cantidades agregadas por partida
    today = date.today()
    per_batch: dict[str, int] = {}
    for alloc in body.allocations:
        per_batch[alloc.batchId] = per_batch.get(alloc.batchId, 0) + alloc.quantity

    batches: dict[str, Batch] = {}
    for batch_id in sorted(per_batch):
        qty = per_batch[batch_id]
        batch = db.execute(
            select(Batch).where(Batch.id == batch_id).with_for_update()
        ).scalar_one_or_none()
        if batch is None:
            raise HTTPException(404, detail={
                "code": "BATCH_NOT_FOUND",
                "message": f"Partida no encontrada: {batch_id}",
            })
        if batch.expirationDate < today:
            raise HTTPException(409, detail={
                "code": "EXPIRED_BATCH",
                "message": f"Partida {batch_id} vencida el {batch.expirationDate.isoformat()}",
            })
        if qty > batch.availableQuantity:
            raise HTTPException(409, detail={
                "code": "INSUFFICIENT_BATCH",
                "message": f"Partida {batch_id}: {qty} excede disponible ({batch.availableQuantity})",
            })
        batches[batch_id] = batch

    per_med: dict[str, int] = {}
    for batch_id, qty in per_batch.items():
        med_id = batches[batch_id].medicationId
        per_med[med_id] = per_med.get(med_id, 0) + qty

    if body.expectedItems is not None:
        expected: dict[str, int] = {}
        for item in body.expectedItems:
            expected[item.medicationId] = expected.get(item.medicationId, 0) + item.quantity
        if per_med != expected:
            raise HTTPException(409, detail={
                "code": "ALLOCATION_MISMATCH",
                "message": "Las partidas asignadas no corresponden a los medicamentos recetados",
                "details": {"expected": expected, "provided": per_med},
            })

    meds: dict[str, Medication] = {}
    for med_id in sorted(per_med):
        med = db.execute(
            select(Medication).where(Medication.id == med_id).with_for_update()
        ).scalar_one_or_none()
        if med is None:
            raise HTTPException(404, detail={
                "code": "NOT_FOUND",
                "message": f"Medicamento no encontrado: {med_id}",
            })
        if per_med[med_id] > med.reservedQuantity:
            raise HTTPException(409, detail={
                "code": "INSUFFICIENT_RESERVED",
                "message": f"{med_id}: el consumo ({per_med[med_id]}) excede lo reservado ({med.reservedQuantity})",
            })
        meds[med_id] = med

    for batch_id, qty in per_batch.items():
        batches[batch_id].availableQuantity -= qty
    for med_id, qty in per_med.items():
        meds[med_id].physicalQuantity -= qty
        meds[med_id].reservedQuantity -= qty
    db.commit()
    return ok({"consumed": len(body.allocations)})
