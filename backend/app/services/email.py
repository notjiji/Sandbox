import smtplib
from email.message import EmailMessage

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("sandbox.email")


def send_password_reset_email(*, to_email: str, reset_link: str) -> None:
    settings = get_settings()
    subject = "Reset your Sandbox password"
    body = (
        "You requested a password reset for your Sandbox account.\n\n"
        f"Reset your password using this link:\n{reset_link}\n\n"
        "If you did not request this, you can ignore this email.\n"
        f"This link expires in {settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hour(s)."
    )

    if not settings.SMTP_HOST:
        logger.info(
            "password reset email (dev mode)",
            extra={
                "to_email": to_email,
                "reset_link": reset_link,
            },
        )
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM
    message["To"] = to_email
    message.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(message)

    logger.info("password reset email sent", extra={"to_email": to_email})
