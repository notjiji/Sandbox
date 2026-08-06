"""Convert raw TLS data into structured objects."""

from app.plugins.ssl.cert_parser import hostname_matches_certificate, parse_certificate_b64
from app.plugins.ssl.schemas import ParsedCipher, SslParsedData, SslRawResponse

_FORWARD_SECRECY_PREFIXES = ("ECDHE", "DHE", "TLS_AES_", "TLS_CHACHA20_")


def _key_exchange_from_cipher(name: str) -> str | None:
    upper = name.upper()
    for token in ("ECDHE", "DHE", "RSA", "ECDH", "PSK"):
        if token in upper:
            return token
    return None


def _forward_secrecy_from_cipher(name: str) -> bool:
    upper = name.upper()
    return any(upper.startswith(prefix) or prefix in upper for prefix in _FORWARD_SECRECY_PREFIXES)


def _protocols_from_probes(raw: SslRawResponse) -> tuple[list[str], list[str]]:
    all_versions = [probe.version for probe in raw.protocol_probes]
    accepted = [probe.version for probe in raw.protocol_probes if probe.accepted]
    return all_versions, accepted


def parse(raw: SslRawResponse) -> SslParsedData:
    certificate = parse_certificate_b64(raw.certificate_b64, hostname=raw.host)
    hostname_matches = hostname_matches_certificate(raw.host, certificate)

    cipher: ParsedCipher | None = None
    if raw.negotiated_cipher is not None:
        cipher = ParsedCipher(
            name=raw.negotiated_cipher.name,
            protocol=raw.negotiated_cipher.protocol,
            secret_bits=raw.negotiated_cipher.secret_bits,
            key_exchange=_key_exchange_from_cipher(raw.negotiated_cipher.name),
            forward_secrecy=_forward_secrecy_from_cipher(raw.negotiated_cipher.name),
        )

    _, accepted = _protocols_from_probes(raw)

    return SslParsedData(
        host=raw.host,
        port=raw.port,
        protocols=accepted,
        protocols_accepted=accepted,
        certificate=certificate,
        cipher=cipher,
        hostname_matches=hostname_matches,
    )
