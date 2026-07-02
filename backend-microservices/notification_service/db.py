from sqlalchemy.orm import DeclarativeBase, Session

from shared.db import build_session_factory


class Base(DeclarativeBase):
    pass


engine, SessionLocal = build_session_factory()


def get_session():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import models  # noqa: F401  (registra los modelos en Base.metadata)

    Base.metadata.create_all(engine)
