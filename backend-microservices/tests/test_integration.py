"""Aserciones relativas (antes/después) para poder repetir sin resetear datos."""


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


def test_health(client):
    assert client.get("/health").status_code == 200


def test_login(client):
    d = client.post("/api/v1/auth/login", json={"username": "drperez", "password": "x"}).json()["data"]
    assert d["token"].startswith("sandbox-token-")
    assert d["user"]["role"] == "doctor"


def test_doctor_dashboard(client, auth):
    d = client.get("/api/v1/doctor/dashboard", headers=auth).json()["data"]
    assert {"prescriptionStates", "recentPatients"} <= d.keys()
    assert len(d["recentPatients"]) > 0


def test_pharmacy_dashboard(client, pharmacy_auth):
    d = client.get("/api/v1/pharmacy/dashboard", headers=pharmacy_auth).json()["data"]
    expected = {"kpis", "queue", "stockAlerts", "stockSummary", "stockTop",
                "topMedications", "topMedicationsWindow"}
    assert expected <= d.keys()
    assert d["stockSummary"]["totalMedications"] == 14


def test_pharmacy_top_medications_window(client, pharmacy_auth):
    d = client.get("/api/v1/pharmacy/top-medications?days=90", headers=pharmacy_auth).json()["data"]
    assert d["window"]["days"] == 90
    assert isinstance(d["topMedications"], list)
    allt = client.get("/api/v1/pharmacy/top-medications?days=0", headers=pharmacy_auth).json()["data"]
    assert allt["window"]["days"] == 0


def test_patients_list_via_proxy(client, auth):
    d = client.get("/api/v1/patients", headers=auth).json()["data"]
    assert d["pagination"]["total"] >= 5


def test_medication_detail_via_proxy(client, auth):
    d = client.get("/api/v1/medications/MED-0001", headers=auth).json()["data"]
    assert d["description"] == "Paracetamol 500mg"
    assert {"availableQuantity", "reservedQuantity", "physicalQuantity"} <= d["stock"].keys()


def test_update_patient_persists(client, auth, pharmacy_auth):
    """La edición de la ficha persiste y exige rol de farmacia."""
    before = client.get("/api/v1/patients/PAT-003", headers=auth).json()["data"]
    r = client.put("/api/v1/patients/PAT-003", headers=auth, json={"phone": "+56 9 0000 0000"})
    assert r.status_code == 403
    r = client.put("/api/v1/patients/PAT-003", headers=pharmacy_auth, json={"phone": "+56 9 4040 3030"})
    assert r.status_code == 200
    after = client.get("/api/v1/patients/PAT-003", headers=auth).json()["data"]
    assert after["phone"] == "+56 9 4040 3030"
    client.put("/api/v1/patients/PAT-003", headers=pharmacy_auth, json={"phone": before["phone"]})


def test_guardian_management_cycle(client, auth, pharmacy_auth):
    """Registrar, duplicar (rechazado), retirar con el apoderado y quitarlo."""
    body = {"rut": "9.876.543-3", "firstName": "Rosa", "lastName": "Ramírez",
            "relationship": "Hija", "phone": "+56 9 5555 4444"}
    r = client.post("/api/v1/patients/PAT-002/guardians", headers=pharmacy_auth, json=body)
    assert r.status_code == 201
    gid = r.json()["data"]["id"]
    assert r.json()["data"]["authorizationDate"]  # default: hoy

    dup = client.post("/api/v1/patients/PAT-002/guardians", headers=pharmacy_auth, json=body)
    assert dup.json()["error"]["code"] == "DUPLICATE_GUARDIAN"
    assert client.post("/api/v1/patients/PAT-002/guardians", headers=auth, json=body).status_code == 403

    # el apoderado recién registrado puede retirar una receta del paciente
    rid = _create(client, auth, [_item("MED-0001", 3)]).json()["data"]["id"]
    client.post(f"/api/v1/prescriptions/{rid}/prepare", headers=pharmacy_auth)
    delivered = client.post(
        f"/api/v1/prescriptions/{rid}/deliver", headers=pharmacy_auth,
        json={"pickerType": "guardian", "guardianId": gid,
              "batches": [{"batchId": "BCH-001", "quantity": 3}]},
    ).json()["data"]
    assert delivered["status"] == "PICKED_UP"
    assert delivered["delivery"]["guardianId"] == gid

    r = client.delete(f"/api/v1/patients/PAT-002/guardians/{gid}", headers=pharmacy_auth)
    assert r.status_code == 200
    ids = {g["id"] for g in client.get("/api/v1/patients/PAT-002/guardians", headers=auth).json()["data"]}
    assert gid not in ids


def test_full_flow_create_prepare_deliver(client, auth, pharmacy_auth):
    before = _stock(client, auth)
    r = _create(client, auth, [_item("MED-0001", 10)])
    assert r.json()["data"]["status"] == "SUBMITTED"
    rid = r.json()["data"]["id"]

    prepared = client.post(f"/api/v1/prescriptions/{rid}/prepare", headers=pharmacy_auth).json()["data"]
    assert prepared["status"] == "READY_FOR_PICKUP"
    mid = _stock(client, auth)
    assert mid["availableQuantity"] == before["availableQuantity"] - 10
    assert mid["reservedQuantity"] == before["reservedQuantity"] + 10

    delivered = client.post(
        f"/api/v1/prescriptions/{rid}/deliver", headers=pharmacy_auth,
        json={"pickerType": "patient", "batches": [{"batchId": "BCH-001", "quantity": 10}]},
    ).json()["data"]
    assert delivered["status"] == "PICKED_UP"
    after = _stock(client, auth)
    assert after["physicalQuantity"] == before["physicalQuantity"] - 10


def test_create_with_unknown_patient(client, auth):
    err = _create(client, auth, [_item("MED-0001", 5)], patient="PAT-999").json()["error"]
    assert err["code"] == "PATIENT_NOT_FOUND"


def test_compensation_on_partial_prepare(client, auth, pharmacy_auth):
    before = _stock(client, auth, "MED-0001")
    rid = _create(client, auth, [_item("MED-0001", 5), _item("MED-0003", 5)]).json()["data"]["id"]

    err = client.post(f"/api/v1/prescriptions/{rid}/prepare", headers=pharmacy_auth).json()["error"]
    assert err["code"] == "INSUFFICIENT_STOCK"
    assert err["details"]["medicationId"] == "MED-0003"

    after = _stock(client, auth, "MED-0001")
    assert after == before  # la línea 1 quedó liberada
    status = client.get(f"/api/v1/prescriptions/{rid}", headers=auth).json()["data"]["status"]
    assert status == "SUBMITTED"


def test_cancel_releases_reserved_stock(client, auth, pharmacy_auth):
    before = _stock(client, auth, "MED-0001")
    rid = _create(client, auth, [_item("MED-0001", 7)]).json()["data"]["id"]
    client.post(f"/api/v1/prescriptions/{rid}/prepare", headers=pharmacy_auth)  # reserva 7
    cancelled = client.post(
        f"/api/v1/prescriptions/{rid}/cancel", headers=auth, json={"reason": "prueba"},
    ).json()["data"]
    assert cancelled["status"] == "CANCELLED"
    after = _stock(client, auth, "MED-0001")
    assert after == before  # al cancelar desde READY_FOR_PICKUP se libera el stock


def test_invalid_transition_deliver_submitted(client, auth, pharmacy_auth):
    rid = _create(client, auth, [_item("MED-0001", 3)]).json()["data"]["id"]
    err = client.post(
        f"/api/v1/prescriptions/{rid}/deliver", headers=pharmacy_auth,
        json={"pickerType": "patient", "batches": [{"batchId": "BCH-001", "quantity": 3}]},
    ).json()["error"]
    assert err["code"] == "INVALID_STATE"


def test_reserve_insufficient_stock_direct(client, auth, pharmacy_auth):
    rid = _create(client, auth, [_item("MED-0003", 5)]).json()["data"]["id"]
    err = client.post(f"/api/v1/prescriptions/{rid}/prepare", headers=pharmacy_auth).json()["error"]
    assert err["code"] == "INSUFFICIENT_STOCK"


def test_deliver_rejects_wrong_medication_batch(client, auth, pharmacy_auth):
    """Las partidas entregadas deben ser del medicamento recetado."""
    rid = _create(client, auth, [_item("MED-0001", 10)]).json()["data"]["id"]
    client.post(f"/api/v1/prescriptions/{rid}/prepare", headers=pharmacy_auth)
    err = client.post(
        f"/api/v1/prescriptions/{rid}/deliver", headers=pharmacy_auth,
        json={"pickerType": "patient", "batches": [{"batchId": "BCH-006", "quantity": 10}]},
    ).json()["error"]  # BCH-006 es de MED-0007
    assert err["code"] == "ALLOCATION_MISMATCH"
    client.post(f"/api/v1/prescriptions/{rid}/cancel", headers=pharmacy_auth,
                json={"reason": "limpieza"})


def test_deliver_rejects_foreign_guardian(client, auth, pharmacy_auth):
    """El apoderado debe pertenecer al paciente de la receta."""
    rid = _create(client, auth, [_item("MED-0001", 4)]).json()["data"]["id"]
    client.post(f"/api/v1/prescriptions/{rid}/prepare", headers=pharmacy_auth)
    err = client.post(
        f"/api/v1/prescriptions/{rid}/deliver", headers=pharmacy_auth,
        json={"pickerType": "guardian", "guardianId": "GRD-999",
              "batches": [{"batchId": "BCH-001", "quantity": 4}]},
    ).json()["error"]
    assert err["code"] == "INVALID_GUARDIAN"
    client.post(f"/api/v1/prescriptions/{rid}/cancel", headers=pharmacy_auth,
                json={"reason": "limpieza"})


def test_consume_rejects_expired_batch(client, pharmacy_auth):
    """No se entrega desde una partida vencida (BCH-003 venció en junio 2026)."""
    r = client.post(
        "/api/v1/medications/consume", headers=pharmacy_auth,
        json={"allocations": [{"batchId": "BCH-003", "quantity": 1}],
              "expectedItems": [{"medicationId": "MED-0004", "quantity": 1}]},
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "EXPIRED_BATCH"


def test_consume_validates_aggregate_per_batch(client, pharmacy_auth):
    """Dos asignaciones a la misma partida se validan por su suma, no por separado."""
    batches = client.get(
        "/api/v1/medications/MED-0007/batches", headers=pharmacy_auth,
    ).json()["data"]
    available = next(b["availableQuantity"] for b in batches if b["id"] == "BCH-006")
    assert available > 0
    r = client.post(
        "/api/v1/medications/consume", headers=pharmacy_auth,
        json={"allocations": [
            {"batchId": "BCH-006", "quantity": available},
            {"batchId": "BCH-006", "quantity": available},
        ], "expectedItems": [{"medicationId": "MED-0007", "quantity": available * 2}]},
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "INSUFFICIENT_BATCH"


def test_role_enforcement(client, auth, pharmacy_auth):
    """Farmacia no emite recetas; el médico no da de baja stock."""
    assert _create(client, pharmacy_auth, [_item("MED-0001", 1)]).status_code == 403
    r = client.post(
        "/api/v1/batches/BCH-006/write-off", headers=auth,
        json={"reason": "DAMAGED", "quantity": 1, "discard": False},
    )
    assert r.status_code == 403


def test_reserved_matches_ready_prescriptions(client, auth):
    """reserved = suma de items READY_FOR_PICKUP; RESERVED no retiene stock."""
    ready = client.get(
        "/api/v1/prescriptions?status_filter=READY_FOR_PICKUP&limit=200", headers=auth,
    ).json()["data"]["data"]
    expected: dict = {}
    for rx in ready:
        for it in rx["items"]:
            expected[it["medicationId"]] = expected.get(it["medicationId"], 0) + it["totalQuantity"]
    meds = client.get("/api/v1/medications?limit=50", headers=auth).json()["data"]["data"]
    for m in meds:
        assert m["stock"]["reservedQuantity"] == expected.get(m["id"], 0), m["id"]


def test_write_off_preserves_invariant(client, auth, pharmacy_auth):
    """Una baja retira físico: mantiene physical = available + reserved."""
    before = _stock(client, auth, "MED-0007")
    r = client.post(
        "/api/v1/batches/BCH-006/write-off", headers=pharmacy_auth,
        json={"reason": "DAMAGED", "quantity": 5, "discard": False, "notes": "prueba"},
    )
    assert r.status_code == 200
    after = _stock(client, auth, "MED-0007")
    assert after["physicalQuantity"] == before["physicalQuantity"] - 5
    assert after["availableQuantity"] == before["availableQuantity"] - 5
    assert after["physicalQuantity"] == after["availableQuantity"] + after["reservedQuantity"]


def test_deliver_requires_full_quantity(client, auth, pharmacy_auth):
    rid = _create(client, auth, [_item("MED-0001", 10)]).json()["data"]["id"]
    client.post(f"/api/v1/prescriptions/{rid}/prepare", headers=pharmacy_auth)  # READY, reserva 10
    err = client.post(
        f"/api/v1/prescriptions/{rid}/deliver", headers=pharmacy_auth,
        json={"pickerType": "patient", "batches": [{"batchId": "BCH-001", "quantity": 7}]},
    ).json()["error"]
    assert err["code"] == "QUANTITY_MISMATCH"
    client.post(f"/api/v1/prescriptions/{rid}/cancel", headers=pharmacy_auth, json={"reason": "limpieza"})


def test_prescription_trend(client, auth):
    d = client.get(
        "/api/v1/analytics/prescription-trend?dateFrom=2026-04-01&dateTo=2026-06-30",
        headers=auth,
    ).json()["data"]
    assert "series" in d and len(d["series"]) > 0
    assert d["totals"]["emission"] >= 6
