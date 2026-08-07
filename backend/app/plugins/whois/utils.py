"""WHOIS scanner helpers."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime

_PRIVACY_MARKERS = (
    "redacted",
    "privacy",
    "whoisguard",
    "data protected",
    "not disclosed",
    "gdpr masked",
    "withheld for privacy",
    "domains by proxy",
    "contact privacy",
    "private registration",
    "whois privacy",
)
_EMAIL_PATTERN = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_UNKNOWN_REGISTRAR_VALUES = frozenset({"", "n/a", "na", "unknown", "not available", "none"})


def extract_domain(identifier: str) -> str:
    cleaned = identifier.strip().lower().replace("https://", "").replace("http://", "")
    host = cleaned.split("/")[0].split(":")[0].rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    return host


def normalize_datetime(value: datetime | date | list | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, list):
        value = value[0] if value else None
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime.combine(value, datetime.min.time(), tzinfo=UTC)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    return None


def days_until(target: datetime | None, *, now: datetime | None = None) -> int | None:
    if target is None:
        return None
    current = now or datetime.now(UTC)
    return (target.date() - current.date()).days


def normalize_name_servers(values: list[str] | str | None) -> list[str]:
    if not values:
        return []
    if isinstance(values, str):
        values = [values]
    servers: list[str] = []
    for value in values:
        cleaned = value.strip().lower().rstrip(".")
        if cleaned and cleaned not in servers:
            servers.append(cleaned)
    return servers


def privacy_is_enabled(*, text: str | None, registrant: str | None, emails: list[str]) -> bool | None:
    haystack = " ".join(filter(None, [text or "", registrant or ""])).lower()
    if any(marker in haystack for marker in _PRIVACY_MARKERS):
        return True

    visible_emails = [email for email in emails if email and "redact" not in email.lower()]
    if visible_emails:
        return False

    if registrant and registrant.strip() and "redact" not in registrant.lower():
        return False

    if not text and not registrant and not emails:
        return None
    return None


def is_unknown_registrar(registrar: str | None) -> bool:
    if registrar is None:
        return True
    normalized = registrar.strip().lower()
    return normalized in _UNKNOWN_REGISTRAR_VALUES


def extract_emails(*values: str | None) -> list[str]:
    emails: list[str] = []
    for value in values:
        if not value:
            continue
        emails.extend(_EMAIL_PATTERN.findall(value))
    return list(dict.fromkeys(email.lower() for email in emails))
