from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from identity_service.db import get_session
from identity_service.models import User
from identity_service.schemas import LoginRequest
from shared.auth import current_user
from shared.envelope import ok

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_session)):
    """Login sandbox: acepta cualquier credencial."""
    user = db.execute(
        select(User).where(User.username == body.username)
    ).scalar_one_or_none() or db.execute(
        select(User).order_by(User.id)
    ).scalars().first()
    return ok({
        "token": f"sandbox-token-{user.id}",
        "user": user.to_dict(),
    })


@router.get("/me")
def me(user: dict = Depends(current_user), db: Session = Depends(get_session)):
    seed_user = db.get(User, user["id"])
    return ok(seed_user.to_dict() if seed_user is not None else user)


@router.post("/validate")
def validate_token(user: dict = Depends(current_user)):
    return ok(user)


@router.post("/logout")
def logout(_user: dict = Depends(current_user)):
    return ok({"message": "Sesión cerrada"})
