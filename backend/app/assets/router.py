import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.assets.enums import AssetCriticality, AssetEnvironment, AssetStatus, AssetType
from app.assets.permissions import ASSET_CREATE, ASSET_DELETE, ASSET_READ, ASSET_UPDATE
from app.assets.schemas import AssetListQuery, CreateAssetRequest, UpdateAssetRequest
from app.assets.services import asset_service
from app.core.database import get_db
from app.core.responses import success_response
from app.members.models import OrganizationMember
from app.scans.asset_router import router as asset_scans_router

router = APIRouter()

router.include_router(asset_scans_router, prefix="/{asset_id}/scans", tags=["scans"])


@router.get("")
def list_assets(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: AssetStatus | None = None,
    asset_type: AssetType | None = Query(None, alias="type"),
    criticality: AssetCriticality | None = None,
    environment: AssetEnvironment | None = None,
    search: str | None = Query(None, max_length=255),
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(ASSET_READ)),
) -> JSONResponse:
    result = asset_service.list_for_project(
        db,
        membership,
        project_id=project_id,
        query=AssetListQuery(
            page=page,
            limit=limit,
            status=status,
            type=asset_type,
            criticality=criticality,
            environment=environment,
            search=search,
        ),
    )
    return success_response(data=result.model_dump(mode="json"))


@router.post("", status_code=201)
def create_asset(
    project_id: uuid.UUID,
    body: CreateAssetRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(ASSET_CREATE)),
) -> JSONResponse:
    asset = asset_service.create_project_asset(db, membership, project_id=project_id, body=body)
    return success_response(data=asset.model_dump(mode="json"), status_code=201)


@router.get("/{asset_id}")
def get_asset(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(ASSET_READ)),
) -> JSONResponse:
    asset = asset_service.get_project_asset(
        db, membership, project_id=project_id, asset_id=asset_id
    )
    return success_response(data=asset.model_dump(mode="json"))


@router.put("/{asset_id}")
def update_asset(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    body: UpdateAssetRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(ASSET_UPDATE)),
) -> JSONResponse:
    asset = asset_service.update_project_asset(
        db, membership, project_id=project_id, asset_id=asset_id, body=body
    )
    return success_response(data=asset.model_dump(mode="json"))


@router.patch("/{asset_id}/archive")
def archive_asset(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(ASSET_UPDATE)),
) -> JSONResponse:
    asset = asset_service.archive_project_asset(
        db, membership, project_id=project_id, asset_id=asset_id
    )
    return success_response(data=asset.model_dump(mode="json"))


@router.patch("/{asset_id}/restore")
def restore_asset(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(ASSET_UPDATE)),
) -> JSONResponse:
    asset = asset_service.restore_project_asset(
        db, membership, project_id=project_id, asset_id=asset_id
    )
    return success_response(data=asset.model_dump(mode="json"))


@router.delete("/{asset_id}", status_code=200)
def delete_asset(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(ASSET_DELETE)),
) -> JSONResponse:
    asset_service.delete_project_asset(
        db, membership, project_id=project_id, asset_id=asset_id
    )
    return success_response(data={"message": "Asset deleted successfully"})
