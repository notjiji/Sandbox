import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.deps import require_permission
from app.core.permissions import Permission
from app.core.responses import success_response
from app.models.organization_member import OrganizationMember
from app.schemas.asset import CreateAssetRequest, UpdateAssetRequest
from app.services import asset as asset_service

router = APIRouter()


@router.get("")
def list_assets(
    _membership: OrganizationMember = Depends(require_permission(Permission.ASSET_READ)),
) -> JSONResponse:
    result = asset_service.list_assets()
    return success_response(data=result.model_dump(mode="json"))


@router.post("", status_code=201)
def create_asset(
    body: CreateAssetRequest,
    _membership: OrganizationMember = Depends(require_permission(Permission.ASSET_CREATE)),
) -> JSONResponse:
    asset_service.create_asset(body=body)
    return success_response(data={})


@router.get("/{asset_id}")
def get_asset(
    asset_id: uuid.UUID,
    _membership: OrganizationMember = Depends(require_permission(Permission.ASSET_READ)),
) -> JSONResponse:
    asset_service.get_asset(asset_id=str(asset_id))
    return success_response(data={})


@router.patch("/{asset_id}")
def update_asset(
    asset_id: uuid.UUID,
    body: UpdateAssetRequest,
    _membership: OrganizationMember = Depends(require_permission(Permission.ASSET_UPDATE)),
) -> JSONResponse:
    asset_service.update_asset(asset_id=str(asset_id), body=body)
    return success_response(data={})


@router.delete("/{asset_id}", status_code=200)
def delete_asset(
    asset_id: uuid.UUID,
    _membership: OrganizationMember = Depends(require_permission(Permission.ASSET_DELETE)),
) -> JSONResponse:
    asset_service.delete_asset(asset_id=str(asset_id))
    return success_response(data={"message": "Asset deleted successfully"})
