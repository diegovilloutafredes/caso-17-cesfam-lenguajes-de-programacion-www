"""Persistencia síncrona (SQLAlchemy 2.0) compartida por los microservicios.

Cada servicio tiene su propia base PostgreSQL (Database per Service) y define su
propio `Base`; este módulo solo aporta la fábrica de engine + sessionmaker.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def build_session_factory(database_url: str | None = None):
    """Crea (engine, SessionLocal) desde `DATABASE_URL` (o el argumento)."""
    url = database_url or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no configurada para este servicio")
    engine = create_engine(url, pool_pre_ping=True, future=True)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    return engine, SessionLocal
