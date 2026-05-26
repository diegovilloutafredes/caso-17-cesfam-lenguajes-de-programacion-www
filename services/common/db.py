import os
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@db:5432/backend"
)


engine = None
SessionLocal: Optional[sessionmaker] = None
Base = declarative_base()

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception:
    engine = None
    SessionLocal = None


def create_tables():
    """Create DB tables for all models that inherit from Base.

    If no engine is available (sandbox mode), this is a no-op.
    """
    if engine is None:
        return
    Base.metadata.create_all(bind=engine)
