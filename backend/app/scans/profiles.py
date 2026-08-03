"""Reusable scan profiles — map profile names to plugin sets."""

from app.core.exceptions import ValidationAppError
from app.scans.enums import ScanType

# Plugin slugs per profile (order = execution order)
SCAN_PROFILE_PLUGINS: dict[ScanType, list[str]] = {
    ScanType.QUICK: ["http_headers", "ssl", "dns"],
    ScanType.FULL: ["http_headers", "ssl", "dns", "whois", "ports"],
}

SCAN_PROFILE_LABELS: dict[ScanType, str] = {
    ScanType.QUICK: "Quick Scan",
    ScanType.FULL: "Full Scan",
    ScanType.CUSTOM: "Custom Scan",
}

SCAN_PROFILE_DESCRIPTIONS: dict[ScanType, str] = {
    ScanType.QUICK: "Fast baseline checks — HTTP headers, SSL, and DNS.",
    ScanType.FULL: "Comprehensive scan — HTTP, SSL, DNS, WHOIS, and port checks.",
    ScanType.CUSTOM: "Choose exactly which scanners to run.",
}


def resolve_profile_plugins(
    scan_type: ScanType,
    selected_plugins: list[str] | None = None,
) -> list[str]:
    """Return the plugin slugs to run for a scan profile."""
    if scan_type == ScanType.CUSTOM:
        if not selected_plugins:
            raise ValidationAppError("Custom scans require at least one plugin")
        seen: set[str] = set()
        ordered: list[str] = []
        for name in selected_plugins:
            slug = name.strip()
            if not slug or slug in seen:
                continue
            seen.add(slug)
            ordered.append(slug)
        if not ordered:
            raise ValidationAppError("Custom scans require at least one plugin")
        return ordered

    plugins = SCAN_PROFILE_PLUGINS.get(scan_type)
    if not plugins:
        raise ValidationAppError(f"Unknown scan profile: {scan_type.value}")
    return list(plugins)


def list_scan_profiles(*, available_plugins: list[str] | None = None) -> list[dict]:
    """Return profile metadata for API consumers."""
    available = set(available_plugins or [])
    profiles: list[dict] = []
    for scan_type in (ScanType.QUICK, ScanType.FULL, ScanType.CUSTOM):
        if scan_type == ScanType.CUSTOM:
            plugins = sorted(available) if available else []
        else:
            plugins = SCAN_PROFILE_PLUGINS[scan_type]
        profiles.append(
            {
                "profile": scan_type.value,
                "label": SCAN_PROFILE_LABELS[scan_type],
                "description": SCAN_PROFILE_DESCRIPTIONS[scan_type],
                "plugins": plugins,
            }
        )
    return profiles
