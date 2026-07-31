"""Coordinates scan lifecycle: validate → dispatch → normalize → persist."""

import uuid

from sqlalchemy.orm import Session

from app.assets.service import asset_service
from app.core.logging import get_logger
from app.core.scan_engine.dispatcher import ScanDispatcher
from app.core.scan_engine.normalizer import ScanNormalizer
from app.core.scan_engine.plugin_loader import PluginLoader
from app.core.scan_engine.plugin_map import SCAN_TYPE_PLUGINS
from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.repositories.finding_repository import create_finding
from app.plugins.base import ScanTarget
from app.scans.enums import ScanStatus
from app.scans.models import Scan
from app.scans.repositories.scan_repository import update_scan_status

logger = get_logger("sandbox.scan_engine")


class ScanOrchestrator:
    """Entry point for running scans through the engine pipeline."""

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
        plugin_names = SCAN_TYPE_PLUGINS.get(scan.scan_type, [])
        if not plugin_names:
            update_scan_status(db, scan, status=ScanStatus.FAILED)
            return scan

        self._loader.load_all()
        targets = asset_service.resolve_plugin_targets(
            db, project_id=project_id, asset_id=asset_id
        )

        try:
            for target in targets:
                self._run_plugins_for_target(
                    db,
                    scan=scan,
                    asset_id=uuid.UUID(target.asset_id),
                    target=target,
                    plugin_names=plugin_names,
                )
            update_scan_status(db, scan, status=ScanStatus.COMPLETED)
        except Exception:
            logger.exception("scan orchestration failed", extra={"scan_id": str(scan.id)})
            update_scan_status(db, scan, status=ScanStatus.FAILED)
            raise

        return scan

    def _run_plugins_for_target(
        self,
        db: Session,
        *,
        scan: Scan,
        asset_id: uuid.UUID,
        target: ScanTarget,
        plugin_names: list[str],
    ) -> None:
        for plugin_name in plugin_names:
            result = self._dispatcher.dispatch(plugin_name=plugin_name, target=target)
            if not result.success:
                logger.warning(
                    "plugin scan failed",
                    extra={"plugin": plugin_name, "scan_id": str(scan.id), "asset_id": target.asset_id},
                )
                continue

            findings = self._normalizer.normalize_findings(
                plugin_name=plugin_name,
                raw_findings=result.findings,
            )
            for finding in findings:
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
