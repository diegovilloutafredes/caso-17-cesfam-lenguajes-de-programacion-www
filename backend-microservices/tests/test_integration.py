"""Tests de integración cross-service (entran por el ApiGateway).

Cubren el flujo feliz extremo a extremo y, sobre todo, los CAMINOS DE FALLA donde
cambió la frontera transaccional al pasar a microservicios: compensación en una
preparación parcial, liberación al cancelar, y transición inválida. Las aserciones
son relativas (antes/después) para ser repetibles sin reiniciar el estado.
"""


def _item(med, qty):
    return {
        "medicationId": med, "dosesPerInterval": 1, "intervalHours": 8,
        "doseDescription": "1 c/8h", "durationDays": 7, "totalQuantity": qty,
    }


def _stock(client, auth, med="MED-0001"):
    return client.get(f"/api/v1/medications/{med}", headers=auth).json()["data"]["stock"]


def _create(client, auth, items, patient="PAT-002"):
    return client.post("/api/v1/prescriptions", headers=auth, json={
        "patientId": patient, "treatmentType": "SHORT", "durationDays": 7,
        "pickupDeadline": "2026-07-20", "items": items,
    })


# --- Salud y autenticación -------------------------------------------------

def test_health(client):
    assert client.get("/health").status_code == 200


def test_login(client):
    d = client.post("/api/v1/auth/login", json={"username": "drperez", "password": "x"}).json()["data"]
    assert d["token"].startswith("sandbox-token-")
    assert d["user"]["role"] == "doctor"


# --- BFF (agregación cross-service) ----------------------------------------

def test_doctor_dashboard(client, auth):
    d = client.get("/api/v1/doctor/dashboard", headers=auth).json()["data"]
    assert {"stockSummary", "recentPatients", "stockTop"} <= d.keys()
    assert d["stockSummary"]["totalMedications"] == 7


def test_pharmacy_dashboard(client, pharmacy_auth):
    d = client.get("/api/v1/pharmacy/dashboard", headers=pharmacy_auth).json()["data"]
    assert {"kpis", "queue", "stockAlerts"} <= d.keys()


# --- Proxy a servicios de dominio ------------------------------------------

def test_patients_list_via_proxy(client, auth):
    d = client.get("/api/v1/patients", headers=auth).json()["data"]
    assert d["pagination"]["total"] >= 5


def test_medication_detail_via_proxy(client, auth):
    d = client.get("/api/v1/medications/MED-0001", headers=auth).json()["data"]
    assert d["description"] == "Paracetamol 500mg"
    assert {"availableQuantity", "reservedQuantity", "physicalQuantity"} <= d["stock"].keys()


# --- Flujo feliz extremo a extremo -----------------------------------------

def test_full_flow_create_prepare_deliver(client, auth):
    before = _stock(client, auth)
    r = _create(client, auth, [_item("MED-0001", 10)])
    assert r.json()["data"]["status"] == "SUBMITTED"
    rid = r.json()["data"]["id"]

    prepared = client.post(f"/api/v1/prescriptions/{rid}/prepare", headers=auth).json()["data"]
    assert prepared["status"] == "READY_FOR_PICKUP"
    mid = _stock(client, auth)
    assert mid["availableQuantity"] == before["availableQuantity"] - 10
    assert mid["reservedQuantity"] == before["reservedQuantity"] + 10

    delivered = client.post(
        f"/api/v1/prescriptions/{rid}/deliver", headers=auth,
        json={"pickerType": "patient", "batches": [{"batchId": "BCH-001", "quantity": 10}]},
    ).json()["data"]
    assert delivered["status"] == "PICKED_UP"
    after = _stock(client, auth)
    assert after["physicalQuantity"] == before["physicalQuantity"] - 10


# --- Caminos de falla (lo crítico al pasar a microservicios) ----------------

def test_create_with_unknown_patient(client, auth):
    err = _create(client, auth, [_item("MED-0001", 5)], patient="PAT-999").json()["error"]
    assert err["code"] == "PATIENT_NOT_FOUND"


def test_compensation_on_partial_prepare(client, auth):
    """Stock insuficiente en la 2ª línea: la 1ª (ya reservada) debe liberarse."""
    before = _stock(client, auth, "MED-0001")
    rid = _create(client, auth, [_item("MED-0001", 5), _item("MED-0003", 5)]).json()["data"]["id"]

    err = client.post(f"/api/v1/prescriptions/{rid}/prepare", headers=auth).json()["error"]
    assert err["code"] == "INSUFFICIENT_STOCK"
    assert err["details"]["medicationId"] == "MED-0003"

    after = _stock(client, auth, "MED-0001")
    assert after == before  # la reserva de la línea 1 fue compensada (liberada)
    status = client.get(f"/api/v1/prescriptions/{rid}", headers=auth).json()["data"]["status"]
    assert status == "SUBMITTED"


def test_cancel_releases_reserved_stock(client, auth):
    before = _stock(client, auth, "MED-0001")
    rid = _create(client, auth, [_item("MED-0001", 7)]).json()["data"]["id"]
    client.post(f"/api/v1/prescriptions/{rid}/prepare", headers=auth)  # reserva 7
    cancelled = client.post(
        f"/api/v1/prescriptions/{rid}/cancel", headers=auth, json={"reason": "prueba"},
    ).json()["data"]
    assert cancelled["status"] == "CANCELLED"
    after = _stock(client, auth, "MED-0001")
    assert after == before  # al cancelar desde READY_FOR_PICKUP se libera el stock


def test_invalid_transition_deliver_submitted(client, auth):
    rid = _create(client, auth, [_item("MED-0001", 3)]).json()["data"]["id"]
    err = client.post(
        f"/api/v1/prescriptions/{rid}/deliver", headers=auth,
        json={"pickerType": "patient", "batches": [{"batchId": "BCH-001", "quantity": 3}]},
    ).json()["error"]
    assert err["code"] == "INVALID_STATE"


def test_reserve_insufficient_stock_direct(client, auth):
    rid = _create(client, auth, [_item("MED-0003", 5)]).json()["data"]["id"]
    err = client.post(f"/api/v1/prescriptions/{rid}/prepare", headers=auth).json()["error"]
    assert err["code"] == "INSUFFICIENT_STOCK"


# --- Reportería C8 ----------------------------------------------------------

def test_prescription_trend(client, auth):
    d = client.get(
        "/api/v1/analytics/prescription-trend?dateFrom=2026-04-01&dateTo=2026-06-30",
        headers=auth,
    ).json()["data"]
    assert "series" in d and len(d["series"]) > 0
    assert d["totals"]["emission"] >= 6
