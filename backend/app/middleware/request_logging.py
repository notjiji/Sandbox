import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger, request_id_ctx, user_id_ctx

logger = get_logger("sandbox.request")


def _resolve_user_id(request: Request) -> str | None:
    user_id = getattr(request.state, "user_id", None)
    if user_id is not None:
        return str(user_id)
    return None


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        request_id_token = request_id_ctx.set(request_id)
        user_id = _resolve_user_id(request)
        user_id_token = user_id_ctx.set(user_id)

        start = time.perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception:
            status_code = 500
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "endpoint": request.url.path,
                    "status_code": status_code,
                    "execution_time_ms": duration_ms,
                    "user_id": user_id,
                },
            )
            request_id_ctx.reset(request_id_token)
            user_id_ctx.reset(user_id_token)
