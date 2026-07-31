from pydantic import Field

from app.assets.enums import AssetType, AssetStatus
from app.schemas.base import BaseSchema


class AssetSummary(BaseSchema):
    id: str
    project_id: str
    parent_id: str | None = None
    name: str
    identifier: str | None = None
    type: AssetType
    status: AssetStatus
    created_by: str | None = None
    children_count: int = 0


class AssetListResponse(BaseSchema):
    items: list[AssetSummary]
    total: int


class CreateAssetRequest(BaseSchema):
    name: str = Field(min_length=1, max_length=255)
    identifier: str | None = Field(default=None, max_length=512)
    type: AssetType = AssetType.WEBSITE
    parent_id: str | None = Field(
        default=None,
        description=(
            "Required for child asset types: public_ip (website), "
            "email_domain (domain), s3_bucket (cloud_account)"
        ),
    )


class UpdateAssetRequest(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    identifier: str | None = Field(default=None, max_length=512)
    type: AssetType | None = None
    status: AssetStatus | None = None
    parent_id: str | None = None


class RelatedScanTarget(BaseSchema):
    asset_id: str
    identifier: str
    asset_type: AssetType


class ScanTargetContext(BaseSchema):
    """Scan-ready view of an asset — consumed by the Scan Engine."""

    asset_id: str
    project_id: str
    name: str
    identifier: str
    asset_type: AssetType
    parent_id: str | None = None
    metadata: dict = Field(default_factory=dict)
    related_targets: list[RelatedScanTarget] = Field(default_factory=list)
