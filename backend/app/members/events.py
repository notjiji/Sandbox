"""Audit event names for the members feature."""


class MemberAuditAction:
    INVITE = "org.member_invite"
    INVITE_REVOKE = "org.member_invite_revoke"
    INVITE_RESEND = "org.member_invite_resend"
    ACCEPT = "org.member_accept"
    UPDATE = "org.member_update"
    REMOVE = "org.member_remove"
    OWNERSHIP_TRANSFER = "org.ownership_transfer"
