from app.findings.enums import FindingSeverity
from app.plugins.base.contracts import FindingCheckStatus, ScanFinding, scan_finding
from app.plugins.base.plugin import ScanTarget
from app.plugins.ports.schemas import PortsParsedData

_PORT_RULES = {
    21: ("PORT_FTP_OPEN", "FTP Port Open", FindingSeverity.MEDIUM, "Disable FTP or use SFTP instead."),
    23: ("PORT_TELNET_OPEN", "Telnet Port Open", FindingSeverity.CRITICAL, "Disable Telnet and use SSH instead."),
    445: ("PORT_SMB_OPEN", "SMB Port Open", FindingSeverity.HIGH, "Restrict SMB to trusted networks."),
    3389: ("PORT_RDP_OPEN", "RDP Port Open", FindingSeverity.HIGH, "Restrict RDP and enforce MFA/VPN access."),
}


def evaluate_rules(parsed: PortsParsedData, asset: ScanTarget, *, plugin_id: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    for port in parsed.dangerous_ports:
        rule_id, title, severity, recommendation = _PORT_RULES.get(
            port,
            (f"PORT_{port}_OPEN", f"Port {port} Open", FindingSeverity.MEDIUM, "Review and close unnecessary ports."),
        )
        findings.append(
            scan_finding(
                plugin=plugin_id,
                rule_id=rule_id,
                asset_id=asset.asset_id,
                title=title,
                category="network",
                evidence=f"TCP port {port} is open",
                recommendation=recommendation,
                severity=severity,
                status=FindingCheckStatus.FAILED,
            )
        )
    return findings
