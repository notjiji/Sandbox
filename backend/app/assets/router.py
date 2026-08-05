import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.assets.enums import AssetCategory, AssetCriticality, AssetEnvironment, AssetStatus, AssetType
from app.assets.permissions import ASSET_CREATE, ASSET_DELETE, ASSET_READ, ASSET_UPDATE
from app.assets.services.relationship_service import asset_relationship_service
from app.assets.services.overview_service import get_asset_overview
from app.assets.services.risk_history_service import get_asset_risk_history
from app.assets.services.timeline_service import get_asset_timeline
from app.assets.services import (
    archive_project_asset,
    create_project_asset,
    delete_project_asset,
    get_project_asset,
    list_asset_audit_history,
    list_project_asset_children,
    list_project_assets,
    restore_project_asset,
    update_project_asset,
)
from app.assets.schemas import AssetListQuery, CreateAssetLinkRequest, CreateAssetRequest, UpdateAssetRequest
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
    asset_category: AssetCategory | None = None,
    search: str | None = Query(None, max_length=255),
    roots_only: bool = Query(False),
    parent_id: str | None = None,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(ASSET_READ)),
) -> JSONResponse:
    result = list_project_assets(
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
            asset_category=asset_category,
            search=search,
            roots_only=roots_only,
            parent_id=parent_id,
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
    asset = create_project_asset(db, membership, project_id=project_id, body=body)
    return success_response(data=asset.model_dump(mode="json"), status_code=201)


@router.get("/{asset_id}/children")
def list_asset_children(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    status: AssetStatus | None = None,
    asset_type: AssetType | None = Query(None, alias="type"),
    criticality: AssetCriticality | None = None,
    environment: AssetEnvironment | None = None,
    asset_category: AssetCategory | None = None,
    search: str | None = Query(None, max_length=255),
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(ASSET_READ)),
) -> JSONResponse:
    result = list_project_asset_children(
        db,
        membership,
        project_id=project_id,
        parent_id=asset_id,
        query=AssetListQuery(
            status=status,
            type=asset_type,
            criticality=criticality,
            environment=environment,
            asset_category=asset_category,
            search=search,
        ),
    )
    return success_response(data=result.model_dump(mode="json"))


@router.get("/{asset_id}/risk-history")
def get_asset_risk_history_route(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    limit: int = Query(20, ge=2, le=50),
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(ASSET_READ)),
) -> JSONResponse:
    result = get_asset_risk_history(
        db,
        membership,
        project_id=project_id,
        asset_id=asset_id,
        limit=limit,
    )
    return success_response(data=result.model_dump(mode="json"))


@router.get("/{asset_id}/timeline")
def get_asset_timeline_route(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(ASSET_READ)),
) -> JSONResponse:
    result = get_asset_timeline(
        db,
        membership,
        project_id=project_id,
        asset_id=asset_id,
        limit=limit,
    )
    return success_response(data=result.model_dump(mode="json"))


@router.get("/{asset_id}/overview")
def get_asset_overview_route(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(ASSET_READ)),
) -> JSONResponse:
    result = get_asset_overview(
        db,
        membership,
        project_id=project_id,
        asset_id=asset_id,
    )
    return success_response(data=result.model_dump(mode="json"))


@router.get("/{asset_id}/relationships")
def get_asset_relationships(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(ASSET_READ)),
) -> JSONResponse:
    result = asset_relationship_service.get_relationships(
        db,
        membership,
        project_id=project_id,
        asset_id=asset_id,
    )
    return success_response(data=result.model_dump(mode="json"))


@router.post("/{asset_id}/links", status_code=201)
def create_asset_link(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    body: CreateAssetLinkRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(ASSET_UPDATE)),
) -> JSONResponse:
    link = asset_relationship_service.create_link(
        db,
        membership,
        project_id=project_id,
        asset_id=asset_id,
        body=body,
    )
    return success_response(data=link.model_dump(mode="json"), status_code=201)


@router.delete("/{asset_id}/links/{link_id}", status_code=200)
def delete_asset_link(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    link_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(ASSET_UPDATE)),
) -> JSONResponse:
    asset_relationship_service.delete_link(
        db,
        membership,
        project_id=project_id,
        asset_id=asset_id,
        link_id=link_id,
    )
    return success_response(data={"message": "Asset link removed"})


@router.get("/{asset_id}/audit-history")
def list_asset_audit_history(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(ASSET_READ)),
) -> JSONResponse:
    result = list_asset_audit_history(
        db, membership, project_id=project_id, asset_id=asset_id
    )
    return success_response(data=result.model_dump(mode="json"))


@router.get("/{asset_id}")
def get_asset(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(ASSET_READ)),
) -> JSONResponse:
    asset = get_project_asset(
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
    asset = update_project_asset(
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
    asset = archive_project_asset(
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
    asset = restore_project_asset(
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
    delete_project_asset(
        db, membership, project_id=project_id, asset_id=asset_id
    )
    return success_response(data={"message": "Asset deleted successfully"})
