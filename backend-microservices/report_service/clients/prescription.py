import os

from shared.http_client import ServiceClient


class PrescriptionServiceClient(ServiceClient):
    def __init__(self) -> None:
        super().__init__(
            base_url=os.getenv("PRESCRIPTION_SERVICE_URL", "http://localhost:8004"),
            service_name="prescription",
        )

    def list_by_status(self, statuses: str, token: str, limit: int = 100) -> dict:
        return self.get(
            "/api/v1/prescriptions",
            token=token,
            params={"status_filter": statuses, "limit": limit},
        )

    def list_all(self, token: str, page_size: int = 200) -> dict:
        first = self.get("/api/v1/prescriptions", token=token,
                         params={"page": 1, "limit": page_size})
        data = (first or {}).get("data") or {}
        items = list(data.get("data") or [])
        total_pages = (data.get("pagination") or {}).get("totalPages", 1)
        for page in range(2, total_pages + 1):
            nxt = self.get("/api/v1/prescriptions", token=token,
                           params={"page": page, "limit": page_size})
            items.extend(((nxt or {}).get("data") or {}).get("data") or [])
        return {"data": items}
