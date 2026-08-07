"""Async TCP connect scan with protocol-aware banner capture."""

from __future__ import annotations

import asyncio

from app.plugins.ports.banners import extract_from_banner
from app.plugins.ports.schemas import NmapServiceRaw, PortProbeRaw

SCAN_PORTS: tuple[int, ...] = (
    21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 993, 995, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 8888, 9200, 27017,
)


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


async def _read_banner(reader: asyncio.StreamReader, *, timeout: float, max_bytes: int = 512) -> str | None:
    try:
        data = await asyncio.wait_for(reader.read(max_bytes), timeout=timeout)
    except (TimeoutError, asyncio.TimeoutError):
        return None
    if not data:
        return None
    return data.decode("utf-8", errors="replace").strip()


async def _grab_banner(host: str, port: int, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, timeout: float) -> str | None:
    probe_timeout = min(timeout, 3.0)
    if port == 22:
        return await _read_banner(reader, timeout=probe_timeout)

    if port in {21, 25, 110, 143}:
        return await _read_banner(reader, timeout=probe_timeout)

    if port in {80, 8080, 8443, 8888}:
        request = f"GET / HTTP/1.0\r\nHost: {host}\r\n\r\n".encode()
        writer.write(request)
        await writer.drain()
        return await _read_banner(reader, timeout=probe_timeout)

    if port == 6379:
        writer.write(b"PING\r\n")
        await writer.drain()
        banner = await _read_banner(reader, timeout=probe_timeout)
        if banner:
            return banner
        writer.write(b"INFO\r\n")
        await writer.drain()
        return await _read_banner(reader, timeout=probe_timeout, max_bytes=1024)

    if port == 3306:
        return await _read_banner(reader, timeout=probe_timeout, max_bytes=256)

    if port == 27017:
        # Minimal wire probe; many deployments require auth — connect success is enough for open detection.
        return None

    if port == 3389:
        return None

    writer.write(b"\r\n")
    await writer.drain()
    return await _read_banner(reader, timeout=probe_timeout)


async def probe_port(host: str, port: int, timeout: float) -> PortProbeRaw:
    probe = PortProbeRaw(port=port, open=False)
    writer = None
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
        probe.open = True
        probe.banner = await _grab_banner(host, port, reader, writer, timeout)
        _, _, version = extract_from_banner(port, probe.banner)
        probe.version = version
    except (TimeoutError, asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return probe
    finally:
        if writer is not None:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
    return probe


async def scan_ports(host: str, *, timeout: float, ports: tuple[int, ...] = SCAN_PORTS) -> list[PortProbeRaw]:
    semaphore = asyncio.Semaphore(40)

    async def limited_probe(port: int) -> PortProbeRaw:
        async with semaphore:
            return await probe_port(host, port, timeout)

    return list(await asyncio.gather(*(limited_probe(port) for port in ports)))


def merge_nmap_into_probes(probes: list[PortProbeRaw], nmap_services: list[NmapServiceRaw]) -> list[PortProbeRaw]:
    if not nmap_services:
        return probes

    nmap_by_port = {service.port: service for service in nmap_services}
    merged: list[PortProbeRaw] = []
    for probe in probes:
        nmap = nmap_by_port.get(probe.port)
        if not nmap:
            merged.append(probe)
            continue
        version_parts = [part for part in (nmap.version, nmap.extrainfo) if part]
        merged.append(
            probe.model_copy(
                update={
                    "version": " ".join(version_parts) if version_parts else probe.version,
                    "banner": probe.banner or _nmap_banner(nmap),
                }
            )
        )
    return merged


def _nmap_banner(nmap: NmapServiceRaw) -> str | None:
    parts = [part for part in (nmap.product, nmap.version, nmap.extrainfo) if part]
    return " ".join(parts) if parts else nmap.service_name
