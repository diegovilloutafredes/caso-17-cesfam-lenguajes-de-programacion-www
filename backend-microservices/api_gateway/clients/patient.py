import os

from shared.http_client import ServiceClient


class PatientServiceClient(ServiceClient):
    def __init__(self) -> None:
        super().__init__(
            base_url=os.getenv("PATIENT_SERVICE_URL", "http://localhost:8002"),
            service_name="patient",
        )

    def list_recent(self, token: str, limit: int = 3) -> dict:
        return self.get("/api/v1/patients/recent", token=token, params={"limit": limit})

    def get_patient(self, patient_id: str, token: str) -> dict:
        return self.get(f"/api/v1/patients/{patient_id}", token=token)
