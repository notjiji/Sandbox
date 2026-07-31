import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.models.organization_member import OrganizationMember
from app.schemas.asset import CreateAssetRequest, UpdateAssetRequest
from app.services import asset as asset_service

router = APIRouter()


@router.get("")
def list_assets(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.ASSET_READ)),
) -> JSONResponse:
    result = asset_service.list_project_assets(
        db, membership, project_id=project_id
    )
    return success_response(data=result.model_dump(mode="json"))


@router.post("", status_code=201)
def create_asset(
    project_id: uuid.UUID,
    body: CreateAssetRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.ASSET_CREATE)),
) -> JSONResponse:
    asset = asset_service.create_project_asset(
        db, membership, project_id=project_id, body=body
    )
    return success_response(data=asset.model_dump(mode="json"), status_code=201)


@router.get("/{asset_id}")
def get_asset(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.ASSET_READ)),
) -> JSONResponse:
    asset = asset_service.get_project_asset(
        db, membership, project_id=project_id, asset_id=asset_id
    )
    return success_response(data=asset.model_dump(mode="json"))


@router.patch("/{asset_id}")
def update_asset(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    body: UpdateAssetRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.ASSET_UPDATE)),
) -> JSONResponse:
    asset = asset_service.update_project_asset(
        db, membership, project_id=project_id, asset_id=asset_id, body=body
    )
    return success_response(data=asset.model_dump(mode="json"))


@router.delete("/{asset_id}", status_code=200)
def delete_asset(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.ASSET_DELETE)),
) -> JSONResponse:
    asset_service.delete_project_asset(
        db, membership, project_id=project_id, asset_id=asset_id
    )
    return success_response(data={"message": "Asset deleted successfully"})
