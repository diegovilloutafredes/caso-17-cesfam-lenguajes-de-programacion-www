from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api_gateway.clients.identity import IdentityServiceClient

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación (Gateway)"])

identity_client = IdentityServiceClient()


class LoginBody(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(body: LoginBody):
    response = identity_client.login(body.username, body.password)
    if response.get("error"):
        return JSONResponse(
            status_code=response.get("statusCode", 502), content=response,
        )
    return response
