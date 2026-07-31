from app.assets.schemas import CreateAssetRequest, UpdateAssetRequest
from app.core.exceptions import ValidationAppError
from app.projects.validators import require_active_project

__all__ = ["require_active_project", "validate_create_payload", "validate_update_payload"]


def validate_update_payload(body: UpdateAssetRequest) -> None:
    if body.model_dump(exclude_none=True) == {}:
        raise ValidationAppError("At least one field must be provided")


def validate_create_payload(body: CreateAssetRequest) -> None:
    if not body.name.strip():
        raise ValidationAppError("Asset name is required")
