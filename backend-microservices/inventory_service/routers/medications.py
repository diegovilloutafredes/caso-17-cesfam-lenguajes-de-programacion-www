from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from inventory_service.db import get_session
from inventory_service.models import Batch, Medication
from inventory_service.schemas import (
    BatchCreate, ConsumeRequest, StockReleaseRequest, StockReserveRequest,
)
from inventory_service.seed import next_id
from shared.auth import current_user
from shared.envelope import created, ok

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
    meds = db.execute(select(Medication)).scalars().all()
    items = [_serialize_med(m) for m in meds]
    if search:
        q = search.lower()
        items = [m for m in items
                 if q in m["description"].lower()
                 or q in m["manufacturer"].lower()
                 or q in m["code"].lower()]
    total = len(items)
    start = max(0, (page - 1) * limit)
    return ok({
        "data": items[start : start + limit],
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
    _: dict = Depends(current_user),
):
    med = db.execute(
        select(Medication).where(Medication.id == medication_id).with_for_update()
    ).scalar_one_or_none()
    if not med:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Medicamento no encontrado"})
    new_id = next_id(db, "BCH")
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
    """Decrementa el físico por las partidas indicadas (al entregar).

    Valida todas las partidas antes de mutar: si una no existe o no alcanza, falla
    sin tocar ningún contador.
    """
    # Fase 1: validación previa, ningún side-effect aún
    batches: dict[str, Batch] = {}
    for alloc in body.allocations:
        batch = db.execute(
            select(Batch).where(Batch.id == alloc.batchId).with_for_update()
        ).scalar_one_or_none()
        if batch is None:
            raise HTTPException(404, detail={
                "code": "BATCH_NOT_FOUND",
                "message": f"Partida no encontrada: {alloc.batchId}",
            })
        if alloc.quantity > batch.availableQuantity:
            raise HTTPException(409, detail={
                "code": "INSUFFICIENT_BATCH",
                "message": f"Partida {alloc.batchId}: {alloc.quantity} excede disponible ({batch.availableQuantity})",
            })
        batches[alloc.batchId] = batch
    # Fase 2: mutación — ya tenemos garantía de que todas las partidas existen
    for alloc in body.allocations:
        batch = batches[alloc.batchId]
        med = db.execute(
            select(Medication).where(Medication.id == batch.medicationId).with_for_update()
        ).scalar_one_or_none()
        if med:
            med.physicalQuantity -= alloc.quantity
            med.reservedQuantity = max(0, med.reservedQuantity - alloc.quantity)
        batch.availableQuantity = max(0, batch.availableQuantity - alloc.quantity)
    db.commit()
    return ok({"consumed": len(body.allocations)})
