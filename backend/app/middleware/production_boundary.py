"""Block public access to operator documentation endpoints in production."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

OPERATOR_DOC_PREFIXES = ("/docs", "/redoc")


def is_blocked_public_operator_path(path: str) -> bool:
    if path in {"/openapi.json", "/openapi.yaml"}:
        return True
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in OPERATOR_DOC_PREFIXES)


async def production_operator_docs_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    if is_blocked_public_operator_path(request.url.path):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    return await call_next(request)
