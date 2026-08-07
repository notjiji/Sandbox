"""Legacy TLS probing via OpenSSL CLI for accurate TLS 1.0/1.1 detection."""

from __future__ import annotations

import re
import shutil
import subprocess

from app.plugins.ssl.schemas import ProtocolProbeRaw

_OPENSSL_TLS_FLAGS = (
    ("TLSv1.0", "-tls1"),
    ("TLSv1.1", "-tls1_1"),
    ("TLSv1.2", "-tls1_2"),
    ("TLSv1.3", "-tls1_3"),
)


def probe_protocols_openssl(host: str, port: int, timeout: float) -> list[ProtocolProbeRaw] | None:
    openssl = shutil.which("openssl")
    if not openssl:
        return None

    probes: list[ProtocolProbeRaw] = []
    for version_label, flag in _OPENSSL_TLS_FLAGS:
        try:
            result = subprocess.run(
                [
                    openssl,
                    "s_client",
                    flag,
                    "-connect",
                    f"{host}:{port}",
                    "-servername",
                    host,
                ],
                input=b"",
                capture_output=True,
                timeout=timeout,
                check=False,
            )
            output = result.stdout.decode("utf-8", errors="replace")
            if "Cipher is (NONE)" in output or "connect:errno" in output.lower():
                probes.append(ProtocolProbeRaw(version=version_label, accepted=False, error="handshake failed"))
                continue
            negotiated = None
            match = re.search(r"Protocol\s*:\s*(TLSv[\d.]+)", output)
            if match:
                negotiated = match.group(1)
            probes.append(ProtocolProbeRaw(version=version_label, accepted=True, negotiated=negotiated))
        except Exception as exc:
            probes.append(ProtocolProbeRaw(version=version_label, accepted=False, error=str(exc)))
    return probes


def merge_protocol_probes(
    stdlib_probes: list[ProtocolProbeRaw],
    openssl_probes: list[ProtocolProbeRaw] | None,
) -> list[ProtocolProbeRaw]:
    if not openssl_probes:
        return stdlib_probes

    merged: dict[str, ProtocolProbeRaw] = {probe.version: probe for probe in stdlib_probes}
    for probe in openssl_probes:
        existing = merged.get(probe.version)
        if existing is None or (probe.accepted and not existing.accepted):
            merged[probe.version] = probe
    return [merged[key] for key in ("TLSv1.0", "TLSv1.1", "TLSv1.2", "TLSv1.3") if key in merged]
