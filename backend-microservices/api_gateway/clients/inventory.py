import os

from shared.http_client import ServiceClient


class InventoryServiceClient(ServiceClient):
    def __init__(self) -> None:
        super().__init__(
            base_url=os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8003"),
            service_name="inventory",
        )

    def stock_summary(self, token: str) -> dict:
        return self.get("/api/v1/medications/stock-summary", token=token)

    def list_medications(self, token: str, limit: int = 6) -> dict:
        return self.get("/api/v1/medications", token=token, params={"limit": limit})

    def low_stock(self, token: str) -> dict:
        return self.get("/api/v1/medications/low-stock", token=token)
