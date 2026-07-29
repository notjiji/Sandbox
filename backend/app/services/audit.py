import uuid

from sqlalchemy.orm import Session

from app.core.request_context import RequestContext
from app.repositories.audit import create_audit_log


class AuditAction:
    AUTH_REGISTER = "auth.register"
    AUTH_LOGIN = "auth.login"
    AUTH_LOGIN_FAILED = "auth.login_failed"
    AUTH_LOGOUT = "auth.logout"
    AUTH_REFRESH = "auth.refresh"
    AUTH_PASSWORD_CHANGE = "auth.password_change"
    AUTH_PASSWORD_RESET = "auth.password_reset"
    AUTH_EMAIL_VERIFIED = "auth.email_verified"
    AUTH_SESSION_REVOKED = "auth.session_revoked"
    USER_PROFILE_UPDATE = "user.profile_update"


def record_audit_event(
    db: Session,
    *,
    action: str,
    user_id: uuid.UUID | None = None,
    organization_id: uuid.UUID | None = None,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    details: dict | None = None,
    context: RequestContext | None = None,
) -> None:
    create_audit_log(
        db,
        action=action,
        user_id=user_id,
        organization_id=organization_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=context.ip_address if context else None,
        user_agent=context.user_agent if context else None,
    )
