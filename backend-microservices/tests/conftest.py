"""Requieren el stack corriendo (make up); URL en GATEWAY_URL."""

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
    r = client.post("/api/v1/auth/login", json={"username": "drperez", "password": "medico2026"})
    return r.json()["data"]["token"]


@pytest.fixture(scope="session")
def pharmacy_token(client):
    r = client.post("/api/v1/auth/login", json={"username": "mgonzalez", "password": "farmacia2026"})
    return r.json()["data"]["token"]


@pytest.fixture
def auth(doctor_token):
    return {"Authorization": f"Bearer {doctor_token}"}


@pytest.fixture
def pharmacy_auth(pharmacy_token):
    return {"Authorization": f"Bearer {pharmacy_token}"}
