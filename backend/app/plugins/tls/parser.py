from app.plugins.tls.schemas import TlsParsedData, TlsRawResponse

_WEAK_CIPHERS = {"ECDHE-RSA-AES128-SHA", "RC4-SHA", "DES-CBC3-SHA"}


def parse(raw: TlsRawResponse) -> TlsParsedData:
    return TlsParsedData(
        min_version=raw.min_version,
        negotiated_cipher=raw.negotiated_cipher,
        cipher_count=raw.cipher_count,
        weak_cipher=raw.negotiated_cipher in _WEAK_CIPHERS,
    )
