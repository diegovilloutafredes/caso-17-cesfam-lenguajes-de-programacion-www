import os

from shared.http_client import ServiceClient


class PrescriptionServiceClient(ServiceClient):
    """Cliente HTTP de patient_service → prescription_service.

    Usado por GET /patients/{id}/history para obtener prescripciones del paciente
    (que viven en prescription_service, no en patient_service por bounded contexts).
    """

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
