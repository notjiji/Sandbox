"""Async TCP connect port scanner."""

from __future__ import annotations

import asyncio
import re
import socket

from app.plugins.ports.schemas import PortProbeRaw

_COMMON_PORTS = (
    21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 993, 995, 3306, 3389, 5432, 5900, 8080, 8443, 8888, 9200, 27017,
)
_SERVICE_BY_PORT = {
    21: "ftp",
    22: "ssh",
    23: "telnet",
    25: "smtp",
    53: "dns",
    80: "http",
    110: "pop3",
    143: "imap",
    443: "https",
    445: "smb",
    993: "imaps",
    995: "pop3s",
    3306: "mysql",
    3389: "rdp",
    5432: "postgresql",
    5900: "vnc",
    8080: "http-proxy",
    8443: "https-alt",
    8888: "http-alt",
    9200: "elasticsearch",
    27017: "mongodb",
}
_BANNER_PORTS = {21, 22, 25, 110, 143}


def resolve_host(identifier: str) -> str:
    cleaned = identifier.strip()
    if cleaned.startswith(("http://", "https://")):
        from urllib.parse import urlparse

        parsed = urlparse(cleaned)
        return parsed.hostname or cleaned
    if "/" in cleaned:
        cleaned = cleaned.split("/", 1)[0]
    if cleaned.count(":") == 1 and cleaned.rsplit(":", 1)[1].isdigit():
        cleaned = cleaned.rsplit(":", 1)[0]
    return cleaned.strip("[]")


async def _probe_port(host: str, port: int, timeout: float) -> PortProbeRaw:
    probe = PortProbeRaw(port=port, open=False, service=_SERVICE_BY_PORT.get(port))
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
        probe.open = True
        if port in _BANNER_PORTS:
            try:
                if port == 22:
                    banner = await asyncio.wait_for(reader.read(256), timeout=min(timeout, 3.0))
                else:
                    writer.write(b"\r\n")
                    await writer.drain()
                    banner = await asyncio.wait_for(reader.read(256), timeout=min(timeout, 3.0))
                probe.banner = banner.decode("utf-8", errors="replace").strip() or None
            except Exception:
                probe.banner = None
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
    except (TimeoutError, asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return probe
    return probe


async def scan_ports(host: str, *, timeout: float, ports: tuple[int, ...] = _COMMON_PORTS) -> list[PortProbeRaw]:
    semaphore = asyncio.Semaphore(40)

    async def limited_probe(port: int) -> PortProbeRaw:
        async with semaphore:
            return await _probe_port(host, port, timeout)

    results = await asyncio.gather(*(limited_probe(port) for port in ports))
    return list(results)


def parse_banner_product(banner: str | None) -> tuple[str | None, str | None]:
    if not banner:
        return None, None
    ssh_match = re.search(r"OpenSSH[_\s-]?([\d.p]+)", banner, re.I)
    if ssh_match:
        return "openssh", ssh_match.group(1)
    if banner.upper().startswith("SSH-"):
        return "openssh", None
    return None, None
