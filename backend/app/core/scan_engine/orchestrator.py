"""Coordinates scan lifecycle: load plugins → run → record status → normalize → persist."""

import uuid

from sqlalchemy.orm import Session

from app.assets.adapter import asset_adapter
from app.core.logging import get_logger
from app.core.scan_engine.dispatcher import ScanDispatcher
from app.core.scan_engine.normalizer import ScanNormalizer
from app.core.scan_engine.plugin_loader import PluginLoader
from app.core.scan_engine.plugin_map import SCAN_TYPE_PLUGINS
from app.core.scan_engine.result_combiner import combine_normalized_findings, resolve_scan_status
from app.core.scan_engine.types import CombinedScanResults, PluginExecutionRecord
from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.repositories.finding_repository import create_finding
from app.plugins.base import ScanTarget
from app.scans.enums import PluginRunStatus, ScanStatus
from app.scans.models import Scan
from app.scans.repositories.scan_plugin_repository import (
    complete_plugin_run,
    create_plugin_run,
)
from app.scans.repositories.scan_repository import update_scan_status

logger = get_logger("sandbox.scan_engine")


class ScanOrchestrator:
    """Entry point for running scans through the engine pipeline.

    Responsibilities:
    - Load enabled plugins for the scan type
    - Pass normalized scan targets to each plugin
    - Run plugins and catch failures without aborting the whole scan
    - Persist per-plugin execution status
    - Combine normalized findings across plugins and targets
    - Delegate raw output normalization to ScanNormalizer
    """

    def __init__(self) -> None:
        self._loader = PluginLoader()
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
        configured_plugins = SCAN_TYPE_PLUGINS.get(scan.scan_type, [])
        plugin_set = self._loader.load_enabled(configured_plugins)

        if not plugin_set.enabled and not plugin_set.skipped:
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

        records: list[PluginExecutionRecord] = []

        primary_target = targets[0] if targets else None
        for plugin_name in plugin_set.skipped:
            if primary_target is not None:
                records.append(
                    self._record_skipped_plugin(
                        db,
                        scan=scan,
                        target=primary_target,
                        plugin_name=plugin_name,
                        reason="Plugin is disabled or not registered",
                    )
                )

        for target in targets:
            for plugin_name in plugin_set.enabled:
                records.append(
                    self._run_plugin(
                        db,
                        scan=scan,
                        target=target,
                        plugin_name=plugin_name,
                    )
                )

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
            },
        )
        return scan

    def _run_plugin(
        self,
        db: Session,
        *,
        scan: Scan,
        target: ScanTarget,
        plugin_name: str,
    ) -> PluginExecutionRecord:
        asset_id = uuid.UUID(target.asset_id)
        plugin_run = create_plugin_run(
            db,
            scan_id=scan.id,
            asset_id=asset_id,
            plugin_name=plugin_name,
            status=PluginRunStatus.RUNNING,
        )

        result = self._dispatcher.dispatch(plugin_name=plugin_name, target=target)
        if not result.success:
            error_message = str(result.metadata.get("error", "Plugin returned failure"))
            complete_plugin_run(
                db,
                plugin_run,
                status=PluginRunStatus.FAILED,
                error_message=error_message,
                metadata=result.metadata or None,
            )
            return PluginExecutionRecord(
                plugin_name=plugin_name,
                target=target,
                status=PluginRunStatus.FAILED,
                error_message=error_message,
                metadata=result.metadata,
            )

        normalized_findings = self._normalizer.normalize_findings(
            plugin_name=plugin_name,
            raw_findings=result.findings,
        )
        complete_plugin_run(
            db,
            plugin_run,
            status=PluginRunStatus.COMPLETED,
            findings_count=len(normalized_findings),
            metadata=result.metadata or None,
        )
        return PluginExecutionRecord(
            plugin_name=plugin_name,
            target=target,
            status=PluginRunStatus.COMPLETED,
            raw_findings=result.findings,
            normalized_findings=normalized_findings,
            metadata=result.metadata,
        )

    def _record_skipped_plugin(
        self,
        db: Session,
        *,
        scan: Scan,
        target: ScanTarget,
        plugin_name: str,
        reason: str,
    ) -> PluginExecutionRecord:
        plugin_run = create_plugin_run(
            db,
            scan_id=scan.id,
            asset_id=uuid.UUID(target.asset_id),
            plugin_name=plugin_name,
            status=PluginRunStatus.SKIPPED,
        )
        complete_plugin_run(
            db,
            plugin_run,
            status=PluginRunStatus.SKIPPED,
            error_message=reason,
        )
        return PluginExecutionRecord(
            plugin_name=plugin_name,
            target=target,
            status=PluginRunStatus.SKIPPED,
            error_message=reason,
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
                create_finding(
                    db,
                    project_id=scan.project_id,
                    scan_id=scan.id,
                    asset_id=asset_id,
                    title=finding["title"],
                    description=finding.get("description"),
                    severity=FindingSeverity(finding["severity"]),
                    status=FindingStatus.OPEN,
                )


scan_orchestrator = ScanOrchestrator()
