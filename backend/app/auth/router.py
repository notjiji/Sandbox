from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
import uuid

from app.api.deps import get_current_session_id_header, get_current_user
from app.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
)
from app.auth.services import auth_service, session_service
from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.core.rate_limit import limiter
from app.core.responses import success_response
from app.users.models import User
from fastapi.responses import JSONResponse

router = APIRouter()
settings = get_settings()


@router.post("/register", status_code=201)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def register(request: Request, body: RegisterRequest, db: Session = Depends(get_db)) -> JSONResponse:
    result = auth_service.register_user(
        db,
        first_name=body.first_name,
        last_name=body.last_name,
        email=str(body.email),
        password=body.password,
        invite_token=body.invite_token,
    )
    return success_response(data=result.model_dump(), status_code=201, request=request)


@router.post("/verify-email")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def verify_email_route(
    request: Request,
    body: VerifyEmailRequest,
    db: Session = Depends(get_db),
) -> JSONResponse:
    result = auth_service.verify_email(db, email=str(body.email), otp=body.otp)
    return success_response(data=result.model_dump(), request=request)


@router.post("/resend-verification")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def resend_verification_route(
    request: Request,
    body: ResendVerificationRequest,
    db: Session = Depends(get_db),
) -> JSONResponse:
    result = auth_service.resend_verification(db, email=str(body.email))
    return success_response(data=result.model_dump(), request=request)


@router.post("/login")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)) -> JSONResponse:
    result = auth_service.login_user(db, email=str(body.email), password=body.password)
    return success_response(data=result.model_dump(), request=request)


@router.post("/refresh")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def refresh(request: Request, body: RefreshRequest, db: Session = Depends(get_db)) -> JSONResponse:
    result = auth_service.refresh_access_token(db, refresh_token=body.refresh_token)
    return success_response(data=result.model_dump(), request=request)


@router.post("/logout")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def logout(request: Request, body: LogoutRequest, db: Session = Depends(get_db)) -> JSONResponse:
    result = auth_service.logout_user(db, refresh_token=body.refresh_token)
    return success_response(data=result.model_dump(), request=request)


@router.post("/forgot-password")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> JSONResponse:
    result = auth_service.request_password_reset(db, email=str(body.email))
    return success_response(data=result.model_dump(), request=request)


@router.post("/reset-password")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def reset_password_route(
    request: Request,
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> JSONResponse:
    result = auth_service.reset_password(db, body=body)
    return success_response(data=result.model_dump(), request=request)


@router.put("/change-password")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def change_password_route(
    request: Request,
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    result = auth_service.change_password(db, current_user, body=body)
    return success_response(data=result.model_dump(), request=request)


@router.get("/sessions")
def list_sessions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_session_id: uuid.UUID | None = Depends(get_current_session_id_header),
) -> JSONResponse:
    result = session_service.list_user_sessions(db, current_user, current_session_id=current_session_id)
    return success_response(data=result.model_dump(mode="json"), request=request)


@router.delete("/sessions/{session_id}")
def revoke_session(
    request: Request,
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_session_id: uuid.UUID | None = Depends(get_current_session_id_header),
) -> JSONResponse:
    result = session_service.revoke_user_session(
        db,
        current_user,
        session_id=session_id,
        current_session_id=current_session_id,
    )
    return success_response(data=result.model_dump(), request=request)


@router.post("/sessions/revoke-others")
def revoke_other_sessions_route(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_session_id: uuid.UUID | None = Depends(get_current_session_id_header),
) -> JSONResponse:
    if current_session_id is None:
        raise UnauthorizedError("X-Session-ID header is required")
    result = session_service.revoke_other_sessions(db, current_user, current_session_id=current_session_id)
    return success_response(data=result.model_dump(), request=request)


@router.post("/sessions/revoke-all")
def revoke_all_sessions_route(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    result = session_service.revoke_all_sessions(db, current_user)
    return success_response(data=result.model_dump(), request=request)
