from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uuid

from app.api.deps import get_current_session_id_header, get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.core.rate_limit import limiter
from app.models.user import User
from app.schemas.auth import (
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
from app.services.auth import (
    change_password,
    login_user,
    logout_user,
    refresh_access_token,
    register_user,
    request_password_reset,
    resend_verification,
    reset_password,
    verify_email,
)
from app.services.session import (
    list_user_sessions,
    revoke_all_sessions,
    revoke_other_sessions,
    revoke_user_session,
)

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
        invite_token=body.invite_token,
    )
    return JSONResponse(status_code=201, content=result.model_dump())


@router.post("/verify-email")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def verify_email_route(
    request: Request,
    body: VerifyEmailRequest,
    db: Session = Depends(get_db),
) -> JSONResponse:
    result = verify_email(db, email=str(body.email), otp=body.otp)
    return JSONResponse(status_code=200, content=result.model_dump())


@router.post("/resend-verification")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def resend_verification_route(
    request: Request,
    body: ResendVerificationRequest,
    db: Session = Depends(get_db),
) -> JSONResponse:
    result = resend_verification(db, email=str(body.email))
    return JSONResponse(status_code=200, content=result.model_dump())


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
def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> JSONResponse:
    result = request_password_reset(db, email=str(body.email))
    return JSONResponse(status_code=200, content=result.model_dump())


@router.post("/reset-password")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def reset_password_route(
    request: Request,
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> JSONResponse:
    result = reset_password(db, body=body)
    return JSONResponse(status_code=200, content=result.model_dump())


@router.put("/change-password")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def change_password_route(
    request: Request,
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    result = change_password(db, current_user, body=body)
    return JSONResponse(status_code=200, content=result.model_dump())


@router.get("/sessions")
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_session_id: uuid.UUID | None = Depends(get_current_session_id_header),
) -> JSONResponse:
    result = list_user_sessions(db, current_user, current_session_id=current_session_id)
    return JSONResponse(status_code=200, content=result.model_dump(mode="json"))


@router.delete("/sessions/{session_id}")
def revoke_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_session_id: uuid.UUID | None = Depends(get_current_session_id_header),
) -> JSONResponse:
    result = revoke_user_session(
        db,
        current_user,
        session_id=session_id,
        current_session_id=current_session_id,
    )
    return JSONResponse(status_code=200, content=result.model_dump())


@router.post("/sessions/revoke-others")
def revoke_other_sessions_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_session_id: uuid.UUID | None = Depends(get_current_session_id_header),
) -> JSONResponse:
    if current_session_id is None:
        raise UnauthorizedError("X-Session-ID header is required")
    result = revoke_other_sessions(db, current_user, current_session_id=current_session_id)
    return JSONResponse(status_code=200, content=result.model_dump())


@router.post("/sessions/revoke-all")
def revoke_all_sessions_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    result = revoke_all_sessions(db, current_user)
    return JSONResponse(status_code=200, content=result.model_dump())
