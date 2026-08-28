from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import router as api_v1_router
from app.core.config import get_settings
from app.core.exceptions import AccountLockedError, AppException, InternalServerError
from app.core.health import router as health_router
from app.core.logging import get_logger, setup_logging
from app.core.rate_limit import limiter
from app.core.responses import error_response
from app.core.version import API_VERSION
from app.middleware.production_boundary import production_operator_docs_middleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.core.request_context import RequestContextMiddleware
from app.events.bus import ensure_default_handlers

settings = get_settings()
setup_logging(
    settings.LOG_LEVEL,
    service_name="sandbox-api",
    environment=settings.ENVIRONMENT,
)

logger = get_logger("sandbox.errors")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_default_handlers()
    yield


_is_production = settings.ENVIRONMENT == "production"

app = FastAPI(
    title="Sandbox",
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if not _is_production else None,
    redoc_url="/redoc" if not _is_production else None,
    openapi_url="/openapi.json" if not _is_production else None,
)

app.state.limiter = limiter
app.include_router(health_router, tags=["health"])
app.include_router(api_v1_router, prefix="/api/v1")

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestContextMiddleware)
if _is_production:
    app.middleware("http")(production_operator_docs_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-Correlation-ID",
        "X-Organization-ID",
        "X-Session-ID",
    ],
    expose_headers=["X-Request-ID", "X-Correlation-ID", "X-Response-Time", "Retry-After"],
)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Prometheus scrapes backend:8000/metrics on the internal Docker network — not via public nginx.
instrumentator = Instrumentator().instrument(app)
instrumentator.expose(app, endpoint="/metrics")


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, _exc: RateLimitExceeded) -> JSONResponse:
    return error_response(
        code="RATE_LIMIT_EXCEEDED",
        message="Too many requests. Please try again later.",
        status_code=429,
        request=request,
    )


@app.exception_handler(AccountLockedError)
async def account_locked_handler(request: Request, exc: AccountLockedError) -> JSONResponse:
    response = error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        request=request,
    )
    if exc.retry_after_seconds:
        response.headers["Retry-After"] = str(exc.retry_after_seconds)
    return response


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        request=request,
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code_map = {
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "RESOURCE_NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return error_response(code=code, message=message, status_code=exc.status_code, request=request)


def _format_validation_errors(exc: RequestValidationError) -> list[dict[str, str]]:
    formatted: list[dict[str, str]] = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", ()) if part != "body")
        formatted.append(
            {
                "field": location or "body",
                "message": error.get("msg", "Invalid value"),
            }
        )
    return formatted


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    details = _format_validation_errors(exc)
    return error_response(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=422,
        details=details,
        request=request,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled exception",
        extra={
            "method": request.method,
            "endpoint": request.url.path,
            "request_id": getattr(request.state, "request_id", None),
            "correlation_id": getattr(request.state, "correlation_id", None),
        },
    )
    internal = InternalServerError()
    return error_response(
        code=internal.code,
        message=internal.message,
        status_code=internal.status_code,
        request=request,
    )
