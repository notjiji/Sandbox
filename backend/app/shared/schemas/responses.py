from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ResponseMeta(BaseModel):
    timestamp: str
    request_id: str | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[dict[str, str]] | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


class SuccessResponse(BaseModel):
    success: bool = True
    data: Any = Field(default_factory=dict)
    meta: ResponseMeta
