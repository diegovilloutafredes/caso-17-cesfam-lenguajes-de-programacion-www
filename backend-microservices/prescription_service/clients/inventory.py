import os
from typing import List

from shared.http_client import ServiceClient


class InventoryServiceClient(ServiceClient):
    def __init__(self) -> None:
        super().__init__(
            base_url=os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8003"),
            service_name="inventory",
        )

    def get_medication(self, med_id: str, token: str) -> dict:
        return self.get(f"/api/v1/medications/{med_id}", token=token)

    def reserve_stock(self, med_id: str, quantity: int, token: str) -> dict:
        return self.post(
            f"/api/v1/medications/{med_id}/reserve",
            token=token,
            json={"quantity": quantity},
        )

    def release_stock(self, med_id: str, quantity: int, token: str) -> dict:
        return self.post(
            f"/api/v1/medications/{med_id}/release",
            token=token,
            json={"quantity": quantity},
        )

    def consume(self, allocations: List[dict], token: str) -> dict:
        return self.post(
            "/api/v1/medications/consume",
            token=token,
            json={"allocations": allocations},
        )
