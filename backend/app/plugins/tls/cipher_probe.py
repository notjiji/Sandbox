"""TLS cipher and protocol probing — distinct from certificate-focused SSL scanner."""

from __future__ import annotations

import asyncio
import re
import shutil
import socket
import ssl
import subprocess

from app.plugins.ssl.legacy_probe import merge_protocol_probes, probe_protocols_openssl
from app.plugins.ssl.schemas import ProtocolProbeRaw
from app.plugins.ssl.utils import is_weak_cipher_name, resolve_host_port

_PROTOCOL_PROBES: list[tuple[str, ssl.TLSVersion, ssl.TLSVersion]] = [
    ("TLSv1.0", ssl.TLSVersion.TLSv1, ssl.TLSVersion.TLSv1),
    ("TLSv1.1", ssl.TLSVersion.TLSv1_1, ssl.TLSVersion.TLSv1_1),
    ("TLSv1.2", ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_2),
    ("TLSv1.3", ssl.TLSVersion.TLSv1_3, ssl.TLSVersion.TLSv1_3),
]

_CIPHER_CANDIDATES = (
    "ECDHE-RSA-AES128-GCM-SHA256",
    "ECDHE-RSA-AES128-SHA",
    "ECDHE-RSA-AES256-GCM-SHA384",
    "AES128-GCM-SHA256",
    "AES128-SHA",
    "AES256-SHA",
    "DES-CBC3-SHA",
    "RC4-SHA",
    "NULL-SHA",
)


def _create_context(*, min_version: ssl.TLSVersion, max_version: ssl.TLSVersion) -> ssl.SSLContext:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    context.minimum_version = min_version
    context.maximum_version = max_version
    try:
        context.set_ciphers("DEFAULT:@SECLEVEL=0")
    except ssl.SSLError:
        pass
    return context


def _connect_cipher(host: str, port: int, cipher: str, timeout: float) -> str | None:
    context = _create_context(min_version=ssl.TLSVersion.TLSv1_2, max_version=ssl.TLSVersion.TLSv1_2)
    try:
        context.set_ciphers(cipher)
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as sslobj:
                negotiated = sslobj.cipher()
                return negotiated[0] if negotiated else None
    except Exception:
        return None


def _probe_protocol(host: str, port: int, version_label: str, min_ver: ssl.TLSVersion, max_ver: ssl.TLSVersion, timeout: float) -> ProtocolProbeRaw:
    context = _create_context(min_version=min_ver, max_version=max_ver)
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as sslobj:
                return ProtocolProbeRaw(version=version_label, accepted=True, negotiated=sslobj.version())
    except Exception as exc:
        return ProtocolProbeRaw(version=version_label, accepted=False, error=str(exc))


def _default_negotiated_cipher(host: str, port: int, timeout: float) -> str | None:
    context = _create_context(
        min_version=ssl.TLSVersion.MINIMUM_SUPPORTED,
        max_version=ssl.TLSVersion.MAXIMUM_SUPPORTED,
    )
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as sslobj:
                negotiated = sslobj.cipher()
                return negotiated[0] if negotiated else None
    except Exception:
        return None


def _probe_ciphers_openssl(host: str, port: int, timeout: float) -> list[str]:
    openssl = shutil.which("openssl")
    if not openssl:
        return []

    try:
        result = subprocess.run(
            [openssl, "ciphers", "ALL:COMPLEMENTOFALL"],
            capture_output=True,
            text=True,
            timeout=min(timeout, 10.0),
            check=False,
        )
    except Exception:
        return []

    accepted: list[str] = []
    for cipher in result.stdout.split(":")[:40]:
        cipher = cipher.strip()
        if not cipher:
            continue
        try:
            probe = subprocess.run(
                [
                    openssl,
                    "s_client",
                    "-connect",
                    f"{host}:{port}",
                    "-servername",
                    host,
                    "-cipher",
                    cipher,
                    "-tls1_2",
                ],
                input=b"",
                capture_output=True,
                text=True,
                timeout=min(timeout, 5.0),
                check=False,
            )
        except Exception:
            continue
        if "Cipher is (NONE)" in probe.stdout or "connect:errno" in probe.stdout.lower():
            continue
        match = re.search(r"Cipher\s*:\s*(\S+)", probe.stdout)
        if match:
            accepted.append(match.group(1))
    return list(dict.fromkeys(accepted))


def _collect_sync(host: str, port: int, timeout: float) -> dict:
    stdlib_probes = [
        _probe_protocol(host, port, label, min_ver, max_ver, timeout)
        for label, min_ver, max_ver in _PROTOCOL_PROBES
    ]
    openssl_probes = probe_protocols_openssl(host, port, timeout)
    protocol_probes = merge_protocol_probes(stdlib_probes, openssl_probes)

    accepted_ciphers: list[str] = []
    for cipher in _CIPHER_CANDIDATES:
        negotiated = _connect_cipher(host, port, cipher, timeout)
        if negotiated:
            accepted_ciphers.append(negotiated)

    openssl_ciphers = _probe_ciphers_openssl(host, port, timeout)
    for cipher in openssl_ciphers:
        if cipher not in accepted_ciphers:
            accepted_ciphers.append(cipher)

    negotiated_cipher = _default_negotiated_cipher(host, port, timeout)
    weak_ciphers = [cipher for cipher in accepted_ciphers if is_weak_cipher_name(cipher)]

    return {
        "host": host,
        "port": port,
        "protocol_probes": protocol_probes,
        "accepted_ciphers": accepted_ciphers,
        "weak_ciphers_accepted": weak_ciphers,
        "negotiated_cipher": negotiated_cipher,
    }


async def collect_sync(host: str, port: int, timeout: float) -> dict:
    return await asyncio.to_thread(_collect_sync, host, port, timeout)


def resolve_tls_target(identifier: str) -> tuple[str, int]:
    return resolve_host_port(identifier)
