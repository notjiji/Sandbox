from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.exceptions import AppException, InternalServerError
from app.core.logging import setup_logging
from app.core.responses import error_response
from app.core.version import API_VERSION
from app.middleware.request_logging import RequestLoggingMiddleware
from app.api.v1.router import router as api_v1_router

settings = get_settings()
setup_logging(settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Sandbox",
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

app.include_router(api_v1_router, prefix="/api/v1")

app.add_middleware(RequestLoggingMiddleware)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.exception_handler(AppException)
async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    return error_response(code=exc.code, message=exc.message, status_code=exc.status_code)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code_map = {
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "RESOURCE_NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return error_response(code=code, message=message, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = exc.errors()
    message = errors[0]["msg"] if errors else "Validation failed"
    return error_response(code="VALIDATION_ERROR", message=message, status_code=422)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    internal = InternalServerError()
    return error_response(
        code=internal.code,
        message=internal.message,
        status_code=internal.status_code,
    )

