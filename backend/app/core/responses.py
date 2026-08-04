from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.logging import request_id_ctx
from app.shared.schemas.responses import ErrorDetail, ErrorResponse, ResponseMeta, SuccessResponse


def _build_meta(request: Request | None = None) -> ResponseMeta:
    request_id = None
    if request is not None:
        request_id = getattr(request.state, "request_id", None)
    if request_id is None:
        request_id = request_id_ctx.get()
    return ResponseMeta(
        timestamp=datetime.now(timezone.utc).isoformat(),
        request_id=request_id,
    )


def attach_trace_headers(request: Request | None, response: JSONResponse) -> JSONResponse:
    if request is None:
        return response
    request_id = getattr(request.state, "request_id", None)
    correlation_id = getattr(request.state, "correlation_id", None)
    if request_id:
        response.headers["X-Request-ID"] = request_id
    if correlation_id:
        response.headers["X-Correlation-ID"] = correlation_id
    return response


def success_response(
    data: Any = None,
    status_code: int = 200,
    request: Request | None = None,
) -> JSONResponse:
    payload = SuccessResponse(
        data=data if data is not None else {},
        meta=_build_meta(request),
    ).model_dump()
    response = JSONResponse(status_code=status_code, content=payload)
    return attach_trace_headers(request, response)


def error_response(
    code: str,
    message: str,
    status_code: int = 400,
    details: list[dict[str, str]] | None = None,
    request: Request | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorDetail(code=code, message=message, details=details),
    ).model_dump()
    response = JSONResponse(status_code=status_code, content=payload)
    return attach_trace_headers(request, response)
