import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session, joinedload

from app.auth.models import EmailVerificationOtp
from app.core.security import hash_token


def revoke_user_verification_otps(db: Session, user_id: uuid.UUID) -> None:
    db.query(EmailVerificationOtp).filter(
        EmailVerificationOtp.user_id == user_id,
        EmailVerificationOtp.revoked.is_(False),
    ).update({"revoked": True}, synchronize_session=False)


def create_verification_otp(
    db: Session,
    *,
    user_id: uuid.UUID,
    otp: str,
    expires_at: datetime,
) -> EmailVerificationOtp:
    revoke_user_verification_otps(db, user_id)
    record = EmailVerificationOtp(
        user_id=user_id,
        otp_hash=hash_token(otp),
        expires_at=expires_at,
        revoked=False,
        attempts=0,
    )
    db.add(record)
    db.flush()
    return record


def get_latest_verification_otp(db: Session, user_id: uuid.UUID) -> EmailVerificationOtp | None:
    return (
        db.query(EmailVerificationOtp)
        .options(joinedload(EmailVerificationOtp.user))
        .filter(
            EmailVerificationOtp.user_id == user_id,
            EmailVerificationOtp.revoked.is_(False),
        )
        .order_by(EmailVerificationOtp.created_at.desc())
        .first()
    )


def increment_otp_attempts(db: Session, record: EmailVerificationOtp) -> None:
    record.attempts += 1
    db.add(record)


def revoke_verification_otp(db: Session, record: EmailVerificationOtp) -> None:
    record.revoked = True
    db.add(record)


def is_verification_otp_valid(record: EmailVerificationOtp) -> bool:
    if record.revoked:
        return False
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at > datetime.now(UTC)


def verify_otp_code(record: EmailVerificationOtp, otp: str) -> bool:
    return record.otp_hash == hash_token(otp)
