"""Collect raw TLS/certificate data — no findings."""

from __future__ import annotations

import asyncio
import base64
import socket
import ssl
from typing import Any

import certifi

from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.ssl.legacy_probe import merge_protocol_probes, probe_protocols_openssl
from app.plugins.ssl.ocsp import probe_ocsp_stapling
from app.plugins.ssl.ct import analyze_ct_issuers
from app.plugins.ssl.schemas import CipherRaw, ProtocolProbeRaw, SslRawResponse
from app.plugins.ssl.utils import resolve_host_port

_PROTOCOL_PROBES: list[tuple[str, ssl.TLSVersion, ssl.TLSVersion]] = [
    ("TLSv1.0", ssl.TLSVersion.TLSv1, ssl.TLSVersion.TLSv1),
    ("TLSv1.1", ssl.TLSVersion.TLSv1_1, ssl.TLSVersion.TLSv1_1),
    ("TLSv1.2", ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_2),
    ("TLSv1.3", ssl.TLSVersion.TLSv1_3, ssl.TLSVersion.TLSv1_3),
]

_WEAK_CIPHERS = (
    "DES-CBC3-SHA",
    "RC4-SHA",
    "RC4-MD5",
    "NULL-SHA",
    "ECDHE-RSA-AES128-SHA",
    "AES128-SHA",
    "AES256-SHA",
)


def _create_context(*, min_version: ssl.TLSVersion, max_version: ssl.TLSVersion, verify: bool = False) -> ssl.SSLContext:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    if verify:
        context.load_verify_locations(cafile=certifi.where())
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
    else:
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
    host: str, port: int, version_label: str, min_ver: ssl.TLSVersion, max_ver: ssl.TLSVersion, timeout: float
) -> ProtocolProbeRaw:
    context = _create_context(min_version=min_ver, max_version=max_ver)
    try:
        _, _, _, negotiated = _connect(host, port, context=context, timeout=timeout)
        return ProtocolProbeRaw(version=version_label, accepted=True, negotiated=negotiated)
    except Exception as exc:
        return ProtocolProbeRaw(version=version_label, accepted=False, error=str(exc))


def _probe_trusted_chain(host: str, port: int, timeout: float) -> bool:
    context = _create_context(
        min_version=ssl.TLSVersion.MINIMUM_SUPPORTED,
        max_version=ssl.TLSVersion.MAXIMUM_SUPPORTED,
        verify=True,
    )
    try:
        _connect(host, port, context=context, timeout=timeout)
        return True
    except Exception:
        return False


def _probe_weak_ciphers(host: str, port: int, timeout: float) -> list[str]:
    accepted: list[str] = []
    for cipher in _WEAK_CIPHERS:
        context = _create_context(
            min_version=ssl.TLSVersion.TLSv1_2,
            max_version=ssl.TLSVersion.TLSv1_2,
        )
        try:
            context.set_ciphers(cipher)
            _, _, negotiated, _ = _connect(host, port, context=context, timeout=timeout)
            if negotiated:
                accepted.append(negotiated.name)
        except Exception:
            continue
    return list(dict.fromkeys(accepted))


def _format_x509_name(field) -> str | None:
    if not field:
        return None
    parts: list[str] = []
    for item in field:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            parts.append(f"{item[0]}={item[1]}")
    return ", ".join(parts) if parts else None


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

    stdlib_probes = [
        _probe_protocol(host, port, label, min_ver, max_ver, timeout)
        for label, min_ver, max_ver in _PROTOCOL_PROBES
    ]
    openssl_probes = probe_protocols_openssl(host, port, timeout)
    protocol_probes = merge_protocol_probes(stdlib_probes, openssl_probes)

    live_issuer = _format_x509_name(cert_dict.get("issuer") if cert_dict else None)
    ct_issuers, suspicious_ct_issuers = analyze_ct_issuers(host, live_issuer)

    return SslRawResponse(
        host=host,
        port=port,
        certificate_b64=base64.b64encode(der_cert).decode("ascii") if der_cert else None,
        getpeercert=cert_dict or {},
        negotiated_cipher=negotiated_cipher,
        protocol_probes=protocol_probes,
        chain_trusted=_probe_trusted_chain(host, port, timeout),
        ocsp_stapling=probe_ocsp_stapling(host, port, timeout),
        weak_ciphers_accepted=_probe_weak_ciphers(host, port, timeout),
        ct_issuers=ct_issuers,
        suspicious_ct_issuers=suspicious_ct_issuers,
    )


async def collect(asset: ScanTarget, options: ScanOptions) -> SslRawResponse:
    host, port = resolve_host_port(asset.identifier)
    return await asyncio.to_thread(_collect_sync, host, port, options.timeout)
