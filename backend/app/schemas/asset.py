from pydantic import Field

from app.schemas.base import BaseSchema


class AssetSummary(BaseSchema):
    id: str
    name: str
    type: str
    status: str


class AssetListResponse(BaseSchema):
    items: list[AssetSummary]
    total: int


class CreateAssetRequest(BaseSchema):
    name: str = Field(min_length=1, max_length=255)
    type: str = Field(default="host", min_length=1, max_length=64)


class UpdateAssetRequest(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    type: str | None = Field(default=None, min_length=1, max_length=64)
