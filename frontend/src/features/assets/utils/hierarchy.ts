import type { AssetSummary } from "@/shared/types/asset";
import { CHILD_ASSET_TYPES } from "../types";

export interface AssetFiltersState {
  search: string;
  type: string;
  status: string;
  environment: string;
  criticality: string;
  asset_category: string;
}

export type TreeDisplayRow =
  | { kind: "asset"; asset: AssetSummary; depth: number }
  | { kind: "loading"; parentId: string; depth: number }
  | { kind: "empty"; parentId: string; depth: number };

/**
 * Reorder a flat asset page so parents appear immediately before their children.
 * Falls back to the API order when no parent/child pairs overlap on the page.
 */
export function orderAssetsHierarchically(assets: AssetSummary[]): AssetSummary[] {
  if (!assets.length) return [];

  const seen = new Set<string>();
  const ordered: AssetSummary[] = [];
  const roots = assets.filter((asset) => !asset.parent_id);

  const appendWithChildren = (asset: AssetSummary): void => {
    if (seen.has(asset.id)) return;
    seen.add(asset.id);
    ordered.push(asset);
    assets.filter((child) => child.parent_id === asset.id).forEach(appendWithChildren);
  };

  roots.forEach(appendWithChildren);
  assets.forEach((asset) => {
    if (!seen.has(asset.id)) ordered.push(asset);
  });

  return ordered;
}

export function isChildAsset(asset: AssetSummary | null | undefined): boolean {
  return Boolean(asset?.parent_id);
}

export function canUseTreeView(filters: AssetFiltersState = { search: "", type: "", status: "", environment: "", criticality: "", asset_category: "" }): boolean {
  return !filters.search.trim() && !CHILD_ASSET_TYPES.includes(filters.type as (typeof CHILD_ASSET_TYPES)[number]);
}

export function buildTreeDisplayRows(
  roots: AssetSummary[],
  expandedIds: Set<string>,
  childrenByParentId: Record<string, AssetSummary[]>,
  loadingChildren: Record<string, boolean>,
): TreeDisplayRow[] {
  const rows: TreeDisplayRow[] = [];

  roots.forEach((root) => {
    rows.push({ kind: "asset", asset: root, depth: 0 });

    if ((root.children_count ?? 0) <= 0 || !expandedIds.has(root.id)) {
      return;
    }

    if (loadingChildren[root.id]) {
      rows.push({ kind: "loading", parentId: root.id, depth: 1 });
      return;
    }

    const children = childrenByParentId[root.id];
    if (!children) return;

    if (children.length === 0) {
      rows.push({ kind: "empty", parentId: root.id, depth: 1 });
      return;
    }

    children.forEach((child) => {
      rows.push({ kind: "asset", asset: child, depth: 1 });
    });
  });

  return rows;
}

export function getParentLabel(
  asset: AssetSummary,
  assetsById: Map<string, AssetSummary>,
): string | null {
  if (asset.parent_name) return asset.parent_name;
  if (asset.parent_id && assetsById.has(asset.parent_id)) {
    return assetsById.get(asset.parent_id)?.name ?? null;
  }
  return null;
}
