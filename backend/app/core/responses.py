from typing import Any

from fastapi.responses import JSONResponse

from app.schemas.responses import ErrorDetail, ErrorResponse, SuccessResponse


def success_response(data: Any = None, status_code: int = 200) -> JSONResponse:
    payload = SuccessResponse(data=data if data is not None else {}).model_dump()
    return JSONResponse(status_code=status_code, content=payload)


def error_response(
    code: str,
    message: str,
    status_code: int = 400,
    details: list[dict[str, str]] | None = None,
) -> JSONResponse:
    error: dict[str, Any] = {"code": code, "message": message}
    if details:
        error["details"] = details
    return JSONResponse(status_code=status_code, content={"success": False, "error": error})
