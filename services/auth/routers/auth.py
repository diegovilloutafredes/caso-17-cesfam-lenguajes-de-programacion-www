from fastapi import APIRouter, Depends

from services.auth.schemas.auth import LoginRequest, LoginResponse, User
from services.auth.schemas.common import MessageResponse
from data import STATE
from services.common.deps import current_user

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    """Login sandbox: acepta cualquier credencial, devuelve un token stub."""
    user = next(
        (u for u in STATE["users"].values() if u["username"] == body.username),
        None,
    )
    if user is None:
        user = next(iter(STATE["users"].values()))
    return {
        "token": f"sandbox-token-{user['id']}",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "rut": user.get("rut", ""),
            "fullName": user["fullName"],
            "email": user.get("email"),
            "role": user["role"],
        },
    }


@router.post("/logout", response_model=MessageResponse)
def logout(_: dict = Depends(current_user)):
    return {"message": "Sesión cerrada"}


@router.get("/me", response_model=User)
def me(user: dict = Depends(current_user)):
    seed_user = STATE["users"].get(user["id"], user)
    return {
        "id": seed_user["id"],
        "username": seed_user["username"],
        "rut": seed_user.get("rut", ""),
        "fullName": seed_user["fullName"],
        "email": seed_user.get("email"),
        "role": seed_user["role"],
    }
