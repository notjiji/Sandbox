from app.plugins.ssl.legacy_probe import merge_protocol_probes
from app.plugins.ssl.schemas import ProtocolProbeRaw


def test_merge_protocol_probes_prefers_openssl_when_stdlib_rejects() -> None:
    stdlib = [
        ProtocolProbeRaw(version="TLSv1.0", accepted=False, error="disabled"),
        ProtocolProbeRaw(version="TLSv1.1", accepted=False, error="disabled"),
    ]
    openssl = [
        ProtocolProbeRaw(version="TLSv1.0", accepted=True, negotiated="TLSv1"),
        ProtocolProbeRaw(version="TLSv1.1", accepted=True, negotiated="TLSv1.1"),
    ]

    merged = merge_protocol_probes(stdlib, openssl)

    assert merged[0].accepted is True
    assert merged[1].accepted is True
