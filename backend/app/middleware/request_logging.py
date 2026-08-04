import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import (
    correlation_id_ctx,
    get_logger,
    request_id_ctx,
    user_id_ctx,
)

logger = get_logger("sandbox.request")


def _resolve_user_id(request: Request) -> str | None:
    user_id = getattr(request.state, "user_id", None)
    if user_id is not None:
        return str(user_id)
    return user_id_ctx.get()


def _resolve_correlation_id(request: Request, request_id: str) -> str:
    header_value = request.headers.get("X-Correlation-ID")
    if header_value:
        return header_value.strip()
    return request_id


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Assigns request/correlation IDs, times requests, and emits structured access logs."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        correlation_id = _resolve_correlation_id(request, request_id)

        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        request_id_token = request_id_ctx.set(request_id)
        correlation_id_token = correlation_id_ctx.set(correlation_id)
        user_id_token = user_id_ctx.set(_resolve_user_id(request))

        start = time.perf_counter()
        status_code = 500
        response: Response | None = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = 500
            logger.exception(
                "request failed",
                extra={
                    "method": request.method,
                    "endpoint": request.url.path,
                    "query": request.url.query or None,
                    "client_ip": request.client.host if request.client else None,
                },
            )
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            resolved_user_id = _resolve_user_id(request)

            logger.info(
                "request completed",
                extra={
                    "method": request.method,
                    "endpoint": request.url.path,
                    "query": request.url.query or None,
                    "status_code": status_code,
                    "execution_time_ms": duration_ms,
                    "client_ip": request.client.host if request.client else None,
                    "user_id": resolved_user_id,
                },
            )

            if response is not None:
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Correlation-ID"] = correlation_id
                response.headers["X-Response-Time"] = f"{duration_ms}ms"

            request_id_ctx.reset(request_id_token)
            correlation_id_ctx.reset(correlation_id_token)
            user_id_ctx.reset(user_id_token)
