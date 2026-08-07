from app.plugins.base.plugin import ScanTarget
from app.plugins.security_txt import parser, rules
from app.plugins.security_txt.plugin import SecurityTxtPlugin
from app.plugins.security_txt.schemas import SecurityTxtRawResponse


VALID_SAMPLE = """\
Contact: mailto:security@example.com
Contact: https://example.com/security
Encryption: https://example.com/pgp-key.txt
Expires: 2027-12-31T23:59:59.000Z
Canonical: https://example.com/.well-known/security.txt
Preferred-Languages: en
Policy: https://example.com/security-policy
Acknowledgments: https://example.com/hall-of-fame
Hiring: https://example.com/jobs
"""


def test_parse_valid_security_txt() -> None:
    raw = SecurityTxtRawResponse(
        url="https://example.com/.well-known/security.txt",
        final_url="https://example.com/.well-known/security.txt",
        status_code=200,
        body=VALID_SAMPLE,
    )
    parsed = parser.parse(raw)

    assert parsed.present is True
    assert parsed.has_required_contact is True
    assert parsed.contact_valid is True
    assert parsed.expires_valid is True
    assert parsed.expires_expired is False
    assert parsed.encryption_valid is True
    assert parsed.canonical_valid is True
    assert parsed.canonical_matches is True
    assert parsed.validation_issues == []


def test_missing_contact_and_expires() -> None:
    raw = SecurityTxtRawResponse(
        url="https://example.com/.well-known/security.txt",
        final_url="https://example.com/.well-known/security.txt",
        status_code=200,
        body="Policy: https://example.com/security-policy\n",
    )
    parsed = parser.parse(raw)

    assert "Missing required Contact field" in parsed.validation_issues
    assert "Missing recommended Expires field" in parsed.validation_issues


def test_expired_security_txt() -> None:
    raw = SecurityTxtRawResponse(
        url="https://example.com/.well-known/security.txt",
        final_url="https://example.com/.well-known/security.txt",
        status_code=200,
        body="Contact: mailto:security@example.com\nExpires: 2020-01-01T00:00:00.000Z\n",
    )
    parsed = parser.parse(raw)

    assert parsed.expires_expired is True
    assert "Expires date is in the past" in parsed.validation_issues


def test_rules_for_missing_and_invalid_fields() -> None:
    asset = ScanTarget(asset_id="00000000-0000-4000-8000-000000000001", identifier="example.com", asset_type="website")

    missing = parser.parse(
        SecurityTxtRawResponse(url="https://example.com/.well-known/security.txt", status_code=404, body="")
    )
    missing_ids = {item.rule_id for item in rules.evaluate_rules(missing, asset, plugin_id="security_txt")}
    assert "SECURITY_TXT_MISSING" in missing_ids

    invalid = parser.parse(
        SecurityTxtRawResponse(
            url="https://example.com/.well-known/security.txt",
            final_url="https://example.com/.well-known/security.txt",
            status_code=200,
            body="Contact: not-an-email\nEncryption: ftp://bad.example/key\nCanonical: not-a-url\n",
        )
    )
    invalid_ids = {item.rule_id for item in rules.evaluate_rules(invalid, asset, plugin_id="security_txt")}
    assert "SECURITY_TXT_INVALID_CONTACT" in invalid_ids
    assert "SECURITY_TXT_INVALID_ENCRYPTION" in invalid_ids
    assert "SECURITY_TXT_INVALID_CANONICAL" in invalid_ids


def test_build_metadata_includes_validated_fields() -> None:
    raw = SecurityTxtRawResponse(
        url="https://example.com/.well-known/security.txt",
        final_url="https://example.com/.well-known/security.txt",
        status_code=200,
        body=VALID_SAMPLE,
    )
    parsed = parser.parse(raw)
    metadata = SecurityTxtPlugin().build_metadata(parsed)

    assert metadata["present"] is True
    assert metadata["contact"][0] == "mailto:security@example.com"
    assert metadata["encryption"][0].endswith("pgp-key.txt")
    assert metadata["expires"].startswith("2027-")
    assert metadata["canonical"][0].endswith("security.txt")
