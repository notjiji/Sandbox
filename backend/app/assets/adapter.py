"""Asset Adapter — converts database assets into normalized scan targets.

Database Asset → Asset Adapter → NormalizedScanTarget → Scan Orchestrator → Plugins

This module is the only place that loads ORM ``Asset`` models for scanning.
The scan engine and plugins receive normalized objects and never touch the database layer.
"""

import uuid

from sqlalchemy.orm import Session

from app.assets.enums import PARENT_ASSET_TYPES
from app.assets.metadata import build_asset_metadata, metadata_to_dict, resolve_primary_value
from app.assets.repositories.asset_repository import get_asset_by_id, list_child_assets
from app.assets.schemas import NormalizedScanTarget, RelatedScanTarget
from app.assets.validators import validate_asset_scannable
from app.core.exceptions import NotFoundError
from app.plugins.base import ScanTarget


class AssetAdapter:
    """Translates persisted assets into scan-engine targets."""

    def adapt(
        self,
        db: Session,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> NormalizedScanTarget:
        """Load an asset from the database and produce a normalized scan target."""
        asset = get_asset_by_id(db, project_id=project_id, asset_id=asset_id)
        if not asset:
            raise NotFoundError("Asset")
        validate_asset_scannable(asset)

        children = (
            list_child_assets(db, parent_id=asset.id)
            if asset.type in PARENT_ASSET_TYPES
            else []
        )
        metadata = metadata_to_dict(asset.metadata_entries)
        child_metadata = {
            str(child.id): metadata_to_dict(child.metadata_entries) for child in children
        }
        scan_metadata = build_asset_metadata(
            asset,
            metadata=metadata,
            children=children,
            child_metadata=child_metadata,
        )
        related = [
            RelatedScanTarget(
                asset_id=str(child.id),
                identifier=resolve_primary_value(child, child_metadata[str(child.id)]),
                asset_type=child.type,
            )
            for child in children
        ]

        return NormalizedScanTarget(
            asset_id=str(asset.id),
            project_id=str(asset.project_id),
            name=asset.name,
            identifier=resolve_primary_value(asset, metadata),
            asset_type=asset.type,
            parent_id=str(asset.parent_id) if asset.parent_id else None,
            environment=asset.environment,
            criticality=asset.criticality,
            metadata=scan_metadata,
            related_targets=related,
        )

    def to_plugin_targets(self, normalized: NormalizedScanTarget) -> list[ScanTarget]:
        """Flatten a normalized target into plugin-facing scan targets."""
        targets = [
            ScanTarget(
                asset_id=normalized.asset_id,
                identifier=normalized.identifier,
                asset_type=normalized.asset_type.value,
            )
        ]
        for related in normalized.related_targets:
            targets.append(
                ScanTarget(
                    asset_id=related.asset_id,
                    identifier=related.identifier,
                    asset_type=related.asset_type.value,
                )
            )
        return targets

    def resolve_targets(
        self,
        db: Session,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> list[ScanTarget]:
        """Convenience: adapt an asset and return plugin scan targets."""
        return self.to_plugin_targets(
            self.adapt(db, project_id=project_id, asset_id=asset_id)
        )


asset_adapter = AssetAdapter()
