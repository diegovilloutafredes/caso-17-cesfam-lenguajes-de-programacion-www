"""Manejador uniforme de HTTPException → ApiResponse envelope.

Cada servicio registra este handler al arrancar. Garantiza que cualquier error
HTTP (raise HTTPException(...) en cualquier router) se serialice con la misma
forma de envelope que las respuestas exitosas (`{statusCode, data:null, error,
traceId, timestamp}`).
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

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

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=fail(
                code="VALIDATION_ERROR",
                message="Datos de entrada inválidos",
                status_code=422,
                details={"errors": jsonable_encoder(exc.errors())},
            ),
        )

    @app.exception_handler(IntegrityError)
    async def _integrity_handler(request: Request, exc: IntegrityError):
        return JSONResponse(
            status_code=409,
            content=fail(
                code="CONFLICT",
                message="Conflicto de datos; reintenta la operación",
                status_code=409,
            ),
        )

    @app.exception_handler(Exception)
    async def _unhandled_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=fail(
                code="INTERNAL_ERROR",
                message="Error interno del servicio",
                status_code=500,
            ),
        )
