"""Normalizes and validates standard plugin output."""

from app.plugins.base.output import PluginFinding, PluginOutput


class ScanNormalizer:
    def normalize_output(self, output: PluginOutput) -> list[PluginFinding]:
        """Validate findings from a plugin output — plugins must already use PluginFinding shape."""
        normalized: list[PluginFinding] = []
        for item in output.findings:
            finding = item if isinstance(item, PluginFinding) else PluginFinding.model_validate(item)
            if finding.plugin != output.plugin:
                finding = finding.model_copy(update={"plugin": output.plugin})
            normalized.append(finding)
        return normalized

    def normalize_findings(self, *, plugin_name: str, raw_findings: list) -> list[dict]:
        """Backward-compatible dict output for legacy callers."""
        findings = [
            item if isinstance(item, PluginFinding) else PluginFinding.model_validate({**item, "plugin": plugin_name})
            for item in raw_findings
        ]
        return [finding.model_dump(mode="json") for finding in findings]
