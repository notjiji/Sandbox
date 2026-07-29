from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    get_refresh_token_expiry,
    hash_password,
    verify_password,
)
from app.repositories.refresh_token import (
    create_refresh_token_record,
    get_refresh_token_by_hash,
    is_refresh_token_valid,
    revoke_refresh_token,
)
from app.repositories.user import create_user, get_user_by_email
from app.schemas.auth import (
    LoginResponse,
    LogoutResponse,
    RefreshResponse,
    RegisterResponse,
)


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

    access_token, expires_in = create_access_token(user.id)
    refresh_token = generate_refresh_token()
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

    access_token, expires_in = create_access_token(user.id)
    new_refresh_token = generate_refresh_token()
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
    if record and record.revoked_at is None:
        revoke_refresh_token(db, record)
        db.commit()

    return LogoutResponse(message="Logged out successfully")
