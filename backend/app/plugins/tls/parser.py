from app.plugins.ssl.utils import is_weak_cipher_name
from app.plugins.tls.schemas import TlsParsedData, TlsRawResponse

_LEGACY_PROTOCOLS = {"TLSv1.0", "TLSv1.1"}


def parse(raw: TlsRawResponse) -> TlsParsedData:
    legacy: list[str] = []
    min_version: str | None = None
    for probe in raw.protocol_probes:
        version = probe.get("version")
        if probe.get("accepted") and version:
            if version in _LEGACY_PROTOCOLS:
                legacy.append(version)
            if min_version is None or _protocol_rank(version) < _protocol_rank(min_version):
                min_version = version

    negotiated = raw.negotiated_cipher
    return TlsParsedData(
        host=raw.host,
        port=raw.port,
        min_version=min_version,
        negotiated_cipher=negotiated,
        cipher_count=len(raw.accepted_ciphers),
        weak_cipher=bool(negotiated and is_weak_cipher_name(negotiated)),
        weak_ciphers_accepted=raw.weak_ciphers_accepted,
        legacy_protocols_accepted=legacy,
    )


def _protocol_rank(version: str) -> int:
    order = {"TLSv1.0": 0, "TLSv1.1": 1, "TLSv1.2": 2, "TLSv1.3": 3}
    return order.get(version, 99)
