import os

from shared.http_client import ServiceClient


class IdentityServiceClient(ServiceClient):
    def __init__(self) -> None:
        super().__init__(
            base_url=os.getenv("IDENTITY_SERVICE_URL", "http://localhost:8001"),
            service_name="identity",
        )

    def login(self, username: str, password: str) -> dict:
        return self.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )
