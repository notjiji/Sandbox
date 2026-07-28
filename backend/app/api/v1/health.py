from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.rate_limit import limiter
from app.schemas.health import HealthResponse
from app.services.health import get_health

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
@limiter.exempt
def health_check() -> JSONResponse:
    payload, status_code = get_health()
    return JSONResponse(status_code=status_code, content=payload.model_dump())
