"""Signed, short-lived tokens for report PDF downloads."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError

REPORT_DOWNLOAD_TOKEN_TYPE = "report_download"


def create_report_download_token(
    *,
    report_id: uuid.UUID,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
) -> tuple[str, datetime]:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.REPORT_DOWNLOAD_TOKEN_EXPIRE_MINUTES)
    payload = {
        "typ": REPORT_DOWNLOAD_TOKEN_TYPE,
        "report_id": str(report_id),
        "organization_id": str(organization_id),
        "user_id": str(user_id),
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, expires_at


def decode_report_download_token(token: str) -> dict[str, str]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise ValidationAppError("Invalid or expired download link") from exc

    if payload.get("typ") != REPORT_DOWNLOAD_TOKEN_TYPE:
        raise ValidationAppError("Invalid download link")

    report_id = payload.get("report_id")
    organization_id = payload.get("organization_id")
    user_id = payload.get("user_id")
    if not report_id or not organization_id or not user_id:
        raise ValidationAppError("Invalid download link")

    return {
        "report_id": report_id,
        "organization_id": organization_id,
        "user_id": user_id,
    }
