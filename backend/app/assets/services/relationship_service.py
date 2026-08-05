"""Asset relationship graph — parent/child hierarchy and peer links."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.assets.enums import AssetLinkType
from app.assets.events import AssetAuditAction
from app.assets.metadata import metadata_to_dict, resolve_external_identifier
from app.assets.models import Asset
from app.assets.repositories.asset_repository import (
    get_asset_by_id,
    list_child_assets,
)
from app.assets.repositories.link_repository import (
    create_link,
    delete_link,
    get_link_by_id,
    list_links_for_asset,
)
from app.assets.schemas import (
    AssetGraphEdge,
    AssetGraphNode,
    AssetLinkSummary,
    AssetRelationshipGraph,
    AssetRelationshipsResponse,
    AssetSummary,
    CreateAssetLinkRequest,
)
from app.assets.services.asset_service import AssetService
from app.audit.service import record_audit_event
from app.core.exceptions import NotFoundError, ValidationAppError
from app.members.models import OrganizationMember

_asset_service = AssetService()
MAX_GRAPH_DEPTH = 6


def _summaries_map(db: Session, assets: list[Asset]) -> dict[str, AssetSummary]:
    unique = {asset.id: asset for asset in assets if asset}
    if not unique:
        return {}
    summaries = _asset_service._summaries_for_assets(db, list(unique.values()))
    return {summary.id: summary for summary in summaries}


def _summary_from_map(
    asset: Asset | None,
    summaries: dict[str, AssetSummary],
    *,
    db: Session,
) -> AssetSummary | None:
    if not asset:
        return None
    cached = summaries.get(str(asset.id))
    if cached:
        return cached
    return _asset_service.summary_for_asset(db, asset)


def _collect_related_assets(
    *,
    parent: Asset | None,
    ancestors: list[Asset],
    children: list[Asset],
    outbound_links,
    inbound_links,
) -> list[Asset]:
    related: list[Asset] = []
    if parent:
        related.append(parent)
    related.extend(ancestors)
    related.extend(children)
    for link in outbound_links:
        related.append(link.target_asset)
    for link in inbound_links:
        related.append(link.source_asset)
    return related


def _collect_ancestors(db: Session, asset: Asset) -> list[Asset]:
    chain: list[Asset] = []
    current_id = asset.parent_id
    visited: set[uuid.UUID] = {asset.id}
    while current_id and len(chain) < MAX_GRAPH_DEPTH:
        if current_id in visited:
            break
        parent = get_asset_by_id(
            db,
            project_id=asset.project_id,
            asset_id=current_id,
            include_deleted=True,
        )
        if not parent:
            break
        visited.add(parent.id)
        chain.insert(0, parent)
        current_id = parent.parent_id
    return chain


def _count_descendants(db: Session, *, root_id: uuid.UUID, depth: int = MAX_GRAPH_DEPTH) -> int:
    if depth <= 0:
        return 0
    children = list_child_assets(db, parent_id=root_id)
    total = len(children)
    for child in children:
        total += _count_descendants(db, root_id=child.id, depth=depth - 1)
    return total


def _build_graph(
    *,
    current: Asset,
    ancestors: list[Asset],
    children: list[Asset],
    outbound_links,
    inbound_links,
) -> AssetRelationshipGraph:
    nodes: dict[str, AssetGraphNode] = {}
    edges: list[AssetGraphEdge] = []
    seen_edges: set[tuple[str, str, str]] = set()

    def add_node(asset: Asset, *, depth: int, is_current: bool = False) -> None:
        node_id = str(asset.id)
        if node_id in nodes:
            if is_current:
                nodes[node_id].is_current = True
            return
        metadata = metadata_to_dict(asset.metadata_entries)
        nodes[node_id] = AssetGraphNode(
            id=node_id,
            name=asset.name,
            type=asset.type,
            external_identifier=asset.external_identifier
            or resolve_external_identifier(asset.type, metadata, fallback_name=asset.name),
            is_current=is_current,
            depth=depth,
        )

    def add_edge(source: str, target: str, *, kind: str, link_type=None, label=None) -> None:
        key = (source, target, kind if kind != "link" else f"link:{link_type}")
        if key in seen_edges:
            return
        seen_edges.add(key)
        edges.append(
            AssetGraphEdge(
                source=source,
                target=target,
                kind=kind,
                link_type=link_type,
                label=label,
            )
        )

    for index, ancestor in enumerate(ancestors):
        add_node(ancestor, depth=index)
        next_id = str(ancestors[index + 1].id) if index + 1 < len(ancestors) else str(current.id)
        add_edge(str(ancestor.id), next_id, kind="parent")

    add_node(current, depth=len(ancestors), is_current=True)

    for child in children:
        add_node(child, depth=len(ancestors) + 1)
        add_edge(str(current.id), str(child.id), kind="parent")

    for link in outbound_links:
        target = link.target_asset
        add_node(target, depth=len(ancestors) + 1)
        add_edge(
            str(current.id),
            str(target.id),
            kind="link",
            link_type=link.link_type,
            label=link.label,
        )

    for link in inbound_links:
        source = link.source_asset
        add_node(source, depth=max(len(ancestors) - 1, 0))
        add_edge(
            str(source.id),
            str(current.id),
            kind="link",
            link_type=link.link_type,
            label=link.label,
        )

    ordered_nodes = sorted(nodes.values(), key=lambda node: (node.depth, node.name.lower()))
    return AssetRelationshipGraph(nodes=ordered_nodes, edges=edges)


class AssetRelationshipService:
    def get_relationships(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> AssetRelationshipsResponse:
        asset = get_asset_by_id(db, project_id=project_id, asset_id=asset_id, include_deleted=True)
        if not asset:
            raise NotFoundError("Asset")

        ancestors = _collect_ancestors(db, asset)
        parent = asset.parent
        children = list_child_assets(db, parent_id=asset.id)
        outbound, inbound = list_links_for_asset(db, asset_id=asset.id)

        related_assets = _collect_related_assets(
            parent=parent,
            ancestors=ancestors,
            children=children,
            outbound_links=outbound,
            inbound_links=inbound,
        )
        summaries = _summaries_map(db, related_assets)

        parent_summary = _summary_from_map(parent, summaries, db=db)
        ancestor_summaries = [
            summary
            for item in ancestors
            if (summary := _summary_from_map(item, summaries, db=db))
        ]
        child_summaries = [
            summary
            for item in children
            if (summary := _summary_from_map(item, summaries, db=db))
        ]

        link_summaries: list[AssetLinkSummary] = []
        for link in outbound:
            target_summary = _summary_from_map(link.target_asset, summaries, db=db)
            if not target_summary:
                continue
            link_summaries.append(
                AssetLinkSummary(
                    id=str(link.id),
                    link_type=link.link_type,
                    label=link.label,
                    direction="outbound",
                    asset=target_summary,
                )
            )
        for link in inbound:
            source_summary = _summary_from_map(link.source_asset, summaries, db=db)
            if not source_summary:
                continue
            link_summaries.append(
                AssetLinkSummary(
                    id=str(link.id),
                    link_type=link.link_type,
                    label=link.label,
                    direction="inbound",
                    asset=source_summary,
                )
            )

        graph = _build_graph(
            current=asset,
            ancestors=ancestors,
            children=children,
            outbound_links=outbound,
            inbound_links=inbound,
        )

        return AssetRelationshipsResponse(
            parent=parent_summary,
            ancestors=ancestor_summaries,
            children=child_summaries,
            links=link_summaries,
            graph=graph,
            descendants_count=_count_descendants(db, root_id=asset.id),
        )

    def create_link(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
        body: CreateAssetLinkRequest,
    ) -> AssetLinkSummary:
        source = get_asset_by_id(db, project_id=project_id, asset_id=asset_id)
        if not source:
            raise NotFoundError("Asset")

        try:
            target_id = uuid.UUID(body.target_asset_id)
        except ValueError as exc:
            raise ValidationAppError("Invalid target_asset_id") from exc

        if target_id == asset_id:
            raise ValidationAppError("An asset cannot link to itself")

        target = get_asset_by_id(db, project_id=project_id, asset_id=target_id)
        if not target:
            raise NotFoundError("Target asset")

        link = create_link(
            db,
            organization_id=membership.organization_id,
            source_asset_id=asset_id,
            target_asset_id=target_id,
            link_type=body.link_type,
            label=body.label.strip() if body.label else None,
        )
        db.refresh(link)
        record_audit_event(
            db,
            action=AssetAuditAction.UPDATE,
            user_id=membership.user_id,
            organization_id=membership.organization_id,
            resource_type="asset",
            resource_id=asset_id,
            details={
                "link_action": "create",
                "target_asset_id": str(target_id),
                "link_type": body.link_type.value,
            },
        )
        db.commit()

        reloaded = get_link_by_id(
            db, link_id=link.id, organization_id=membership.organization_id
        )
        if not reloaded:
            raise NotFoundError("Asset link")

        outbound, _ = list_links_for_asset(db, asset_id=asset_id)
        created = next((item for item in outbound if item.id == link.id), reloaded)
        target_summary = _asset_service.summary_for_asset(db, target)
        return AssetLinkSummary(
            id=str(created.id),
            link_type=created.link_type,
            label=created.label,
            direction="outbound",
            asset=target_summary,
        )

    def delete_link(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
        link_id: uuid.UUID,
    ) -> None:
        asset = get_asset_by_id(db, project_id=project_id, asset_id=asset_id)
        if not asset:
            raise NotFoundError("Asset")

        link = get_link_by_id(db, link_id=link_id, organization_id=membership.organization_id)
        if not link or link.source_asset_id != asset_id:
            raise NotFoundError("Asset link")

        delete_link(db, link)
        record_audit_event(
            db,
            action=AssetAuditAction.UPDATE,
            user_id=membership.user_id,
            organization_id=membership.organization_id,
            resource_type="asset",
            resource_id=asset_id,
            details={"link_action": "delete", "link_id": str(link_id)},
        )
        db.commit()


asset_relationship_service = AssetRelationshipService()
