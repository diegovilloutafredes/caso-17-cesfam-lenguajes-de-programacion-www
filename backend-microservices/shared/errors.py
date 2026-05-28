"""Manejador uniforme de HTTPException → ApiResponse envelope.

Cada servicio registra este handler al arrancar. Garantiza que cualquier error
HTTP (raise HTTPException(...) en cualquier router) se serialice con la misma
forma de envelope que las respuestas exitosas (`{statusCode, data:null, error,
traceId, timestamp}`).
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from shared.envelope import fail


def register_envelope_handler(app: FastAPI) -> None:
    """Registra el handler global de HTTPException con formato ApiResponse."""

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(request: Request, exc: HTTPException):
        detail = exc.detail
        if isinstance(detail, dict):
            return JSONResponse(
                status_code=exc.status_code,
                content=fail(
                    code=detail.get("code", "ERROR"),
                    message=detail.get("message", str(detail)),
                    status_code=exc.status_code,
                    details=detail.get("details"),
                ),
            )
        return JSONResponse(
            status_code=exc.status_code,
            content=fail(
                code="ERROR", message=str(detail), status_code=exc.status_code
            ),
        )
