from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.core.responses import success_response
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
)
from app.services.auth import login_user, logout_user, refresh_access_token, register_user

router = APIRouter()
settings = get_settings()


@router.post("/register", status_code=201)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def register(request: Request, body: RegisterRequest, db: Session = Depends(get_db)) -> JSONResponse:
    result = register_user(
        db,
        first_name=body.first_name,
        last_name=body.last_name,
        email=str(body.email),
        password=body.password,
    )
    return JSONResponse(status_code=201, content=result.model_dump())


@router.post("/login")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)) -> JSONResponse:
    result = login_user(db, email=str(body.email), password=body.password)
    return JSONResponse(status_code=200, content=result.model_dump())


@router.post("/refresh")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def refresh(request: Request, body: RefreshRequest, db: Session = Depends(get_db)) -> JSONResponse:
    result = refresh_access_token(db, refresh_token=body.refresh_token)
    return JSONResponse(status_code=200, content=result.model_dump())


@router.post("/logout")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def logout(request: Request, body: LogoutRequest, db: Session = Depends(get_db)) -> JSONResponse:
    result = logout_user(db, refresh_token=body.refresh_token)
    return JSONResponse(status_code=200, content=result.model_dump())


@router.post("/forgot-password")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def forgot_password(request: Request, body: ForgotPasswordRequest) -> JSONResponse:
    return success_response(
        data={"message": "If the email exists, a recovery link will be sent"},
    )
