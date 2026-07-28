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
) -> JSONResponse:
    payload = ErrorResponse(error=ErrorDetail(code=code, message=message)).model_dump()
    return JSONResponse(status_code=status_code, content=payload)
