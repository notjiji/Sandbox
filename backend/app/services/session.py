import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.user import User
from app.repositories.refresh_token import (
    get_user_session_by_id,
    list_active_sessions_for_user,
    revoke_all_user_refresh_tokens,
    revoke_all_user_sessions_except,
    revoke_refresh_token,
)
from app.schemas.session import RevokeSessionResponse, SessionListResponse, SessionSummary
from app.services.audit import AuditAction, record_auth_event


def _to_session_summary(session_id: uuid.UUID | None, record) -> SessionSummary:
    return SessionSummary(
        id=str(record.id),
        created_at=record.created_at,
        expires_at=record.expires_at,
        is_current=session_id is not None and record.id == session_id,
    )


def list_user_sessions(
    db: Session,
    user: User,
    *,
    current_session_id: uuid.UUID | None = None,
) -> SessionListResponse:
    sessions = list_active_sessions_for_user(db, user.id)
    items = [_to_session_summary(current_session_id, record) for record in sessions]
    return SessionListResponse(items=items, total=len(items))


def revoke_user_session(
    db: Session,
    user: User,
    *,
    session_id: uuid.UUID,
    current_session_id: uuid.UUID | None = None,
) -> RevokeSessionResponse:
    record = get_user_session_by_id(db, user_id=user.id, session_id=session_id)
    if not record:
        raise NotFoundError("Session")

    revoked_current = current_session_id is not None and record.id == current_session_id
    if not record.revoked:
        record_auth_event(
            db,
            action=AuditAction.AUTH_SESSION_REVOKED,
            user_id=user.id,
            resource_type="session",
            resource_id=record.id,
            details={"revoked_current_session": revoked_current},
        )
        revoke_refresh_token(db, record)
        db.commit()

    return RevokeSessionResponse(
        message="Session revoked successfully",
        revoked_current_session=revoked_current,
    )


def revoke_other_sessions(
    db: Session,
    user: User,
    *,
    current_session_id: uuid.UUID,
) -> RevokeSessionResponse:
    record = get_user_session_by_id(db, user_id=user.id, session_id=current_session_id)
    if not record or record.revoked:
        raise NotFoundError("Session", "Current session not found")

    count = revoke_all_user_sessions_except(db, user.id, except_session_id=current_session_id)
    record_auth_event(
        db,
        action=AuditAction.AUTH_SESSIONS_REVOKED_OTHERS,
        user_id=user.id,
        resource_type="session",
        resource_id=current_session_id,
        details={"revoked_count": count},
    )
    db.commit()
    return RevokeSessionResponse(
        message=f"Signed out {count} other session(s)",
        revoked_current_session=False,
    )


def revoke_all_sessions(db: Session, user: User) -> RevokeSessionResponse:
    revoke_all_user_refresh_tokens(db, user.id)
    record_auth_event(
        db,
        action=AuditAction.AUTH_SESSIONS_REVOKED_ALL,
        user_id=user.id,
        resource_type="user",
        resource_id=user.id,
    )
    db.commit()
    return RevokeSessionResponse(
        message="Signed out of all sessions",
        revoked_current_session=True,
    )
