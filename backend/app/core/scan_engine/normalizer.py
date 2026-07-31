"""Normalizes raw plugin output into finding records."""

from app.findings.enums import FindingSeverity


class ScanNormalizer:
    def normalize_findings(self, *, plugin_name: str, raw_findings: list[dict]) -> list[dict]:
        normalized: list[dict] = []
        for item in raw_findings:
            severity = str(item.get("severity", "info")).lower()
            if severity not in {s.value for s in FindingSeverity}:
                severity = FindingSeverity.INFO.value
            normalized.append(
                {
                    "title": item.get("title") or f"{plugin_name} finding",
                    "description": item.get("description"),
                    "severity": severity,
                }
            )
        return normalized
