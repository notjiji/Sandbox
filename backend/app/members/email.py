import resend

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("sandbox.email")


def send_organization_invite_email(
    *,
    to_email: str,
    organization_name: str,
    role: str,
    invite_link: str,
    inviter_name: str,
) -> None:
    settings = get_settings()
    subject = f"You've been invited to join {organization_name} on Sandbox"
    text = (
        f"{inviter_name} invited you to join {organization_name} on Sandbox as {role}.\n\n"
        f"Accept your invitation:\n{invite_link}\n\n"
        f"This invitation expires in {settings.ORGANIZATION_INVITE_EXPIRE_DAYS} day(s).\n"
        "If you did not expect this invitation, you can ignore this email."
    )
    html = f"""
    <p><strong>{inviter_name}</strong> invited you to join
    <strong>{organization_name}</strong> on Sandbox as <strong>{role}</strong>.</p>
    <p><a href="{invite_link}">Accept invitation</a></p>
    <p>Or copy this link:<br><code>{invite_link}</code></p>
    <p>This invitation expires in {settings.ORGANIZATION_INVITE_EXPIRE_DAYS} day(s).</p>
    <p>If you did not expect this invitation, you can ignore this email.</p>
    """

    if not settings.RESEND_API_KEY:
        logger.info(
            "organization invite email (dev mode — set RESEND_API_KEY to send real emails)",
            extra={
                "to_email": to_email,
                "organization_name": organization_name,
                "invite_link": invite_link,
            },
        )
        return

    resend.api_key = settings.RESEND_API_KEY
    response = resend.Emails.send(
        {
            "from": settings.RESEND_FROM,
            "to": [to_email],
            "subject": subject,
            "text": text,
            "html": html,
        }
    )

    logger.info(
        "organization invite email sent via Resend",
        extra={"to_email": to_email, "resend_id": response.get("id")},
    )
