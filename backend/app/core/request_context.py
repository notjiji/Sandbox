from contextvars import ContextVar
from dataclasses import dataclass

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response

_request_context: ContextVar["RequestContext | None"] = ContextVar(
    "request_context",
    default=None,
)


@dataclass(frozen=True)
class RequestContext:
    ip_address: str | None
    user_agent: str | None


def get_client_ip(request: Request | StarletteRequest) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def build_request_context(request: Request | StarletteRequest) -> RequestContext:
    return RequestContext(
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )


def set_request_context(context: RequestContext):
    return _request_context.set(context)


def get_request_context() -> RequestContext | None:
    return _request_context.get()


def reset_request_context(token) -> None:
    _request_context.reset(token)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        token = set_request_context(build_request_context(request))
        try:
            return await call_next(request)
        finally:
            reset_request_context(token)
