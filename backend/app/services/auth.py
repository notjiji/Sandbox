from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ConflictError, UnauthorizedError, ValidationAppError
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    get_password_reset_expiry,
    get_refresh_token_expiry,
    hash_password,
    verify_password,
)
from app.repositories.refresh_token import (
    create_refresh_token_record,
    get_refresh_token_by_hash,
    is_refresh_token_valid,
    revoke_all_user_refresh_tokens,
    revoke_refresh_token,
)
from app.repositories.user import (
    create_password_reset_token,
    create_user,
    get_password_reset_token,
    get_user_by_email,
    is_password_reset_token_valid,
    mark_password_reset_token_used,
    update_user_password,
)
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordResponse,
    LoginResponse,
    LogoutResponse,
    MessageResponse,
    RefreshResponse,
    RegisterResponse,
    ResetPasswordRequest,
)
from app.services.email import send_password_reset_email
from app.services.token_context import build_access_token_context


def register_user(
    db: Session,
    *,
    first_name: str,
    last_name: str,
    email: str,
    password: str,
) -> RegisterResponse:
    if get_user_by_email(db, email):
        raise ConflictError("An account with this email already exists")

    user = create_user(
        db,
        email=email,
        hashed_password=hash_password(password),
        first_name=first_name,
        last_name=last_name,
    )
    db.commit()
    db.refresh(user)
    return RegisterResponse(message="Account created successfully")


def login_user(db: Session, *, email: str, password: str) -> LoginResponse:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedError("Account is inactive")

    token_context = build_access_token_context(db, user)
    access_token, expires_in = create_access_token(token_context)
    refresh_token = generate_opaque_token()
    create_refresh_token_record(
        db,
        user_id=user.id,
        token=refresh_token,
        expires_at=get_refresh_token_expiry(),
    )
    db.commit()

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


def refresh_access_token(db: Session, *, refresh_token: str) -> RefreshResponse:
    record = get_refresh_token_by_hash(db, refresh_token)
    if not record or not is_refresh_token_valid(record):
        raise UnauthorizedError("Invalid or expired refresh token")

    user = record.user
    if not user.is_active:
        raise UnauthorizedError("Account is inactive")

    token_context = build_access_token_context(db, user)
    access_token, expires_in = create_access_token(token_context)
    new_refresh_token = generate_opaque_token()
    new_record = create_refresh_token_record(
        db,
        user_id=user.id,
        token=new_refresh_token,
        expires_at=get_refresh_token_expiry(),
    )
    revoke_refresh_token(db, record, replaced_by_id=new_record.id)
    db.commit()

    return RefreshResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=expires_in,
    )


def logout_user(db: Session, *, refresh_token: str) -> LogoutResponse:
    record = get_refresh_token_by_hash(db, refresh_token)
    if record and not record.revoked:
        revoke_refresh_token(db, record)
        db.commit()

    return LogoutResponse(message="Logged out successfully")


def request_password_reset(db: Session, *, email: str) -> ForgotPasswordResponse:
    settings = get_settings()
    user = get_user_by_email(db, email)

    if user and user.is_active:
        token = generate_opaque_token()
        create_password_reset_token(
            db,
            user_id=user.id,
            token=token,
            expires_at=get_password_reset_expiry(),
        )
        db.commit()
        reset_link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={token}"
        send_password_reset_email(to_email=user.email, reset_link=reset_link)

    return ForgotPasswordResponse(message="If the email exists, a recovery link will be sent")


def reset_password(db: Session, *, body: ResetPasswordRequest) -> MessageResponse:
    record = get_password_reset_token(db, body.token)
    if not record or not is_password_reset_token_valid(record):
        raise UnauthorizedError("Invalid or expired reset token")

    user = record.user
    if not user.is_active:
        raise UnauthorizedError("Account is inactive")

    if verify_password(body.new_password, user.hashed_password):
        raise ValidationAppError("New password must be different from the current password")

    update_user_password(db, user, hash_password(body.new_password))
    mark_password_reset_token_used(db, record)
    revoke_all_user_refresh_tokens(db, user.id)
    db.commit()

    return MessageResponse(message="Password reset successfully")


def change_password(db: Session, user, *, body: ChangePasswordRequest) -> MessageResponse:
    if not verify_password(body.current_password, user.hashed_password):
        raise UnauthorizedError("Current password is incorrect")

    if body.current_password == body.new_password:
        raise ValidationAppError("New password must be different from the current password")

    update_user_password(db, user, hash_password(body.new_password))
    revoke_all_user_refresh_tokens(db, user.id)
    db.commit()

    return MessageResponse(message="Password changed successfully")
