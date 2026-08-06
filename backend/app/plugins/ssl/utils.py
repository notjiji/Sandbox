"""Host/port helpers for the SSL scanner."""

from urllib.parse import urlparse


def resolve_host_port(identifier: str, default_port: int = 443) -> tuple[str, int]:
    cleaned = identifier.strip()
    if cleaned.startswith(("http://", "https://")):
        parsed = urlparse(cleaned)
        host = parsed.hostname or cleaned
        port = parsed.port or default_port
        return host, port

    if "/" in cleaned:
        cleaned = cleaned.split("/", 1)[0]

    if cleaned.startswith("[") and "]" in cleaned:
        host, _, remainder = cleaned.partition("]")
        host = host + "]"
        port = default_port
        if remainder.startswith(":"):
            port = int(remainder[1:])
        return host, port

    if cleaned.count(":") == 1:
        host, port_str = cleaned.rsplit(":", 1)
        if port_str.isdigit():
            return host, int(port_str)

    return cleaned, default_port


def hostname_matches_pattern(host: str, pattern: str) -> bool:
    host = host.lower().rstrip(".")
    pattern = pattern.lower().rstrip(".")
    if pattern.startswith("*."):
        suffix = pattern[1:]
        return host == pattern[2:] or host.endswith(suffix)
    return host == pattern
