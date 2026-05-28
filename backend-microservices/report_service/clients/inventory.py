import os

from shared.http_client import ServiceClient


class InventoryServiceClient(ServiceClient):
    def __init__(self) -> None:
        super().__init__(
            base_url=os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8003"),
            service_name="inventory",
        )

    def list_medications(self, token: str, limit: int = 100) -> dict:
        return self.get("/api/v1/medications", token=token, params={"limit": limit})

    def list_batches(self, medication_id: str, token: str) -> dict:
        return self.get(f"/api/v1/medications/{medication_id}/batches", token=token)
