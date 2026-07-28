from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.core.responses import error_response, success_response
from app.schemas.auth import ForgotPasswordRequest, LoginRequest, RegisterRequest

router = APIRouter()
settings = get_settings()


@router.post("/login")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def login(request: Request, body: LoginRequest):
    return error_response(
        code="NOT_IMPLEMENTED",
        message="Authentication will be available in a later phase",
        status_code=501,
    )


@router.post("/register")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def register(request: Request, body: RegisterRequest):
    return error_response(
        code="NOT_IMPLEMENTED",
        message="Registration will be available in a later phase",
        status_code=501,
    )


@router.post("/forgot-password")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def forgot_password(request: Request, body: ForgotPasswordRequest):
    return success_response(
        data={"message": "If the email exists, a recovery link will be sent"},
    )
