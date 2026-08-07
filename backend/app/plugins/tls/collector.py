from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.tls.cipher_probe import collect_sync, resolve_tls_target
from app.plugins.tls.schemas import TlsRawResponse


async def collect(asset: ScanTarget, options: ScanOptions) -> TlsRawResponse:
    host, port = resolve_tls_target(asset.identifier)
    try:
        result = await collect_sync(host, port, options.timeout)
    except Exception as exc:
        return TlsRawResponse(host=host, port=port, connection_error=str(exc))

    return TlsRawResponse(
        host=result["host"],
        port=result["port"],
        negotiated_cipher=result.get("negotiated_cipher"),
        accepted_ciphers=result.get("accepted_ciphers", []),
        weak_ciphers_accepted=result.get("weak_ciphers_accepted", []),
        protocol_probes=[probe.model_dump(mode="python") for probe in result.get("protocol_probes", [])],
    )
