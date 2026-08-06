from app.findings.enums import FindingSeverity
from app.plugins.base.contracts import FindingCheckStatus, ScanFinding, scan_finding
from app.plugins.base.plugin import ScanTarget
from app.plugins.future.cve.schemas import CveParsedData


def evaluate_rules(parsed: CveParsedData, asset: ScanTarget, *, plugin_id: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    for package in parsed.vulnerable_packages:
        cve = package.cve_ids[0] if package.cve_ids else None
        findings.append(
            scan_finding(
                plugin=plugin_id,
                rule_id="CVE_KNOWN_VULNERABILITY",
                asset_id=asset.asset_id,
                title="Known CVE Detected",
                description="A package with a published CVE is installed on the asset.",
                category="vulnerability",
                evidence=f"{cve} affects installed package {package.name} {package.version}",
                recommendation="Upgrade the affected package to a patched version.",
                reference_links=["https://nvd.nist.gov/"],
                cve=cve,
                cvss=package.cvss,
                severity=FindingSeverity.HIGH,
                status=FindingCheckStatus.FAILED,
            )
        )
    return findings
