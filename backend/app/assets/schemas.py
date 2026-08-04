from datetime import datetime

from pydantic import Field

from app.assets.enums import (
    AssetCategory,
    AssetCriticality,
    AssetEnvironment,
    AssetLinkType,
    AssetStatus,
    AssetType,
)
from app.scans.enums import ScanStatus
from app.shared.schemas.base import BaseSchema


class AssetActorSummary(BaseSchema):
    id: str | None = None
    name: str | None = None
    email: str | None = None


class AssetSummary(BaseSchema):
    id: str
    organization_id: str
    organization_name: str | None = None
    project_id: str
    project_name: str | None = None
    parent_id: str | None = None
    parent_name: str | None = None

    name: str
    type: AssetType
    description: str | None = None
    external_identifier: str | None = None

    criticality: AssetCriticality
    business_unit: str | None = None
    environment: AssetEnvironment
    owner: str | None = None
    asset_category: AssetCategory | None = None

    status: AssetStatus
    metadata: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    children_count: int = 0

    current_risk_score: float | None = None
    security_grade: str | None = None
    last_scan_at: datetime | None = None
    last_successful_scan_at: datetime | None = None
    last_scan_status: ScanStatus | str | None = None
    findings_count: int = 0
    critical_findings_count: int = 0

    created_at: datetime | None = None
    updated_at: datetime | None = None
    archived_at: datetime | None = None
    archived_by: AssetActorSummary | None = None
    created_by: AssetActorSummary | None = None
    last_modified_by: AssetActorSummary | None = None


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
    asset_category: AssetCategory | None = None
    search: str | None = Field(default=None, max_length=255)
    roots_only: bool = Field(
        default=False,
        description="When true, paginate only root assets (parent_id is null)",
    )
    parent_id: str | None = Field(
        default=None,
        description="Return direct children of the given parent asset",
    )


class AssetChildrenResponse(BaseSchema):
    items: list[AssetSummary]
    total: int


class CreateAssetRequest(BaseSchema):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    type: AssetType = AssetType.WEBSITE
    status: AssetStatus = AssetStatus.PENDING
    environment: AssetEnvironment = AssetEnvironment.PRODUCTION
    criticality: AssetCriticality = AssetCriticality.MEDIUM
    owner: str | None = Field(default=None, max_length=255)
    external_identifier: str | None = Field(default=None, max_length=512)
    business_unit: str | None = Field(default=None, max_length=128)
    asset_category: AssetCategory | None = None
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
    external_identifier: str | None = Field(default=None, max_length=512)
    business_unit: str | None = Field(default=None, max_length=128)
    asset_category: AssetCategory | None = None
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


class NormalizedScanTarget(BaseSchema):
    """Normalized scan target — asset-type agnostic view consumed by the Scan Engine."""

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


ScanTargetContext = NormalizedScanTarget


class AssetLinkSummary(BaseSchema):
    id: str
    link_type: AssetLinkType
    label: str | None = None
    direction: str
    asset: AssetSummary


class AssetGraphNode(BaseSchema):
    id: str
    name: str
    type: AssetType
    external_identifier: str | None = None
    is_current: bool = False
    depth: int = 0


class AssetGraphEdge(BaseSchema):
    source: str
    target: str
    kind: str
    link_type: AssetLinkType | None = None
    label: str | None = None


class AssetRelationshipGraph(BaseSchema):
    nodes: list[AssetGraphNode]
    edges: list[AssetGraphEdge]


class AssetRelationshipsResponse(BaseSchema):
    parent: AssetSummary | None = None
    ancestors: list[AssetSummary] = Field(default_factory=list)
    children: list[AssetSummary] = Field(default_factory=list)
    links: list[AssetLinkSummary] = Field(default_factory=list)
    graph: AssetRelationshipGraph
    descendants_count: int = 0


class CreateAssetLinkRequest(BaseSchema):
    target_asset_id: str
    link_type: AssetLinkType = AssetLinkType.RELATED
    label: str | None = Field(default=None, max_length=255)

