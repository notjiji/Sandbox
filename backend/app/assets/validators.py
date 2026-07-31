import uuid

from app.assets.enums import AssetType, CHILD_ASSET_TYPES, CHILD_PARENT_MAP, ROOT_ASSET_TYPES
from app.assets.schemas import CreateAssetRequest, UpdateAssetRequest
from app.core.exceptions import ValidationAppError
from app.projects.validators import require_active_project

__all__ = [
    "require_active_project",
    "validate_create_payload",
    "validate_hierarchy",
    "validate_parent_type",
    "validate_update_payload",
]


def validate_update_payload(body: UpdateAssetRequest) -> None:
    if body.model_dump(exclude_none=True) == {}:
        raise ValidationAppError("At least one field must be provided")


def validate_create_payload(body: CreateAssetRequest) -> None:
    if not body.name.strip():
        raise ValidationAppError("Asset name is required")
    validate_hierarchy(body.type, body.parent_id)


def validate_hierarchy(asset_type: AssetType, parent_id: str | None) -> None:
    if asset_type in ROOT_ASSET_TYPES:
        if parent_id:
            raise ValidationAppError(f"{asset_type.value} assets cannot have a parent")
        return

    if asset_type in CHILD_ASSET_TYPES:
        if not parent_id:
            raise ValidationAppError(f"{asset_type.value} assets require a parent asset")
        return

    raise ValidationAppError(f"Unsupported asset type: {asset_type.value}")


def validate_parent_type(child_type: AssetType, parent_type: AssetType) -> None:
    expected = CHILD_PARENT_MAP.get(child_type)
    if expected is None:
        raise ValidationAppError(f"{child_type.value} does not support a parent asset")
    if parent_type != expected:
        raise ValidationAppError(
            f"{child_type.value} assets must belong to a {expected.value.replace('_', ' ')}"
        )


def parse_parent_id(parent_id: str | None) -> uuid.UUID | None:
    if not parent_id:
        return None
    try:
        return uuid.UUID(parent_id)
    except ValueError as exc:
        raise ValidationAppError("Invalid parent_id") from exc
