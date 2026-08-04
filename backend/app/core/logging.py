import logging
import sys
import traceback
from contextlib import contextmanager
from contextvars import ContextVar, Token
from datetime import date, datetime
from typing import Any
from uuid import UUID

from pythonjsonlogger.json import JsonFormatter

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)
user_id_ctx: ContextVar[str | None] = ContextVar("user_id", default=None)

_service_name = "sandbox-api"
_environment = "development"


class StructuredJsonFormatter(JsonFormatter):
    """JSON logs with request context and full exception stack traces."""

    def add_fields(
        self,
        log_data: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        exc_info = record.exc_info
        super().add_fields(log_data, record, message_dict)

        for key, value in (
            ("request_id", getattr(record, "request_id", None)),
            ("correlation_id", getattr(record, "correlation_id", None)),
            ("user_id", getattr(record, "user_id", None)),
            ("service", getattr(record, "service", None)),
            ("environment", getattr(record, "environment", None)),
        ):
            if value is not None:
                log_data[key] = value

        if exc_info and exc_info[0] is not None:
            exc_type, exc_value, _ = exc_info
            log_data["exception_type"] = exc_type.__name__
            log_data["exception_message"] = str(exc_value)
            log_data["stack_trace"] = "".join(traceback.format_exception(*exc_info))


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        record.correlation_id = correlation_id_ctx.get()
        record.user_id = user_id_ctx.get()
        record.service = _service_name
        record.environment = _environment
        return True


def _json_default(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return str(value)


def setup_logging(
    log_level: str = "INFO",
    *,
    service_name: str = "sandbox-api",
    environment: str = "development",
) -> None:
    global _service_name, _environment
    _service_name = service_name
    _environment = environment

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        StructuredJsonFormatter(
            "%(levelname)s %(asctime)s %(name)s %(message)s",
            rename_fields={
                "levelname": "level",
                "asctime": "timestamp",
            },
            json_default=_json_default,
        )
    )
    handler.addFilter(RequestContextFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level.upper())

    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def get_correlation_id() -> str | None:
    return correlation_id_ctx.get()


def get_request_id() -> str | None:
    return request_id_ctx.get()


@contextmanager
def log_context(
    *,
    request_id: str | None = None,
    correlation_id: str | None = None,
    user_id: str | None = None,
):
    tokens: list[tuple[ContextVar[str | None], Token]] = []

    if request_id is not None:
        tokens.append((request_id_ctx, request_id_ctx.set(request_id)))
    if correlation_id is not None:
        tokens.append((correlation_id_ctx, correlation_id_ctx.set(correlation_id)))
    if user_id is not None:
        tokens.append((user_id_ctx, user_id_ctx.set(user_id)))

    try:
        yield
    finally:
        for ctx, token in reversed(tokens):
            ctx.reset(token)
