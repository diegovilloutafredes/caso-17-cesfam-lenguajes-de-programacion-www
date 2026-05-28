from fastapi import APIRouter, Depends

from identity_service.schemas import LoginRequest
from identity_service.seed import USERS
from shared.auth import current_user
from shared.envelope import ok

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])


@router.post("/login")
def login(body: LoginRequest):
    """Sandbox login: cualquier credencial es aceptada. Retorna token stub."""
    user = next(
        (u for u in USERS.values() if u["username"] == body.username),
        None,
    ) or next(iter(USERS.values()))
    return ok({
        "token": f"sandbox-token-{user['id']}",
        "user": user,
    })


@router.get("/me")
def me(user: dict = Depends(current_user)):
    seed_user = USERS.get(user["id"], user)
    return ok(seed_user)


@router.post("/validate")
def validate_token(user: dict = Depends(current_user)):
    """Endpoint para otros servicios — valida el token y retorna info del user."""
    return ok(user)


@router.post("/logout")
def logout(_user: dict = Depends(current_user)):
    """Cierra sesión. En sandbox solo registra el evento."""
    return ok({"message": "Sesión cerrada"})
