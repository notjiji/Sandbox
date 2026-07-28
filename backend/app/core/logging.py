import logging
import sys
from contextvars import ContextVar

from pythonjsonlogger.json import JsonFormatter

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_ctx: ContextVar[str | None] = ContextVar("user_id", default=None)


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        record.user_id = user_id_ctx.get()
        return True


def setup_logging(log_level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        JsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s "
            "%(request_id)s %(user_id)s",
            rename_fields={
                "levelname": "level",
                "asctime": "timestamp",
            },
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
