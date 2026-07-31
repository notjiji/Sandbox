from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.database import engine
from app.core.rate_limit import limiter
from app.core.redis import get_redis_client
from app.core.version import API_VERSION
from app.schemas.health import HealthResponse

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


def get_health() -> tuple[HealthResponse, int]:
    database_ok = _check_database()
    redis_ok = _check_redis()
    healthy = database_ok and redis_ok

    payload = HealthResponse(
        status="healthy" if healthy else "unhealthy",
        database="connected" if database_ok else "disconnected",
        redis="connected" if redis_ok else "disconnected",
        version=API_VERSION,
    )
    status_code = 200 if healthy else 503
    return payload, status_code


@router.get("/health", response_model=HealthResponse)
@limiter.exempt
def health_check() -> JSONResponse:
    payload, status_code = get_health()
    return JSONResponse(status_code=status_code, content=payload.model_dump())
