from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from app.shared.schemas.responses import ErrorDetail, ErrorResponse, SuccessResponse


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


def success_response(data: Any = None, status_code: int = 200) -> JSONResponse:
    payload = SuccessResponse(data=data if data is not None else {}).model_dump()
    return JSONResponse(status_code=status_code, content=payload)


def error_response(
    code: str,
    message: str,
    status_code: int = 400,
    details: list[dict[str, str]] | None = None,
    request: Request | None = None,
) -> JSONResponse:
    error: dict[str, Any] = {"code": code, "message": message}
    if details:
        error["details"] = details
    response = JSONResponse(status_code=status_code, content={"success": False, "error": error})
    return attach_trace_headers(request, response)
