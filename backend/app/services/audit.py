import uuid

from sqlalchemy.orm import Session

from app.core.request_context import get_request_context
from app.repositories.audit import create_audit_log
from app.repositories.user import get_primary_membership


class AuditAction:
    AUTH_REGISTER = "auth.register"
    AUTH_LOGIN = "auth.login"
    AUTH_LOGIN_FAILED = "auth.login_failed"
    AUTH_ACCOUNT_LOCKED = "auth.account_locked"
    AUTH_LOGOUT = "auth.logout"
    AUTH_REFRESH = "auth.refresh"
    AUTH_PASSWORD_CHANGE = "auth.password_change"
    AUTH_PASSWORD_RESET_REQUEST = "auth.password_reset_request"
    AUTH_PASSWORD_RESET = "auth.password_reset"
    AUTH_EMAIL_VERIFIED = "auth.email_verified"
    AUTH_SESSION_REVOKED = "auth.session_revoked"
    AUTH_SESSIONS_REVOKED_OTHERS = "auth.sessions_revoked_others"
    AUTH_SESSIONS_REVOKED_ALL = "auth.sessions_revoked_all"
    USER_PROFILE_UPDATE = "user.profile_update"
    ORG_UPDATE = "org.update"
    ORG_DELETE = "org.delete"
    ORG_CREATE = "org.create"
    ORG_MEMBER_INVITE = "org.member_invite"
    ORG_MEMBER_INVITE_REVOKE = "org.member_invite_revoke"
    ORG_MEMBER_ACCEPT = "org.member_accept"
    ORG_MEMBER_UPDATE = "org.member_update"
    ORG_MEMBER_REMOVE = "org.member_remove"
    ORG_OWNERSHIP_TRANSFER = "org.ownership_transfer"
    PROJECT_CREATE = "project.create"
    PROJECT_UPDATE = "project.update"
    PROJECT_DELETE = "project.delete"
    ASSET_CREATE = "asset.create"
    ASSET_UPDATE = "asset.update"
    ASSET_DELETE = "asset.delete"
    SCAN_CREATE = "scan.create"
    SCAN_RUN = "scan.run"
    SCAN_CANCEL = "scan.cancel"
    FINDING_UPDATE = "finding.update"
    FINDING_REVIEW = "finding.review"
    REPORT_CREATE = "report.create"
    REPORT_UPDATE = "report.update"
    REPORT_GENERATE = "report.generate"
    REPORT_DELETE = "report.delete"


def primary_organization_id(db: Session, user_id: uuid.UUID) -> uuid.UUID | None:
    membership = get_primary_membership(db, user_id)
    return membership.organization_id if membership else None


def record_audit_event(
    db: Session,
    *,
    action: str,
    user_id: uuid.UUID | None = None,
    organization_id: uuid.UUID | None = None,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    details: dict | None = None,
) -> None:
    context = get_request_context()
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


def record_auth_event(
    db: Session,
    *,
    action: str,
    user_id: uuid.UUID | None = None,
    resource_type: str | None = "session",
    resource_id: uuid.UUID | None = None,
    details: dict | None = None,
) -> None:
    org_id = primary_organization_id(db, user_id) if user_id else None
    record_audit_event(
        db,
        action=action,
        user_id=user_id,
        organization_id=org_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )
