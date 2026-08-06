"""Collect raw TLS/certificate data — no findings."""

from __future__ import annotations

import asyncio
import base64
import socket
import ssl
from typing import Any

from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.ssl.schemas import CipherRaw, ProtocolProbeRaw, SslRawResponse
from app.plugins.ssl.utils import resolve_host_port

_PROTOCOL_PROBES: list[tuple[str, ssl.TLSVersion, ssl.TLSVersion]] = [
    ("TLSv1.0", ssl.TLSVersion.TLSv1, ssl.TLSVersion.TLSv1),
    ("TLSv1.1", ssl.TLSVersion.TLSv1_1, ssl.TLSVersion.TLSv1_1),
    ("TLSv1.2", ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_2),
    ("TLSv1.3", ssl.TLSVersion.TLSv1_3, ssl.TLSVersion.TLSv1_3),
]


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


def _cipher_from_tuple(cipher: tuple[str, str, int] | None) -> CipherRaw | None:
    if not cipher:
        return None
    name, protocol, secret_bits = cipher
    return CipherRaw(name=name, protocol=protocol, secret_bits=int(secret_bits))


def _connect(
    host: str,
    port: int,
    *,
    context: ssl.SSLContext,
    timeout: float,
) -> tuple[dict[str, Any], bytes | None, CipherRaw | None, str | None]:
    with socket.create_connection((host, port), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=host) as sslobj:
            cert_dict = sslobj.getpeercert()
            der_cert = sslobj.getpeercert(binary_form=True)
            negotiated = sslobj.version()
            cipher = _cipher_from_tuple(sslobj.cipher())
            return cert_dict, der_cert, cipher, negotiated


def _probe_protocol(
    host: str,
    port: int,
    version_label: str,
    min_ver: ssl.TLSVersion,
    max_ver: ssl.TLSVersion,
    timeout: float,
) -> ProtocolProbeRaw:
    context = _create_context(min_version=min_ver, max_version=max_ver)
    try:
        _, _, _, negotiated = _connect(host, port, context=context, timeout=timeout)
        return ProtocolProbeRaw(version=version_label, accepted=True, negotiated=negotiated)
    except Exception as exc:
        return ProtocolProbeRaw(version=version_label, accepted=False, error=str(exc))


def _collect_sync(host: str, port: int, timeout: float) -> SslRawResponse:
    context = _create_context(
        min_version=ssl.TLSVersion.MINIMUM_SUPPORTED,
        max_version=ssl.TLSVersion.MAXIMUM_SUPPORTED,
    )

    try:
        cert_dict, der_cert, negotiated_cipher, _ = _connect(host, port, context=context, timeout=timeout)
    except Exception as exc:
        return SslRawResponse(
            host=host,
            port=port,
            connection_error=str(exc),
            protocol_probes=[],
        )

    protocol_probes = [
        _probe_protocol(host, port, label, min_ver, max_ver, timeout)
        for label, min_ver, max_ver in _PROTOCOL_PROBES
    ]

    return SslRawResponse(
        host=host,
        port=port,
        certificate_b64=base64.b64encode(der_cert).decode("ascii") if der_cert else None,
        getpeercert=cert_dict or {},
        negotiated_cipher=negotiated_cipher,
        protocol_probes=protocol_probes,
    )


async def collect(asset: ScanTarget, options: ScanOptions) -> SslRawResponse:
    host, port = resolve_host_port(asset.identifier)
    return await asyncio.to_thread(_collect_sync, host, port, options.timeout)
