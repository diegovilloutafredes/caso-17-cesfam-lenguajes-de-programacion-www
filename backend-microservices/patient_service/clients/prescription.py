import os

from shared.http_client import ServiceClient


class PrescriptionServiceClient(ServiceClient):
    def __init__(self) -> None:
        super().__init__(
            base_url=os.getenv("PRESCRIPTION_SERVICE_URL", "http://localhost:8004"),
            service_name="prescription",
        )

    def list_for_patient(self, patient_id: str, token: str) -> dict:
        return self.get(
            "/api/v1/prescriptions",
            token=token,
            params={"patientId": patient_id, "limit": 100},
        )
