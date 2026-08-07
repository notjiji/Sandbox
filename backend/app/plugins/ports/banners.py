"""Banner/version extraction from service responses."""

from __future__ import annotations

import re

_BANNER_PATTERNS: tuple[tuple[re.Pattern[str], str, str | None], ...] = (
    (re.compile(r"OpenSSH[_\s/-]?([\d.p]+)", re.I), "ssh", "OpenSSH"),
    (re.compile(r"SSH-[\d.]+-OpenSSH[_\s/-]?([\d.p]+)", re.I), "ssh", "OpenSSH"),
    (re.compile(r"^220[- ].*?(?:vsFTPd|ProFTPD|FileZilla Server|Pure-FTPd)", re.I | re.M), "ftp", None),
    (re.compile(r"vsFTPd\s+([\d.]+)", re.I), "ftp", "vsFTPd"),
    (re.compile(r"ProFTPD\s+([\d.]+)", re.I), "ftp", "ProFTPD"),
    (re.compile(r"^220[- ].*?(?:ESMTP|Postfix|Exim|Microsoft ESMTP)", re.I | re.M), "smtp", None),
    (re.compile(r"Postfix", re.I), "smtp", "Postfix"),
    (re.compile(r"\+OK|POP3", re.I), "pop3", None),
    (re.compile(r"\* OK", re.I), "imap", None),
    (re.compile(r"-ERR wrong number of arguments|PONG|\+PONG|REDIS", re.I), "redis", "Redis"),
    (re.compile(r"redis_version:([\d.]+)", re.I), "redis", "Redis"),
    (re.compile(r"mysql_native_password|MariaDB|^\x00.*?\x0a([\d.]+)", re.I), "mysql", None),
    (re.compile(r"HTTP/[\d.]+", re.I), "http", None),
    (re.compile(r"Server:\s*nginx/([\d.]+)", re.I), "http", "nginx"),
    (re.compile(r"Server:\s*Apache/([\d.]+)", re.I), "http", "Apache"),
    (re.compile(r"MongoDB|ismaster|wire version", re.I), "mongodb", "MongoDB"),
)

_MYSQL_VERSION = re.compile(r"([\d]+\.[\d]+\.[\d]+)")


def extract_from_banner(port: int, banner: str | None) -> tuple[str | None, str | None, str | None]:
    """Return (service, product, version) inferred from banner text."""
    if not banner:
        return _service_from_port(port), None, None

    text = banner.replace("\x00", " ").strip()
    for pattern, service, product in _BANNER_PATTERNS:
        match = pattern.search(text)
        if match:
            version = match.group(1) if match.lastindex else None
            return service, product, version

    if port == 3306:
        mysql_match = _MYSQL_VERSION.search(text)
        if mysql_match:
            return "mysql", "MySQL", mysql_match.group(1)

    return _service_from_port(port), None, None


def _service_from_port(port: int) -> str | None:
    return {
        21: "ftp",
        22: "ssh",
        23: "telnet",
        25: "smtp",
        80: "http",
        443: "https",
        3306: "mysql",
        3389: "rdp",
        6379: "redis",
        27017: "mongodb",
    }.get(port)
