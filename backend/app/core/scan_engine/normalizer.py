"""Normalizes and validates standard plugin output."""

from app.plugins.base.contracts import ScanFinding, ScanResult


class ScanNormalizer:
    def normalize_output(self, output: ScanResult) -> list[ScanFinding]:
        normalized: list[ScanFinding] = []
        for item in output.findings:
            finding = item if isinstance(item, ScanFinding) else ScanFinding.model_validate(item)
            if finding.plugin != output.plugin:
                finding = finding.model_copy(update={"plugin": output.plugin})
            normalized.append(finding)
        return normalized

    def normalize_findings(self, *, plugin_name: str, raw_findings: list) -> list[dict]:
        findings = [
            item
            if isinstance(item, ScanFinding)
            else ScanFinding.model_validate({**item, "plugin": plugin_name})
            for item in raw_findings
        ]
        return [finding.model_dump(mode="json") for finding in findings]
