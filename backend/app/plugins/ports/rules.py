"""Independent port exposure rules."""

from collections.abc import Callable

from app.findings.enums import FindingSeverity
from app.plugins.base.contracts import FindingCheckStatus, ScanFinding, scan_finding
from app.plugins.base.plugin import ScanTarget
from app.plugins.ports.schemas import DetectedService, PortsParsedData

RuleFn = Callable[[PortsParsedData, ScanTarget, str], ScanFinding | None]


def _service_evidence(service: DetectedService) -> str:
    parts = [f"TCP/{service.port} open"]
    if service.product:
        parts.append(service.product)
    if service.version:
        parts.append(service.version)
    if service.banner and not service.product:
        parts.append(service.banner[:120])
    return " — ".join(parts)


def rule_ftp_open(parsed: PortsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    service = parsed.service_on_port(21)
    if service is None:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="PORT_FTP_OPEN", asset_id=asset.asset_id,
        title="FTP Port Open", category="network",
        evidence=_service_evidence(service),
        recommendation="Disable FTP or replace with SFTP/FTPS.",
        severity=FindingSeverity.MEDIUM, status=FindingCheckStatus.FAILED,
    )


def rule_telnet_open(parsed: PortsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    service = parsed.service_on_port(23)
    if service is None:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="PORT_TELNET_OPEN", asset_id=asset.asset_id,
        title="Telnet Port Open", category="network",
        evidence=_service_evidence(service),
        recommendation="Disable Telnet and use SSH instead.",
        severity=FindingSeverity.CRITICAL, status=FindingCheckStatus.FAILED,
    )


def rule_rdp_exposed(parsed: PortsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    service = parsed.service_on_port(3389)
    if service is None:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="PORT_RDP_EXPOSED", asset_id=asset.asset_id,
        title="RDP Exposed", category="network",
        evidence=_service_evidence(service),
        recommendation="Restrict RDP to VPN or bastion hosts and enforce MFA.",
        severity=FindingSeverity.HIGH, status=FindingCheckStatus.FAILED,
    )


def rule_mysql_public(parsed: PortsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    service = parsed.service_on_port(3306)
    if service is None:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="PORT_MYSQL_PUBLIC", asset_id=asset.asset_id,
        title="MySQL Publicly Exposed", category="network",
        evidence=_service_evidence(service),
        recommendation="Bind MySQL to private interfaces and require VPN/firewall restrictions.",
        severity=FindingSeverity.HIGH, status=FindingCheckStatus.FAILED,
    )


def rule_redis_public(parsed: PortsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    service = parsed.service_on_port(6379)
    if service is None:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="PORT_REDIS_PUBLIC", asset_id=asset.asset_id,
        title="Redis Publicly Exposed", category="network",
        evidence=_service_evidence(service),
        recommendation="Do not expose Redis to the public internet; require auth and network ACLs.",
        severity=FindingSeverity.HIGH, status=FindingCheckStatus.FAILED,
    )


def rule_mongodb_public(parsed: PortsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    service = parsed.service_on_port(27017)
    if service is None:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="PORT_MONGODB_PUBLIC", asset_id=asset.asset_id,
        title="MongoDB Publicly Exposed", category="network",
        evidence=_service_evidence(service),
        recommendation="Restrict MongoDB to private networks and enable authentication.",
        severity=FindingSeverity.HIGH, status=FindingCheckStatus.FAILED,
    )


RULES: list[RuleFn] = [
    rule_ftp_open,
    rule_telnet_open,
    rule_rdp_exposed,
    rule_mysql_public,
    rule_redis_public,
    rule_mongodb_public,
]


def evaluate_rules(parsed: PortsParsedData, asset: ScanTarget, *, plugin_id: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    for rule in RULES:
        finding = rule(parsed, asset, plugin_id)
        if finding is not None:
            findings.append(finding)
    return findings
