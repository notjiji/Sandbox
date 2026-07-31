from sqlalchemy.orm import Session

from app.audit.events import AuditAction
from app.audit.service import record_auth_event
from app.auth.email import send_password_reset_email, send_verification_otp_email
from app.auth.repositories.email_verification_repository import (
    create_verification_otp,
    get_latest_verification_otp,
    increment_otp_attempts,
    is_verification_otp_valid,
    revoke_verification_otp,
    verify_otp_code,
)
from app.auth.lockout import clear_login_lockout, get_lockout_status, record_failed_login
from app.auth.repositories.password_reset_repository import (
    create_password_reset_token,
    get_password_reset_token,
    is_password_reset_token_valid,
    mark_password_reset_token_used,
)
from app.auth.repositories.refresh_token_repository import (
    create_refresh_token_record,
    get_refresh_token_by_hash,
    is_refresh_token_valid,
    revoke_all_user_refresh_tokens,
    revoke_refresh_token,
)
from app.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordResponse,
    LoginResponse,
    LogoutResponse,
    MessageResponse,
    RefreshResponse,
    RegisterResponse,
    ResetPasswordRequest,
)
from app.auth.token_context import build_access_token_context
from app.core.config import get_settings
from app.core.exceptions import (
    AccountLockedError,
    ConflictError,
    EmailNotVerifiedError,
    UnauthorizedError,
    ValidationAppError,
)
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    generate_otp,
    get_password_reset_expiry,
    get_refresh_token_expiry,
    get_verification_otp_expiry,
    hash_password,
    verify_password,
)
from app.users.repositories.user_repository import (
    create_user,
    get_user_by_email,
    mark_user_verified,
    update_user_password,
)


def _issue_verification_otp(db: Session, *, user) -> None:
    otp = generate_otp()
    create_verification_otp(
        db,
        user_id=user.id,
        otp=otp,
        expires_at=get_verification_otp_expiry(),
    )
    send_verification_otp_email(to_email=user.email, otp=otp)


def register_user(
    db: Session,
    *,
    first_name: str,
    last_name: str,
    email: str,
    password: str,
    invite_token: str | None = None,
) -> RegisterResponse:
    existing = get_user_by_email(db, email)
    if existing:
        if existing.is_verified:
            raise ConflictError("An account with this email already exists")
        raise ConflictError("An account with this email already exists but is not verified")

    user = create_user(
        db,
        email=email,
        hashed_password=hash_password(password),
        first_name=first_name,
        last_name=last_name,
    )
    _issue_verification_otp(db, user=user)
    record_auth_event(
        db,
        action=AuditAction.AUTH_REGISTER,
        user_id=user.id,
        resource_type="user",
        resource_id=user.id,
        details={"email": email},
    )
    db.commit()
    db.refresh(user)

    if invite_token:
        from app.members.services.invite_service import accept_invite_by_token

        accept_invite_by_token(db, user=user, token=invite_token)

    return RegisterResponse(
        message="Account created. Check your email for a verification code.",
        email=user.email,
    )


def login_user(db: Session, *, email: str, password: str) -> LoginResponse:
    lockout = get_lockout_status(email)
    if lockout.locked:
        record_auth_event(
            db,
            action=AuditAction.AUTH_LOGIN_FAILED,
            details={
                "email": email,
                "reason": "account_locked",
                "retry_after_seconds": lockout.retry_after_seconds,
            },
        )
        db.commit()
        raise AccountLockedError(retry_after_seconds=lockout.retry_after_seconds)

    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        lockout = record_failed_login(email)
        details = {"email": email, "reason": "invalid_credentials"}
        if lockout.failed_attempts:
            details["failed_attempts"] = lockout.failed_attempts
        record_auth_event(
            db,
            action=AuditAction.AUTH_LOGIN_FAILED,
            user_id=user.id if user else None,
            details=details,
        )
        if lockout.newly_locked:
            record_auth_event(
                db,
                action=AuditAction.AUTH_ACCOUNT_LOCKED,
                user_id=user.id if user else None,
                details={
                    "email": email,
                    "retry_after_seconds": lockout.retry_after_seconds,
                },
            )
        db.commit()
        if lockout.locked:
            raise AccountLockedError(retry_after_seconds=lockout.retry_after_seconds)
        raise UnauthorizedError("Invalid email or password")

    if not user.is_active:
        record_auth_event(
            db,
            action=AuditAction.AUTH_LOGIN_FAILED,
            user_id=user.id,
            details={"email": email, "reason": "inactive_account"},
        )
        db.commit()
        raise UnauthorizedError("Account is inactive")

    if not user.is_verified:
        record_auth_event(
            db,
            action=AuditAction.AUTH_LOGIN_FAILED,
            user_id=user.id,
            details={"email": email, "reason": "email_not_verified"},
        )
        db.commit()
        raise EmailNotVerifiedError()

    token_context = build_access_token_context(db, user)
    access_token, expires_in = create_access_token(token_context)
    refresh_token = generate_opaque_token()
    refresh_record = create_refresh_token_record(
        db,
        user_id=user.id,
        token=refresh_token,
        expires_at=get_refresh_token_expiry(),
    )
    record_auth_event(
        db,
        action=AuditAction.AUTH_LOGIN,
        user_id=user.id,
        resource_type="session",
        resource_id=refresh_record.id,
        details={"email": email, "session_id": str(refresh_record.id)},
    )
    clear_login_lockout(email)
    db.commit()

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        session_id=str(refresh_record.id),
    )


def verify_email(db: Session, *, email: str, otp: str) -> MessageResponse:
    settings = get_settings()
    user = get_user_by_email(db, email)
    if not user or not user.is_active:
        raise UnauthorizedError("Invalid verification code")

    if user.is_verified:
        return MessageResponse(message="Email already verified")

    record = get_latest_verification_otp(db, user.id)
    if not record or not is_verification_otp_valid(record):
        raise UnauthorizedError("Invalid or expired verification code")

    if record.attempts >= settings.EMAIL_VERIFICATION_OTP_MAX_ATTEMPTS:
        revoke_verification_otp(db, record)
        db.commit()
        raise UnauthorizedError("Too many attempts. Request a new verification code.")

    if not verify_otp_code(record, otp):
        increment_otp_attempts(db, record)
        db.commit()
        raise UnauthorizedError("Invalid or expired verification code")

    mark_user_verified(db, user)
    revoke_verification_otp(db, record)
    record_auth_event(
        db,
        action=AuditAction.AUTH_EMAIL_VERIFIED,
        user_id=user.id,
        resource_type="user",
        resource_id=user.id,
        details={"email": email},
    )
    db.commit()
    return MessageResponse(message="Email verified successfully")


def resend_verification(db: Session, *, email: str) -> MessageResponse:
    user = get_user_by_email(db, email)
    if user and user.is_active and not user.is_verified:
        _issue_verification_otp(db, user=user)
        db.commit()

    return MessageResponse(
        message="If the account exists and is unverified, a new code will be sent.",
    )


def refresh_access_token(db: Session, *, refresh_token: str) -> RefreshResponse:
    record = get_refresh_token_by_hash(db, refresh_token)
    if not record or not is_refresh_token_valid(record):
        raise UnauthorizedError("Invalid or expired refresh token")

    user = record.user
    if not user.is_active:
        raise UnauthorizedError("Account is inactive")

    if not user.is_verified:
        raise EmailNotVerifiedError()

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
    record_auth_event(
        db,
        action=AuditAction.AUTH_REFRESH,
        user_id=user.id,
        resource_type="session",
        resource_id=new_record.id,
        details={"previous_session_id": str(record.id), "session_id": str(new_record.id)},
    )
    db.commit()

    return RefreshResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=expires_in,
        session_id=str(new_record.id),
    )


def logout_user(db: Session, *, refresh_token: str) -> LogoutResponse:
    record = get_refresh_token_by_hash(db, refresh_token)
    if record and not record.revoked:
        record_auth_event(
            db,
            action=AuditAction.AUTH_LOGOUT,
            user_id=record.user_id,
            resource_type="session",
            resource_id=record.id,
        )
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
        record_auth_event(
            db,
            action=AuditAction.AUTH_PASSWORD_RESET_REQUEST,
            user_id=user.id,
            resource_type="user",
            resource_id=user.id,
            details={"email": email},
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
    record_auth_event(
        db,
        action=AuditAction.AUTH_PASSWORD_RESET,
        user_id=user.id,
        resource_type="user",
        resource_id=user.id,
    )
    clear_login_lockout(user.email)
    db.commit()

    return MessageResponse(message="Password reset successfully")


def change_password(db: Session, user, *, body: ChangePasswordRequest) -> MessageResponse:
    if not verify_password(body.current_password, user.hashed_password):
        raise UnauthorizedError("Current password is incorrect")

    if body.current_password == body.new_password:
        raise ValidationAppError("New password must be different from the current password")

    update_user_password(db, user, hash_password(body.new_password))
    revoke_all_user_refresh_tokens(db, user.id)
    record_auth_event(
        db,
        action=AuditAction.AUTH_PASSWORD_CHANGE,
        user_id=user.id,
        resource_type="user",
        resource_id=user.id,
    )
    clear_login_lockout(user.email)
    db.commit()

    return MessageResponse(message="Password changed successfully")
