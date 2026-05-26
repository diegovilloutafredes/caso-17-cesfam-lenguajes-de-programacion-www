from __future__ import annotations
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .enums import ReportType


class ReportBase(BaseModel):
    reportType: ReportType
    parameters: Optional[str] = None


class ReportCreate(ReportBase):
    pass


class ReportRead(ReportBase):
    id: int
    generatedAt: Optional[datetime] = None
