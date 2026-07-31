from pydantic import Field

from app.models.asset import AssetStatus, AssetType
from app.schemas.base import BaseSchema


class AssetSummary(BaseSchema):
    id: str
    project_id: str
    name: str
    identifier: str | None = None
    type: AssetType
    status: AssetStatus
    created_by: str | None = None


class AssetListResponse(BaseSchema):
    items: list[AssetSummary]
    total: int


class CreateAssetRequest(BaseSchema):
    name: str = Field(min_length=1, max_length=255)
    identifier: str | None = Field(default=None, max_length=512)
    type: AssetType = AssetType.HOST


class UpdateAssetRequest(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    identifier: str | None = Field(default=None, max_length=512)
    type: AssetType | None = None
    status: AssetStatus | None = None
