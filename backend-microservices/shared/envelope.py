from datetime import datetime
from typing import Any, Generic, Optional, TypeVar
import uuid

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None


class ApiResponse(BaseModel, Generic[T]):
    statusCode: int
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    traceId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


def ok(data: Any = None, status_code: int = 200) -> dict:
    return ApiResponse(statusCode=status_code, data=data).model_dump()


def created(data: Any) -> dict:
    return ok(data, status_code=201)


def fail(code: str, message: str, status_code: int = 400,
         details: Optional[dict] = None) -> dict:
    """Usar dentro de JSONResponse."""
    return ApiResponse(
        statusCode=status_code,
        error=ErrorDetail(code=code, message=message, details=details),
    ).model_dump()
