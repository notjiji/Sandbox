"""Coordinates scan lifecycle: load plugins → run → record status → normalize → persist."""

import asyncio
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.assets.adapter import asset_adapter
from app.core.logging import get_logger
from app.core.risk_engine.engine import risk_engine
from app.core.scan_engine.dispatcher import ScanDispatcher
from app.core.scan_engine.normalizer import ScanNormalizer
from app.core.scan_engine.result_combiner import combine_normalized_findings, resolve_scan_status
from app.core.scan_engine.types import CombinedScanResults, PluginExecutionRecord
from app.findings.enums import FindingStatus
from app.findings.repositories.finding_repository import create_finding
from app.plugins.base.contracts import ScanResult, ScanResultStatus
from app.plugins.base.loader import plugin_loader
from app.plugins.base.plugin import ScanTarget, ScannerPlugin
from app.scans.enums import PluginRunStatus, ScanStatus
from app.scans.models import Scan, ScanPluginRun
from app.scans.repositories.scan_plugin_repository import (
    complete_plugin_run,
    create_plugin_run,
)
from app.scans.repositories.scan_repository import update_scan_status

logger = get_logger("sandbox.scan_engine")


@dataclass(frozen=True)
class _PluginWorkItem:
    target: ScanTarget
    plugin: ScannerPlugin
    plugin_run: ScanPluginRun


class ScanOrchestrator:
    """Entry point for running scans through the engine pipeline."""

    def __init__(self) -> None:
        self._loader = plugin_loader
        self._dispatcher = ScanDispatcher()
        self._normalizer = ScanNormalizer()

    def execute(
        self,
        db: Session,
        *,
        scan: Scan,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> Scan:
        selection = self._loader.select_for_scan(scan)

        if not selection.enabled:
            update_scan_status(db, scan, status=ScanStatus.FAILED)
            return scan

        try:
            normalized_asset = asset_adapter.adapt(db, project_id=project_id, asset_id=asset_id)
            targets = asset_adapter.to_plugin_targets(normalized_asset)
        except Exception:
            logger.exception(
                "failed to adapt asset for scan",
                extra={"scan_id": str(scan.id), "asset_id": str(asset_id)},
            )
            update_scan_status(db, scan, status=ScanStatus.FAILED)
            return scan

        work_items = self._prepare_work_items(db, scan=scan, targets=targets, plugins=selection.enabled)
        outputs = asyncio.run(self._run_plugins_parallel(work_items))
        records = [
            self._finalize_plugin_run(db, item, output)
            for item, output in zip(work_items, outputs, strict=True)
        ]

        combined = self._combine_results(records)
        self._persist_findings(db, scan=scan, combined=combined)

        final_status = resolve_scan_status(records)
        update_scan_status(db, scan, status=final_status)
        logger.info(
            "scan orchestration finished",
            extra={
                "scan_id": str(scan.id),
                "status": final_status.value,
                "findings": combined.total_findings,
                "completed_plugins": combined.completed_plugins,
                "failed_plugins": combined.failed_plugins,
                "parallel_plugins": len(work_items),
            },
        )
        return scan

    def _prepare_work_items(
        self,
        db: Session,
        *,
        scan: Scan,
        targets: list[ScanTarget],
        plugins: list[ScannerPlugin],
    ) -> list[_PluginWorkItem]:
        items: list[_PluginWorkItem] = []
        for target in targets:
            for plugin in plugins:
                if not plugin.supports_asset(target.asset_type):
                    continue
                plugin_run = create_plugin_run(
                    db,
                    scan_id=scan.id,
                    asset_id=uuid.UUID(target.asset_id),
                    plugin_name=plugin.id,
                    status=PluginRunStatus.RUNNING,
                )
                items.append(_PluginWorkItem(target=target, plugin=plugin, plugin_run=plugin_run))
        return items

    async def _run_plugins_parallel(self, work_items: list[_PluginWorkItem]) -> list[ScanResult]:
        if not work_items:
            return []
        jobs = [(item.plugin, item.target) for item in work_items]
        return await self._dispatcher.dispatch_parallel(jobs)

    def _finalize_plugin_run(
        self,
        db: Session,
        item: _PluginWorkItem,
        output: ScanResult,
    ) -> PluginExecutionRecord:
        run_status = (
            PluginRunStatus.COMPLETED
            if output.status == ScanResultStatus.SUCCESS
            else PluginRunStatus.FAILED
        )

        if run_status == PluginRunStatus.FAILED:
            error_message = output.error or str(output.metadata.get("error", "Plugin returned failure"))
            complete_plugin_run(
                db,
                item.plugin_run,
                status=PluginRunStatus.FAILED,
                duration_seconds=output.duration,
                error_message=error_message,
                metadata=output.metadata or None,
            )
            return PluginExecutionRecord(
                plugin_name=item.plugin.id,
                target=item.target,
                status=PluginRunStatus.FAILED,
                output=output,
                error_message=error_message,
                duration=output.duration,
            )

        normalized_findings = self._normalizer.normalize_output(output)
        complete_plugin_run(
            db,
            item.plugin_run,
            status=PluginRunStatus.COMPLETED,
            findings_count=len(normalized_findings),
            duration_seconds=output.duration,
            metadata=output.metadata or None,
        )
        return PluginExecutionRecord(
            plugin_name=item.plugin.id,
            target=item.target,
            status=PluginRunStatus.COMPLETED,
            output=output,
            normalized_findings=normalized_findings,
            duration=output.duration,
        )

    def _combine_results(self, records: list[PluginExecutionRecord]) -> CombinedScanResults:
        findings = combine_normalized_findings(records)
        return CombinedScanResults(findings=findings, plugin_records=records)

    def _persist_findings(
        self,
        db: Session,
        *,
        scan: Scan,
        combined: CombinedScanResults,
    ) -> None:
        for record in combined.plugin_records:
            if record.status != PluginRunStatus.COMPLETED:
                continue
            asset_id = uuid.UUID(record.target.asset_id)
            for finding in record.normalized_findings:
                resolved = risk_engine.resolve_finding(db, plugin_finding=finding)
                if resolved is None:
                    continue
                create_finding(
                    db,
                    project_id=scan.project_id,
                    scan_id=scan.id,
                    asset_id=asset_id,
                    plugin=finding.plugin,
                    finding_code=resolved.finding_code,
                    check_status=resolved.check_status,
                    title=resolved.title,
                    description=resolved.description,
                    severity=resolved.severity,
                    risk_score=resolved.risk_score,
                    recommendation_id=resolved.recommendation_id,
                    status=FindingStatus.OPEN,
                    evidence=resolved.evidence,
                    recommendation=resolved.recommendation_text or finding.recommendation,
                    references=resolved.references or finding.reference_links,
                    category=resolved.category or finding.category,
                    raw_data=resolved.raw_data,
                    confidence=resolved.confidence if resolved.confidence is not None else finding.confidence,
                    cvss=resolved.cvss if resolved.cvss is not None else finding.cvss,
                    cwe=resolved.cwe or finding.cwe,
                    cve=resolved.cve or finding.cve,
                    detected_at=resolved.detected_at,
                )


scan_orchestrator = ScanOrchestrator()
