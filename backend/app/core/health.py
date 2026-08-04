from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.database import engine
from app.core.rate_limit import limiter
from app.core.redis import get_redis_client
from app.core.version import API_VERSION
from app.shared.schemas.health import HealthResponse, LiveResponse, ReadinessResponse

router = APIRouter()


def _check_database() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _check_redis() -> bool:
    try:
        return bool(get_redis_client().ping())
    except Exception:
        return False


def get_readiness() -> tuple[ReadinessResponse, int]:
    database_ok = _check_database()
    redis_ok = _check_redis()
    ready = database_ok and redis_ok

    payload = ReadinessResponse(
        status="ready" if ready else "not_ready",
        database="connected" if database_ok else "disconnected",
        redis="connected" if redis_ok else "disconnected",
        version=API_VERSION,
    )
    status_code = 200 if ready else 503
    return payload, status_code


@router.get("/health", response_model=HealthResponse)
@limiter.exempt
def health_check() -> JSONResponse:
    payload = HealthResponse(status="ok", version=API_VERSION)
    return JSONResponse(status_code=200, content=payload.model_dump())


@router.get("/health/live", response_model=LiveResponse)
@limiter.exempt
def liveness_check() -> JSONResponse:
    payload = LiveResponse(status="alive")
    return JSONResponse(status_code=200, content=payload.model_dump())


@router.get("/health/ready", response_model=ReadinessResponse)
@limiter.exempt
def readiness_check() -> JSONResponse:
    payload, status_code = get_readiness()
    return JSONResponse(status_code=status_code, content=payload.model_dump())
