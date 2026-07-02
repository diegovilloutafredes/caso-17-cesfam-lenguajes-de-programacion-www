from sqlalchemy import select
from sqlalchemy.orm import Session


def next_id(db: Session, column, prefix: str, start: int = 1, width: int = 3) -> str:
    rows = db.execute(select(column).where(column.like(f"{prefix}%"))).scalars().all()
    existing = [
        int(value[len(prefix):])
        for value in rows
        if isinstance(value, str) and value[len(prefix):].isdigit()
    ]
    nxt = max(existing) + 1 if existing else start
    return f"{prefix}{nxt:0{width}d}"
