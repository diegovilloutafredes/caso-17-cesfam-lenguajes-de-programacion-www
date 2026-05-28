from fastapi import APIRouter
from pydantic import BaseModel

from api_gateway.clients.identity import IdentityServiceClient

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación (Gateway)"])

identity_client = IdentityServiceClient()


class LoginBody(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(body: LoginBody):
    """Login passthrough — el gateway delega en IdentityService."""
    return identity_client.login(body.username, body.password)
