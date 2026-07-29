from app.core.exceptions import NotImplementedFeatureError
from app.schemas.asset import AssetListResponse, CreateAssetRequest, UpdateAssetRequest


def list_assets() -> AssetListResponse:
    return AssetListResponse(items=[], total=0)


def create_asset(*, body: CreateAssetRequest) -> None:
    raise NotImplementedFeatureError("Asset creation")


def get_asset(*, asset_id: str) -> None:
    raise NotImplementedFeatureError("Asset retrieval")


def update_asset(*, asset_id: str, body: UpdateAssetRequest) -> None:
    raise NotImplementedFeatureError("Asset updates")


def delete_asset(*, asset_id: str) -> None:
    raise NotImplementedFeatureError("Asset deletion")
