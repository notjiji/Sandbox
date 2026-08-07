"""RFC 9116 field parsing and validation."""

from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import urlparse

from app.plugins.security_txt.schemas import SecurityTxtFieldValidation, SecurityTxtParsedData


def _strip_comment(line: str) -> str:
    if "#" in line:
        return line.split("#", 1)[0].strip()
    return line.strip()


def parse_fields(body: str) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    for raw_line in body.splitlines():
        line = _strip_comment(raw_line)
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        normalized_key = key.strip().lower()
        cleaned_value = value.strip()
        if cleaned_value:
            fields.setdefault(normalized_key, []).append(cleaned_value)
    return fields


def _parse_expires(value: str) -> datetime | None:
    cleaned = value.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _is_valid_contact(value: str) -> bool:
    cleaned = value.strip()
    lowered = cleaned.lower()
    if lowered.startswith("mailto:"):
        return "@" in cleaned[7:]
    if lowered.startswith("https://") or lowered.startswith("http://"):
        return bool(urlparse(cleaned).netloc)
    return "@" in cleaned and "." in cleaned.split("@", 1)[1]


def _is_valid_uri(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme in {"https", "http"} and bool(parsed.netloc)


def _normalize_url(url: str) -> str:
    parsed = urlparse(url.strip().rstrip("/"))
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"


def validate_fields(
    fields: dict[str, list[str]],
    *,
    fetched_url: str,
    final_url: str | None,
) -> SecurityTxtParsedData:
    contacts = fields.get("contact", [])
    encryption = fields.get("encryption", [])
    expires_values = fields.get("expires", [])
    canonical = fields.get("canonical", [])

    validation_issues: list[str] = []
    field_validations: list[SecurityTxtFieldValidation] = []

    has_required_contact = bool(contacts)
    contact_valid = bool(contacts) and all(_is_valid_contact(item) for item in contacts)
    if not has_required_contact:
        validation_issues.append("Missing required Contact field")
        field_validations.append(
            SecurityTxtFieldValidation(field="Contact", valid=False, message="At least one Contact is required")
        )
    elif not contact_valid:
        validation_issues.append("One or more Contact values are invalid")
        field_validations.append(
            SecurityTxtFieldValidation(
                field="Contact",
                valid=False,
                message="Contact must be a mailto:, https:, or email address",
            )
        )
    else:
        field_validations.append(SecurityTxtFieldValidation(field="Contact", valid=True))

    expires_raw = expires_values[0] if expires_values else None
    expires_at: datetime | None = None
    expires_valid = False
    expires_expired = False
    if not expires_raw:
        validation_issues.append("Missing recommended Expires field")
        field_validations.append(
            SecurityTxtFieldValidation(field="Expires", valid=False, message="Expires is recommended by RFC 9116")
        )
    else:
        expires_at = _parse_expires(expires_raw)
        if expires_at is None:
            validation_issues.append("Expires value is not a valid ISO 8601 timestamp")
            field_validations.append(
                SecurityTxtFieldValidation(field="Expires", valid=False, message="Invalid ISO 8601 date")
            )
        else:
            expires_valid = True
            expires_expired = expires_at <= datetime.now(UTC)
            if expires_expired:
                validation_issues.append("Expires date is in the past")
                field_validations.append(
                    SecurityTxtFieldValidation(field="Expires", valid=False, message="Expires date has passed")
                )
            else:
                field_validations.append(SecurityTxtFieldValidation(field="Expires", valid=True))

    encryption_valid = True
    if encryption:
        invalid = [item for item in encryption if not _is_valid_uri(item)]
        if invalid:
            encryption_valid = False
            validation_issues.append("One or more Encryption values are invalid URIs")
            field_validations.append(
                SecurityTxtFieldValidation(field="Encryption", valid=False, message="Encryption must be a valid URI")
            )
        else:
            field_validations.append(SecurityTxtFieldValidation(field="Encryption", valid=True))
    else:
        field_validations.append(
            SecurityTxtFieldValidation(field="Encryption", valid=True, message="Optional field not present")
        )

    canonical_valid = True
    canonical_matches: bool | None = None
    if canonical:
        invalid = [item for item in canonical if not _is_valid_uri(item)]
        if invalid:
            canonical_valid = False
            validation_issues.append("One or more Canonical values are invalid URIs")
            field_validations.append(
                SecurityTxtFieldValidation(field="Canonical", valid=False, message="Canonical must be a valid URI")
            )
        else:
            compare_url = final_url or fetched_url
            canonical_matches = any(
                _normalize_url(item) == _normalize_url(compare_url) for item in canonical
            )
            if not canonical_matches:
                validation_issues.append("Canonical URI does not match downloaded security.txt location")
                field_validations.append(
                    SecurityTxtFieldValidation(
                        field="Canonical",
                        valid=False,
                        message="Canonical should point to the authoritative security.txt URL",
                    )
                )
            else:
                field_validations.append(SecurityTxtFieldValidation(field="Canonical", valid=True))
    else:
        field_validations.append(
            SecurityTxtFieldValidation(field="Canonical", valid=True, message="Optional field not present")
        )

    return SecurityTxtParsedData(
        url=fetched_url,
        final_url=final_url,
        present=True,
        contacts=contacts,
        encryption=encryption,
        expires=expires_raw,
        expires_at=expires_at.isoformat() if expires_at else None,
        expires_valid=expires_valid,
        expires_expired=expires_expired,
        canonical=canonical,
        acknowledgments=fields.get("acknowledgments", []),
        policy=fields.get("policy", []),
        hiring=fields.get("hiring", []),
        preferred_languages=fields.get("preferred-languages", []),
        has_required_contact=has_required_contact,
        contact_valid=contact_valid,
        encryption_valid=encryption_valid,
        canonical_valid=canonical_valid,
        canonical_matches=canonical_matches,
        validation_issues=validation_issues,
        field_validations=field_validations,
    )
