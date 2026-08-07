"""Optional Nmap -sV integration for rich service/version detection."""

from __future__ import annotations

import shutil
import subprocess
import xml.etree.ElementTree as ET

from app.plugins.ports.schemas import NmapServiceRaw


def nmap_available() -> bool:
    return shutil.which("nmap") is not None


def scan_versions_nmap(host: str, ports: list[int], timeout: float) -> list[NmapServiceRaw]:
    if not ports or not nmap_available():
        return []

    port_arg = ",".join(str(port) for port in sorted(set(ports)))
    command = [
        "nmap",
        "-sV",
        "-p",
        port_arg,
        "--open",
        "-oX",
        "-",
        host,
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            timeout=max(timeout, 30.0),
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return []

    if result.returncode not in (0, 1) or not result.stdout:
        return []

    return _parse_nmap_xml(result.stdout.decode("utf-8", errors="replace"))


def _parse_nmap_xml(payload: str) -> list[NmapServiceRaw]:
    services: list[NmapServiceRaw] = []
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return services

    for port_node in root.findall(".//port"):
        state = port_node.find("state")
        if state is not None and state.get("state") != "open":
            continue

        port_id = port_node.get("portid")
        if not port_id or not port_id.isdigit():
            continue

        service_node = port_node.find("service")
        if service_node is None:
            continue

        services.append(
            NmapServiceRaw(
                port=int(port_id),
                protocol=port_node.get("protocol") or "tcp",
                service_name=service_node.get("name"),
                product=service_node.get("product"),
                version=service_node.get("version"),
                extrainfo=service_node.get("extrainfo"),
            )
        )
    return services
