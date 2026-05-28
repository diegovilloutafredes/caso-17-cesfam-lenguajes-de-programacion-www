import os

from shared.http_client import ServiceClient


class PrescriptionServiceClient(ServiceClient):
    def __init__(self) -> None:
        super().__init__(
            base_url=os.getenv("PRESCRIPTION_SERVICE_URL", "http://localhost:8004"),
            service_name="prescription",
        )

    def queue(self, token: str) -> dict:
        return self.get("/api/v1/prescriptions/queue", token=token)

    def list_by_status(self, statuses: str, token: str) -> dict:
        return self.get(
            "/api/v1/prescriptions",
            token=token,
            params={"status_filter": statuses, "limit": 100},
        )
