"""Auth stub compartido por los servicios.

Acepta cualquier Bearer y devuelve un usuario stub; en producción cada servicio
validaría el JWT. Un token sandbox-token-USR-XXX resuelve a ese usuario (para probar
flujos por rol); cualquier otro Bearer cae al doctor USR-001.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(
    auto_error=False,
    description=(
        "Sandbox: cualquier valor Bearer es aceptado. "
        "Para testear como un usuario específico, usar el token de su login: "
        "'sandbox-token-USR-001' (doctor), 'sandbox-token-USR-002' (pharmacy_staff), "
        "'sandbox-token-USR-003' (doctor). Otro valor → default doctor."
    ),
)


# Espejo de los usuarios del seed de identity_service, para resolver el usuario
# sin llamar a ese servicio en cada request.
KNOWN_USERS = {
    "USR-001": {
        "id": "USR-001",
        "username": "drperez",
        "rut": "11.111.111-1",
        "fullName": "Dr. Juan Pérez",
        "email": "juan.perez@cesfam.cl",
        "role": "doctor",
    },
    "USR-002": {
        "id": "USR-002",
        "username": "mgonzalez",
        "rut": "22.222.222-2",
        "fullName": "María González",
        "email": "maria.gonzalez@cesfam.cl",
        "role": "pharmacy_staff",
    },
    "USR-003": {
        "id": "USR-003",
        "username": "dralopez",
        "rut": "13.555.444-3",
        "fullName": "Dra. Ana López",
        "email": "ana.lopez@cesfam.cl",
        "role": "doctor",
    },
}

_DEFAULT_USER_ID = "USR-001"
_TOKEN_PREFIX = "sandbox-token-"


def _resolve_user_from_token(token: str) -> dict:
    """Mapea token → usuario. `sandbox-token-USR-XXX` resuelve al usuario; otros → default."""
    if token.startswith(_TOKEN_PREFIX):
        user_id = token[len(_TOKEN_PREFIX):]
        if user_id in KNOWN_USERS:
            return KNOWN_USERS[user_id]
    return KNOWN_USERS[_DEFAULT_USER_ID]


def current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    if not creds or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Falta token Bearer"},
        )
    return _resolve_user_from_token(creds.credentials)


def current_token(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> str:
    """Devuelve el token raw para reenviarlo a otros servicios."""
    if not creds or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Falta token Bearer"},
        )
    return creds.credentials


def require_role(*roles: str):
    def dependency(user: dict = Depends(current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": "El rol del usuario no permite esta operación",
                },
            )
        return user
    return dependency
