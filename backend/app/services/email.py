import resend

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("sandbox.email")


def send_password_reset_email(*, to_email: str, reset_link: str) -> None:
    settings = get_settings()
    subject = "Reset your Sandbox password"
    text = (
        "You requested a password reset for your Sandbox account.\n\n"
        f"Reset your password using this link:\n{reset_link}\n\n"
        "If you did not request this, you can ignore this email.\n"
        f"This link expires in {settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hour(s)."
    )
    html = f"""
    <p>You requested a password reset for your Sandbox account.</p>
    <p><a href="{reset_link}">Reset your password</a></p>
    <p>Or copy this link:<br><code>{reset_link}</code></p>
    <p>If you did not request this, you can ignore this email.</p>
    <p>This link expires in {settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hour(s).</p>
    """

    if not settings.RESEND_API_KEY:
        logger.info(
            "password reset email (dev mode — set RESEND_API_KEY to send real emails)",
            extra={
                "to_email": to_email,
                "reset_link": reset_link,
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
        "password reset email sent via Resend",
        extra={"to_email": to_email, "resend_id": response.get("id")},
    )


def send_verification_otp_email(*, to_email: str, otp: str) -> None:
    settings = get_settings()
    subject = "Verify your Sandbox email"
    text = (
        "Welcome to Sandbox.\n\n"
        f"Your email verification code is: {otp}\n\n"
        "Enter this code on the verification page to activate your account.\n"
        f"This code expires in {settings.EMAIL_VERIFICATION_OTP_EXPIRE_MINUTES} minutes.\n\n"
        "If you did not create an account, you can ignore this email."
    )
    html = f"""
    <p>Welcome to Sandbox.</p>
    <p>Your email verification code is:</p>
    <p style="font-size:28px;font-weight:bold;letter-spacing:6px;">{otp}</p>
    <p>Enter this code on the verification page to activate your account.</p>
    <p>This code expires in {settings.EMAIL_VERIFICATION_OTP_EXPIRE_MINUTES} minutes.</p>
    <p>If you did not create an account, you can ignore this email.</p>
    """

    if not settings.RESEND_API_KEY:
        logger.info(
            "verification OTP email (dev mode — set RESEND_API_KEY to send real emails)",
            extra={
                "to_email": to_email,
                "otp": otp,
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
        "verification OTP email sent via Resend",
        extra={"to_email": to_email, "resend_id": response.get("id")},
    )


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
