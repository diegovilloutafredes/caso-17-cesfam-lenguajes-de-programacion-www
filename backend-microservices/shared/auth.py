"""Auth stub compartido por todos los servicios.

Acepta cualquier Bearer y devuelve un usuario stub. En producción cada servicio
validaría el JWT contra IdentityService o un keyset compartido.

Usa `HTTPBearer` para que Swagger UI muestre el botón **Authorize** 🔓 arriba a la
derecha y ofrezca pegar el token una sola vez para todos los endpoints.

**Resolución del usuario por token**:
- Si el token es `sandbox-token-USR-XXX` (formato emitido por `/auth/login`),
  identifica al usuario por su id → permite testear flujos role-based.
- Cualquier otro Bearer (ej: "x", "test") → fallback al doctor USR-001.
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


# Espejo mínimo de los 3 usuarios del seed de identity_service.
# Necesario acá porque cada servicio NO debería tener que llamar a identity_service
# en cada request solo para resolver al usuario — el stub local cumple el rol.
# En producción esto se reemplaza por validación JWT contra un keyset compartido.
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
