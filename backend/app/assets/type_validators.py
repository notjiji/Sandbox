"""Type-specific asset metadata validation."""

import ipaddress
import re
from urllib.parse import urlparse

from app.assets.enums import AssetType
from app.core.exceptions import ValidationAppError

DOMAIN_PATTERN = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$",
    re.IGNORECASE,
)
HOSTNAME_PATTERN = re.compile(
    r"^[a-zA-Z0-9](?:[a-zA-Z0-9.-]{0,253}[a-zA-Z0-9])?$",
)

SERVER_REQUIRED_FIELDS: tuple[tuple[str, str], ...] = (
    ("hostname", "Hostname"),
    ("os", "Operating System"),
    ("connection_type", "Connection Type"),
)

ALLOWED_CONNECTION_TYPES = frozenset({"ssh", "rdp", "winrm", "agent", "snmp", "other"})


def validate_website_url(url: str) -> str:
    value = url.strip()
    if not value:
        raise ValidationAppError("Website assets require a URL")

    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise ValidationAppError("Website URL must start with http:// or https://")
    if parsed.username or parsed.password:
        raise ValidationAppError("Website URL must not include credentials")
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ValidationAppError("Website URL must not include a path, query, or fragment")

    host = parsed.hostname
    if not host:
        raise ValidationAppError("Website URL must include a valid hostname")
    validate_domain_name(host, label="Website URL hostname")
    return value


def validate_domain_name(domain: str, *, label: str = "Domain") -> str:
    value = domain.strip().lower().rstrip(".")
    if not value:
        raise ValidationAppError(f"{label} is required")
    if "://" in value or "/" in value or "@" in value or " " in value:
        raise ValidationAppError(f"{label} must be a domain name (e.g. vinca.family)")
    if "." not in value:
        raise ValidationAppError(f"{label} must include a valid top-level domain (e.g. vinca.family)")
    if not DOMAIN_PATTERN.match(value):
        raise ValidationAppError(f"{label} must be a valid domain name (e.g. vinca.family)")
    return value


def _is_disallowed_private_ipv4(ip: ipaddress.IPv4Address) -> bool:
    """True for RFC1918, loopback, and link-local addresses."""
    if ip.is_loopback or ip.is_link_local:
        return True
    return any(
        ip in network
        for network in (
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("192.168.0.0/16"),
        )
    )


def validate_public_ipv4(address: str, *, allow_private: bool = False) -> str:
    value = address.strip()
    if not value:
        raise ValidationAppError("Public IP assets require an IP address")

    try:
        ip = ipaddress.ip_address(value)
    except ValueError as exc:
        raise ValidationAppError("Public IP must be a valid IPv4 address") from exc

    if ip.version != 4:
        raise ValidationAppError("Public IP must be an IPv4 address")

    if not allow_private and _is_disallowed_private_ipv4(ip):
        raise ValidationAppError(
            "Private IP addresses are not allowed unless explicitly permitted"
        )
    return value


def validate_hostname(hostname: str) -> str:
    value = hostname.strip()
    if not value:
        raise ValidationAppError("Hostname is required")
    if len(value) > 255 or not HOSTNAME_PATTERN.match(value):
        raise ValidationAppError("Hostname must be a valid hostname")
    return value


def validate_server_metadata(metadata: dict[str, str]) -> None:
    for key, label in SERVER_REQUIRED_FIELDS:
        if not metadata.get(key, "").strip():
            raise ValidationAppError(f"Server assets require {label}")

    validate_hostname(metadata["hostname"])

    connection_type = metadata["connection_type"].strip().lower()
    if connection_type not in ALLOWED_CONNECTION_TYPES:
        allowed = ", ".join(sorted(ALLOWED_CONNECTION_TYPES))
        raise ValidationAppError(f"Connection type must be one of: {allowed}")


def validate_asset_metadata(
    asset_type: AssetType,
    metadata: dict[str, str],
    *,
    allow_private: bool = False,
) -> None:
    """Validate metadata for supported asset types before save."""
    if asset_type == AssetType.WEBSITE:
        validate_website_url(metadata.get("url", ""))
        return

    if asset_type == AssetType.DOMAIN:
        validate_domain_name(metadata.get("domain", ""))
        return

    if asset_type == AssetType.PUBLIC_IP:
        validate_public_ipv4(metadata.get("address", ""), allow_private=allow_private)
        return

    if asset_type == AssetType.SERVER:
        validate_server_metadata(metadata)
        return
