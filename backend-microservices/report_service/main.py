"""ReportService — generación de informes CSV. Agrega datos de Inventory y Prescription."""

from fastapi import FastAPI

from report_service.routers import reports
from shared.errors import register_envelope_handler

app = FastAPI(title="ReportService", version="1.0.0")
register_envelope_handler(app)

app.include_router(reports.router)


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "service": "report_service"}


@app.get("/", include_in_schema=False)
def root():
    return {"service": "ReportService", "port": 8006}
