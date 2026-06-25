"""BFF: arma los dashboards de médico y farmacia en una sola llamada.

Médico: estado de las recetas y pacientes recientes. Farmacia: stock, demanda y cola.
Combina datos de inventory, patient y prescription.
"""

from collections import Counter, defaultdict

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

# estados en orden de avance
_PRESCRIPTION_STATES = [
    "SUBMITTED", "RESERVED", "READY_FOR_PICKUP",
    "PICKED_UP", "EXTERNAL_PURCHASE", "CANCELLED", "EXPIRED",
]


def _data(response: dict):
    return response.get("data") if isinstance(response, dict) else None


def _as_list(response: dict) -> list:
    """Extrae la lista de un payload paginado {data:{data:[...]}} o de {data:[...]}."""
    d = _data(response)
    if isinstance(d, dict):
        return d.get("data", []) or []
    return d or []


def _total(response: dict) -> int:
    d = _data(response)
    if isinstance(d, dict):
        return d.get("pagination", {}).get("total", len(d.get("data", [])))
    if isinstance(d, list):
        return len(d)
    return 0


def _stock_status(m: dict) -> str:
    available = m.get("stock", {}).get("availableQuantity", 0)
    if available == 0:
        return "OUT_OF_STOCK"
    if available < m.get("minStock", 0):
        return "LOW_STOCK"
    return "AVAILABLE"


@router.get("/doctor/dashboard")
def doctor_dashboard(
    _user: dict = Depends(current_user),
    token: str = Depends(current_token),
):
    """Médico (clínico): estado de las recetas + pacientes con actividad reciente."""
    prescriptions = _as_list(prescription_client.list_all(token=token))

    counts = Counter(p.get("status") for p in prescriptions)
    prescription_states = [
        {"status": s, "count": counts.get(s, 0)}
        for s in _PRESCRIPTION_STATES if counts.get(s, 0) > 0
    ]

    # reciente = paciente con la última receta emitida más nueva (no por id);
    # los pacientes sin recetas no aparecen.
    last_emission: dict = {}
    for p in prescriptions:
        pid, emitted = p.get("patientId"), p.get("emissionDate")
        if pid and emitted and emitted > last_emission.get(pid, ""):
            last_emission[pid] = emitted
    top_patient_ids = sorted(last_emission, key=lambda k: last_emission[k], reverse=True)[:3]
    recent_patients = []
    for pid in top_patient_ids:
        patient = _data(patient_client.get_patient(pid, token=token))
        if patient:
            recent_patients.append(patient)

    return ok({
        "prescriptionStates": prescription_states,
        "recentPatients": recent_patients,
    })


@router.get("/pharmacy/dashboard")
def pharmacy_dashboard(
    _user: dict = Depends(current_user),
    token: str = Depends(current_token),
):
    """Farmacia (inventario/operación): KPIs + cola + stock + demanda (top recetados)."""
    queue_data = _as_list(prescription_client.queue(token=token))
    pending_resp = prescription_client.list_by_status("SUBMITTED", token=token)
    reserved_resp = prescription_client.list_by_status("RESERVED", token=token)
    ready_resp = prescription_client.list_by_status("READY_FOR_PICKUP", token=token)
    prescriptions = _as_list(prescription_client.list_all(token=token))
    meds = _as_list(inventory_client.list_medications(token=token, limit=50))

    med_name = {m["id"]: m["description"] for m in meds}

    # Top medicamentos recetados (demanda agregada por unidades → prioridad de reposición).
    demand: dict = defaultdict(int)
    for p in prescriptions:
        for item in p.get("items", []):
            demand[item["medicationId"]] += item.get("totalQuantity", 0)
    top = sorted(demand.items(), key=lambda kv: kv[1], reverse=True)[:6]
    top_medications = [
        {"medicationId": mid, "description": med_name.get(mid, mid), "quantity": qty}
        for mid, qty in top
    ]

    return ok({
        "kpis": {
            "pendingPrescriptions": _total(pending_resp),
            "activeReservations": _total(reserved_resp),
            "readyForPickup": _total(ready_resp),
        },
        "queue": [
            {"id": r["id"], "patientId": r["patientId"], "status": r["status"]}
            for r in queue_data[:10]
        ],
        "stockAlerts": _data(inventory_client.low_stock(token=token)) or [],
        "stockSummary": _data(inventory_client.stock_summary(token=token)) or {},
        "stockTop": [
            {
                "id": m["id"], "description": m["description"],
                "available": m["stock"]["availableQuantity"],
                "status": _stock_status(m),
            }
            for m in meds[:6]
        ],
        "topMedications": top_medications,
    })
