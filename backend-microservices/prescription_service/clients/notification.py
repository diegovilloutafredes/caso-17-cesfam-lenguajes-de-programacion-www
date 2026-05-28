import os

from shared.http_client import ServiceClient


class NotificationServiceClient(ServiceClient):
    def __init__(self) -> None:
        super().__init__(
            base_url=os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8005"),
            service_name="notification",
        )

    def send(self, body: dict, token: str) -> dict:
        return self.post("/api/v1/notifications", token=token, json=body)
