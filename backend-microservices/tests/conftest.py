"""Fixtures para los tests de integración cross-service.

Los tests corren contra el sistema levantado (docker-compose), entrando por el
ApiGateway (BFF). La URL se toma de GATEWAY_URL (default localhost:8000).
"""

import os

import httpx
import pytest

BASE = os.getenv("GATEWAY_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE, timeout=15.0) as c:
        yield c


@pytest.fixture(scope="session")
def doctor_token(client):
    r = client.post("/api/v1/auth/login", json={"username": "drperez", "password": "x"})
    return r.json()["data"]["token"]


@pytest.fixture(scope="session")
def pharmacy_token(client):
    r = client.post("/api/v1/auth/login", json={"username": "mgonzalez", "password": "x"})
    return r.json()["data"]["token"]


@pytest.fixture
def auth(doctor_token):
    return {"Authorization": f"Bearer {doctor_token}"}


@pytest.fixture
def pharmacy_auth(pharmacy_token):
    return {"Authorization": f"Bearer {pharmacy_token}"}
