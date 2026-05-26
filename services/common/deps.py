"""Dependencias compartidas por los routers (migrado desde routers/deps.py)."""

from typing import Annotated
from fastapi import Header, HTTPException, status


def current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    """Auth stub: cualquier token Bearer es aceptado; devuelve un usuario genérico.

    En un backend real esto decodificaría y validaría un JWT.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Falta token Bearer"}},
        )
    return {
        "id": "USR-001",
        "username": "drperez",
        "rut": "11.111.111-1",
        "fullName": "Dr. Juan Pérez",
        "role": "doctor",
    }


def pagination_params(page: int = 1, limit: int = 20) -> tuple[int, int]:
    if page < 1:
        page = 1
    if limit < 1:
        limit = 1
    if limit > 100:
        limit = 100
    return page, limit


def paginate(items: list, page: int, limit: int) -> dict:
    total = len(items)
    start = (page - 1) * limit
    end = start + limit
    return {
        "data": items[start:end],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit if total else 0,
        },
    }
