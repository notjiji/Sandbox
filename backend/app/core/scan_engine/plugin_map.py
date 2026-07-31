"""Maps scan types to plugin names executed by the engine."""

from app.scans.enums import ScanType

SCAN_TYPE_PLUGINS: dict[ScanType, list[str]] = {
    ScanType.FULL: ["http_headers", "ssl", "dns", "whois", "ports"],
    ScanType.QUICK: ["http_headers", "dns"],
}
