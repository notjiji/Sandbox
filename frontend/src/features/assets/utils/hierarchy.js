import { CHILD_ASSET_TYPES } from "../types";

/**
 * Reorder a flat asset page so parents appear immediately before their children.
 * Falls back to the API order when no parent/child pairs overlap on the page.
 */
export function orderAssetsHierarchically(assets) {
  if (!assets?.length) return [];

  const byId = new Map(assets.map((asset) => [asset.id, asset]));
  const roots = assets.filter((asset) => !asset.parent_id);
  const ordered = [];
  const seen = new Set();

  const appendWithChildren = (asset) => {
    if (seen.has(asset.id)) return;
    seen.add(asset.id);
    ordered.push(asset);
    assets
      .filter((child) => child.parent_id === asset.id)
      .forEach(appendWithChildren);
  };

  roots.forEach(appendWithChildren);
  assets.forEach((asset) => {
    if (!seen.has(asset.id)) ordered.push(asset);
  });

  return ordered;
}

export function isChildAsset(asset) {
  return Boolean(asset?.parent_id);
}

export function canUseTreeView(filters = {}) {
  return !filters.search?.trim() && !CHILD_ASSET_TYPES.includes(filters.type);
}

export function buildTreeDisplayRows(roots, expandedIds, childrenByParentId, loadingChildren) {
  const rows = [];

  roots.forEach((root) => {
    rows.push({ kind: "asset", asset: root, depth: 0 });

    if (root.children_count <= 0 || !expandedIds.has(root.id)) {
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

export function getParentLabel(asset, assetsById) {
  if (asset.parent_name) return asset.parent_name;
  if (asset.parent_id && assetsById?.has(asset.parent_id)) {
    return assetsById.get(asset.parent_id).name;
  }
  return null;
}
