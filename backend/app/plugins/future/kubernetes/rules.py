from app.findings.enums import FindingSeverity
from app.plugins.base.contracts import FindingCheckStatus, ScanFinding, scan_finding
from app.plugins.base.plugin import ScanTarget
from app.plugins.future.kubernetes.schemas import KubernetesParsedData


def evaluate_rules(parsed: KubernetesParsedData, asset: ScanTarget, *, plugin_id: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    for pod in parsed.privileged_pods:
        findings.append(
            scan_finding(
                plugin=plugin_id,
                rule_id="K8S_PRIVILEGED_POD",
                asset_id=asset.asset_id,
                title="Privileged Pod Detected",
                category="kubernetes",
                evidence=f"Pod {pod.name} runs with privileged: true",
                recommendation="Run pods with least privilege and drop unnecessary capabilities.",
                severity=FindingSeverity.HIGH,
                status=FindingCheckStatus.FAILED,
            )
        )
    return findings
