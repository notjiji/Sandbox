import uuid

from app.assets.enums import (
    ALLOWED_PARENT_TYPES,
    AssetStatus,
    AssetType,
    OPTIONAL_PARENT_TYPES,
    PURE_ROOT_TYPES,
    REQUIRED_PARENT_TYPES,
)
from app.assets.schemas import CreateAssetRequest, UpdateAssetRequest
from app.assets.models import Asset
from app.assets.type_validators import validate_asset_metadata
from app.core.exceptions import ValidationAppError
from app.projects.validators import require_active_project

__all__ = [
    "require_active_project",
    "validate_archivable",
    "validate_asset_metadata_for_update",
    "validate_asset_scannable",
    "validate_create_payload",
    "validate_hierarchy",
    "validate_parent_type",
    "validate_restorable",
    "validate_updatable",
    "validate_update_payload",
]


def validate_update_payload(body: UpdateAssetRequest) -> None:
    if body.model_dump(exclude_none=True) == {}:
        raise ValidationAppError("At least one field must be provided")
    if body.status == AssetStatus.DELETED:
        raise ValidationAppError("Use DELETE to remove an asset; status cannot be set to deleted")
    if body.status == AssetStatus.ARCHIVED:
        raise ValidationAppError("Use PATCH /archive to archive an asset; status cannot be set to archived")


def validate_create_payload(body: CreateAssetRequest) -> None:
    if not body.name.strip():
        raise ValidationAppError("Asset name is required")
    if body.status == AssetStatus.DELETED:
        raise ValidationAppError("New assets cannot be created with deleted status")
    if body.status == AssetStatus.ARCHIVED:
        raise ValidationAppError("New assets cannot be created with archived status")
    validate_hierarchy(body.type, body.parent_id)
    validate_asset_metadata(body.type, body.metadata, allow_private=body.allow_private_ip)


def validate_asset_metadata_for_update(
    body: UpdateAssetRequest,
    *,
    asset_type: AssetType,
    existing_metadata: dict[str, str],
) -> None:
    if body.metadata is None and body.type is None:
        return

    next_type = body.type or asset_type
    merged = {**existing_metadata, **(body.metadata or {})}
    allow_private = bool(body.allow_private_ip)
    validate_asset_metadata(next_type, merged, allow_private=allow_private)


def validate_hierarchy(asset_type: AssetType, parent_id: str | None) -> None:
    if asset_type in PURE_ROOT_TYPES:
        if parent_id:
            raise ValidationAppError(f"{asset_type.value} assets cannot have a parent")
        return

    if asset_type in REQUIRED_PARENT_TYPES:
        if not parent_id:
            raise ValidationAppError(f"{asset_type.value} assets require a parent asset")
        return

    if asset_type in OPTIONAL_PARENT_TYPES:
        if parent_id:
            return
        return

    if parent_id:
        raise ValidationAppError(f"{asset_type.value} assets cannot have a parent")


def validate_parent_type(child_type: AssetType, parent_type: AssetType) -> None:
    allowed = ALLOWED_PARENT_TYPES.get(child_type)
    if allowed is None:
        raise ValidationAppError(f"{child_type.value} does not support a parent asset")
    if parent_type not in allowed:
        allowed_labels = ", ".join(sorted(t.value.replace("_", " ") for t in allowed))
        raise ValidationAppError(
            f"{child_type.value} assets must belong to one of: {allowed_labels}"
        )


def validate_asset_scannable(asset: Asset) -> None:
    if asset.status != AssetStatus.ACTIVE:
        raise ValidationAppError("Only active assets can be scanned")


def validate_archivable(asset: Asset) -> None:
    if asset.deleted_at is not None:
        raise ValidationAppError("Deleted assets cannot be archived")
    if asset.status == AssetStatus.ARCHIVED:
        raise ValidationAppError("Asset is already archived")


def validate_restorable(asset: Asset) -> None:
    if asset.status not in {AssetStatus.ARCHIVED, AssetStatus.DELETED}:
        raise ValidationAppError("Only archived or deleted assets can be restored")


def validate_updatable(asset: Asset) -> None:
    if asset.deleted_at is not None or asset.status == AssetStatus.DELETED:
        raise ValidationAppError("Deleted assets cannot be updated; restore the asset first")


def parse_parent_id(parent_id: str | None) -> uuid.UUID | None:
    if not parent_id:
        return None
    try:
        return uuid.UUID(parent_id)
    except ValueError as exc:
        raise ValidationAppError("Invalid parent_id") from exc
