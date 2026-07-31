"""Type-specific asset metadata validation."""

import ipaddress
import re
import uuid
from urllib.parse import urlparse

from app.assets.enums import AssetType
from app.assets.metadata import PRIMARY_METADATA_KEYS
from app.core.exceptions import ValidationAppError

DOMAIN_PATTERN = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$",
    re.IGNORECASE,
)
HOSTNAME_PATTERN = re.compile(
    r"^[a-zA-Z0-9](?:[a-zA-Z0-9.-]{0,253}[a-zA-Z0-9])?$",
)
BUNDLE_ID_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+$")
S3_BUCKET_PATTERN = re.compile(r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")
ACCOUNT_ID_PATTERN = re.compile(r"^[A-Za-z0-9:_-]{3,128}$")

SERVER_REQUIRED_FIELDS: tuple[tuple[str, str], ...] = (
    ("hostname", "Hostname"),
    ("os", "Operating System"),
    ("connection_type", "Connection Type"),
)

WINDOWS_SERVER_REQUIRED_FIELDS: tuple[tuple[str, str], ...] = (
    ("hostname", "Hostname"),
    ("os", "Operating System"),
    ("connection_type", "Connection Type"),
)

ALLOWED_CONNECTION_TYPES = frozenset({"ssh", "rdp", "winrm", "agent", "snmp", "other"})


def _require(value: str, *, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValidationAppError(f"{label} is required")
    return normalized


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


def validate_api_endpoint(endpoint: str) -> str:
    value = _require(endpoint, label="API endpoint")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise ValidationAppError("API endpoint must start with http:// or https://")
    if not parsed.netloc:
        raise ValidationAppError("API endpoint must include a valid host")
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


def validate_connection_type(connection_type: str) -> str:
    value = connection_type.strip().lower()
    if value not in ALLOWED_CONNECTION_TYPES:
        allowed = ", ".join(sorted(ALLOWED_CONNECTION_TYPES))
        raise ValidationAppError(f"Connection type must be one of: {allowed}")
    return value


def _validate_host_fields(
    metadata: dict[str, str],
    *,
    required_fields: tuple[tuple[str, str], ...],
) -> None:
    for key, label in required_fields:
        if not metadata.get(key, "").strip():
            raise ValidationAppError(f"Asset requires {label}")

    validate_hostname(metadata["hostname"])

    if "connection_type" in dict(required_fields):
        validate_connection_type(metadata["connection_type"])


def validate_server_metadata(metadata: dict[str, str]) -> None:
    _validate_host_fields(metadata, required_fields=SERVER_REQUIRED_FIELDS)


def validate_windows_server_metadata(metadata: dict[str, str]) -> None:
    _validate_host_fields(metadata, required_fields=WINDOWS_SERVER_REQUIRED_FIELDS)


def validate_docker_host_metadata(metadata: dict[str, str]) -> None:
    validate_hostname(metadata.get("hostname", ""))


def validate_cloud_account_metadata(metadata: dict[str, str]) -> None:
    value = _require(metadata.get("account_id", ""), label="Cloud account ID")
    if not ACCOUNT_ID_PATTERN.match(value):
        raise ValidationAppError("Cloud account ID must be 3-128 alphanumeric characters")


def validate_kubernetes_cluster_metadata(metadata: dict[str, str]) -> None:
    _require(metadata.get("cluster", ""), label="Cluster name")


def validate_mobile_application_metadata(metadata: dict[str, str]) -> None:
    value = _require(metadata.get("bundle_id", ""), label="Bundle ID")
    if not BUNDLE_ID_PATTERN.match(value):
        raise ValidationAppError("Bundle ID must look like com.example.app")


def validate_git_repository_metadata(metadata: dict[str, str]) -> None:
    value = _require(metadata.get("repository", ""), label="Git repository")
    if " " in value:
        raise ValidationAppError("Git repository must not contain spaces")


def validate_s3_bucket_metadata(metadata: dict[str, str]) -> None:
    value = _require(metadata.get("bucket", ""), label="S3 bucket name").lower()
    if len(value) < 3 or len(value) > 63 or not S3_BUCKET_PATTERN.match(value):
        raise ValidationAppError("S3 bucket name must be 3-63 lowercase characters")


def validate_azure_subscription_metadata(metadata: dict[str, str]) -> None:
    value = _require(metadata.get("subscription_id", ""), label="Azure subscription ID")
    try:
        uuid.UUID(value)
    except ValueError as exc:
        raise ValidationAppError("Azure subscription ID must be a valid UUID") from exc


def validate_asset_metadata(
    asset_type: AssetType,
    metadata: dict[str, str],
    *,
    allow_private: bool = False,
) -> None:
    """Validate metadata for all asset types before save."""
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

    if asset_type == AssetType.WINDOWS_SERVER:
        validate_windows_server_metadata(metadata)
        return

    if asset_type == AssetType.DOCKER_HOST:
        validate_docker_host_metadata(metadata)
        return

    if asset_type == AssetType.CLOUD_ACCOUNT:
        validate_cloud_account_metadata(metadata)
        return

    if asset_type == AssetType.KUBERNETES_CLUSTER:
        validate_kubernetes_cluster_metadata(metadata)
        return

    if asset_type == AssetType.API_ENDPOINT:
        validate_api_endpoint(metadata.get("endpoint", ""))
        return

    if asset_type == AssetType.MOBILE_APPLICATION:
        validate_mobile_application_metadata(metadata)
        return

    if asset_type == AssetType.GIT_REPOSITORY:
        validate_git_repository_metadata(metadata)
        return

    if asset_type == AssetType.EMAIL_DOMAIN:
        validate_domain_name(metadata.get("email_domain", ""), label="Email domain")
        return

    if asset_type == AssetType.S3_BUCKET:
        validate_s3_bucket_metadata(metadata)
        return

    if asset_type == AssetType.AZURE_SUBSCRIPTION:
        validate_azure_subscription_metadata(metadata)
        return

    primary_key = PRIMARY_METADATA_KEYS.get(asset_type)
    if primary_key:
        _require(metadata.get(primary_key, ""), label=primary_key.replace("_", " "))
