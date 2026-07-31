from pydantic import Field

from app.assets.enums import (
    AssetCriticality,
    AssetEnvironment,
    AssetStatus,
    AssetType,
)
from app.schemas.base import BaseSchema


class AssetSummary(BaseSchema):
    id: str
    organization_id: str
    project_id: str
    parent_id: str | None = None
    name: str
    description: str | None = None
    type: AssetType
    status: AssetStatus
    environment: AssetEnvironment
    criticality: AssetCriticality
    owner: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    created_by: str | None = None
    children_count: int = 0


class AssetListResponse(BaseSchema):
    items: list[AssetSummary]
    total: int
    page: int
    limit: int


class AssetListQuery(BaseSchema):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    status: AssetStatus | None = None
    type: AssetType | None = None
    criticality: AssetCriticality | None = None
    environment: AssetEnvironment | None = None
    search: str | None = Field(default=None, max_length=255)


class CreateAssetRequest(BaseSchema):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    type: AssetType = AssetType.WEBSITE
    status: AssetStatus = AssetStatus.PENDING
    environment: AssetEnvironment = AssetEnvironment.PRODUCTION
    criticality: AssetCriticality = AssetCriticality.MEDIUM
    owner: str | None = Field(default=None, max_length=255)
    metadata: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    allow_private_ip: bool = Field(
        default=False,
        description="Allow private/reserved IPv4 addresses for public_ip assets",
    )
    parent_id: str | None = Field(
        default=None,
        description=(
            "Required for child asset types: public_ip (website), "
            "email_domain (domain), s3_bucket (cloud_account)"
        ),
    )


class UpdateAssetRequest(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    type: AssetType | None = None
    status: AssetStatus | None = None
    environment: AssetEnvironment | None = None
    criticality: AssetCriticality | None = None
    owner: str | None = Field(default=None, max_length=255)
    metadata: dict[str, str] | None = None
    tags: list[str] | None = None
    allow_private_ip: bool | None = Field(
        default=None,
        description="Allow private/reserved IPv4 addresses for public_ip assets",
    )
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
    environment: AssetEnvironment
    criticality: AssetCriticality
    metadata: dict = Field(default_factory=dict)
    related_targets: list[RelatedScanTarget] = Field(default_factory=list)
