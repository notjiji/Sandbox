import { Link } from "react-router-dom";
import { ChevronDown, ChevronRight, CornerDownRight } from "lucide-react";
import type { AssetSummary } from "@/shared/types/asset";
import AssetEmptyState from "./AssetEmptyState";
import {
  AssetCriticalityBadge,
  AssetEnvironmentBadge,
  AssetStatusBadge,
  AssetTypeBadge,
} from "./AssetBadges";
import { getPrimaryMetadataValue } from "../types";
import {
  buildTreeDisplayRows,
  getParentLabel,
  isChildAsset,
  orderAssetsHierarchically,
} from "../utils/hierarchy";
import { formatDateTime, formatRiskScore, UNAVAILABLE } from "../utils";

type ViewMode = "tree" | "flat";

interface ExpandButtonProps {
  expanded: boolean;
  disabled?: boolean;
  onClick: () => void;
  label: string;
}

function ExpandButton({ expanded, disabled, onClick, label }: ExpandButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="mr-2 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded text-brand-500 hover:bg-brand-800/40 hover:text-brand-200 disabled:opacity-40"
      aria-expanded={expanded}
      aria-label={label}
    >
      {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
    </button>
  );
}

interface AssetNameCellProps {
  asset: AssetSummary;
  projectId: string;
  parentLabel: string | null;
  depth?: number;
  mode: ViewMode;
  expanded: boolean;
  onToggleExpand: (assetId: string) => void;
}

function AssetNameCell({
  asset,
  projectId,
  parentLabel,
  depth = 0,
  mode,
  expanded,
  onToggleExpand,
}: AssetNameCellProps) {
  const primary = getPrimaryMetadataValue(asset);
  const child = isChildAsset(asset) || depth > 0;
  const canExpand = mode === "tree" && depth === 0 && (asset.children_count ?? 0) > 0;
  const indent = depth > 0 ? "pl-8" : canExpand ? undefined : "pl-8";

  return (
    <td className="px-4 py-3">
      <div className={`flex items-start ${indent ?? ""}`}>
        {canExpand ? (
          <ExpandButton
            expanded={expanded}
            onClick={() => onToggleExpand(asset.id)}
            label={`${expanded ? "Collapse" : "Expand"} children for ${asset.name}`}
          />
        ) : depth === 0 ? (
          <span className="mr-2 inline-block h-6 w-6 shrink-0" aria-hidden />
        ) : null}

        <div className="min-w-0 flex-1">
          {child && (
            <CornerDownRight size={14} className="mb-1 inline-block text-brand-600" aria-hidden />
          )}
          <Link
            to={`/projects/${projectId}/assets/${asset.id}`}
            className="link-glow font-medium text-brand-100"
          >
            {asset.name}
          </Link>
          {primary && <p className="mt-0.5 text-xs text-brand-500">{primary}</p>}
          {child && parentLabel && mode === "flat" && (
            <p className="mt-0.5 text-xs text-brand-600">
              Child of{" "}
              <Link
                to={`/projects/${projectId}/assets/${asset.parent_id}`}
                className="text-brand-400 hover:text-brand-200"
              >
                {parentLabel}
              </Link>
            </p>
          )}
          {mode === "tree" && depth === 0 && (asset.children_count ?? 0) > 0 && !expanded && (
            <p className="mt-0.5 text-xs text-brand-600">
              {asset.children_count} child{(asset.children_count ?? 0) === 1 ? "" : "ren"}
            </p>
          )}
        </div>
      </div>
    </td>
  );
}

interface AssetDataRowProps {
  asset: AssetSummary;
  projectId: string;
  projectName?: string;
  parentLabel: string | null;
  depth: number;
  mode: ViewMode;
  expanded: boolean;
  onToggleExpand: (assetId: string) => void;
  selected: boolean;
  onToggleSelect: (assetId: string) => void;
  selectable: boolean;
}

function AssetDataRow({
  asset,
  projectId,
  projectName,
  parentLabel,
  depth,
  mode,
  expanded,
  onToggleExpand,
  selected,
  onToggleSelect,
  selectable,
}: AssetDataRowProps) {
  const child = isChildAsset(asset) || depth > 0;

  return (
    <tr className={child ? "bg-brand-950/20 hover:bg-brand-900/30" : "hover:bg-brand-900/20"}>
      <td className="px-4 py-3">
        <input
          type="checkbox"
          checked={selected}
          disabled={!selectable}
          onChange={() => onToggleSelect(asset.id)}
          aria-label={`Select ${asset.name}`}
          className="rounded border-brand-700 bg-brand-950 text-brand-400"
        />
      </td>
      <td className="px-4 py-3">
        <AssetTypeBadge type={asset.type} />
      </td>
      <AssetNameCell
        asset={asset}
        projectId={projectId}
        parentLabel={parentLabel}
        depth={depth}
        mode={mode}
        expanded={expanded}
        onToggleExpand={onToggleExpand}
      />
      <td className="px-4 py-3 text-brand-300">{projectName ?? "—"}</td>
      <td className="px-4 py-3">
        <AssetCriticalityBadge criticality={asset.criticality} />
      </td>
      <td className="px-4 py-3">
        <AssetEnvironmentBadge environment={asset.environment} />
      </td>
      <td className="px-4 py-3">
        <AssetStatusBadge status={asset.status} />
      </td>
      <td className="px-4 py-3 text-brand-300">{asset.owner || "—"}</td>
      <td className="px-4 py-3 text-brand-300">
        {asset.last_scan_at ? formatDateTime(asset.last_scan_at) : UNAVAILABLE}
      </td>
      <td className="px-4 py-3 text-brand-300">
        {formatRiskScore(asset.current_risk_score ?? null)}
      </td>
    </tr>
  );
}

interface AssetTableProps {
  assets: AssetSummary[];
  projectId: string;
  projectName?: string;
  mode?: ViewMode;
  expandedIds?: Set<string>;
  childrenByParentId?: Record<string, AssetSummary[]>;
  loadingChildren?: Record<string, boolean>;
  onToggleExpand?: (assetId: string) => void;
  selectedIds?: string[];
  onToggleSelect?: (assetId: string) => void;
  onToggleSelectAll?: (assetIds: string[]) => void;
  hasActiveFilters?: boolean;
}

export default function AssetTable({
  assets,
  projectId,
  projectName,
  mode = "flat",
  expandedIds = new Set(),
  childrenByParentId = {},
  loadingChildren = {},
  onToggleExpand = () => {},
  selectedIds = [],
  onToggleSelect = () => {},
  onToggleSelectAll = () => {},
  hasActiveFilters = false,
}: AssetTableProps) {
  if (assets.length === 0) {
    return (
      <AssetEmptyState projectId={projectId} filtered={hasActiveFilters} />
    );
  }

  const assetsById = new Map(assets.map((asset) => [asset.id, asset]));

  const rows =
    mode === "tree"
      ? buildTreeDisplayRows(assets, expandedIds, childrenByParentId, loadingChildren)
      : orderAssetsHierarchically(assets).map((asset) => ({
          kind: "asset" as const,
          asset,
          depth: isChildAsset(asset) ? 1 : 0,
        }));

  const selectableIds = rows
    .filter((row): row is Extract<typeof row, { kind: "asset" }> => row.kind === "asset")
    .map((row) => row.asset.id);
  const allSelected =
    selectableIds.length > 0 && selectableIds.every((id) => selectedIds.includes(id));

  return (
    <div className="glass-panel overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-brand-800/50 bg-brand-950/30 text-xs uppercase tracking-wide text-brand-500">
            <tr>
              <th className="px-4 py-3 font-medium">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={() =>
                    onToggleSelectAll(allSelected ? [] : selectableIds)
                  }
                  aria-label="Select all assets on this page"
                  className="rounded border-brand-700 bg-brand-950 text-brand-400"
                />
              </th>
              <th className="px-4 py-3 font-medium">Type</th>
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Project</th>
              <th className="px-4 py-3 font-medium">Criticality</th>
              <th className="px-4 py-3 font-medium">Environment</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Owner</th>
              <th className="px-4 py-3 font-medium">Last Scan</th>
              <th className="px-4 py-3 font-medium">Risk Score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-brand-800/40">
            {rows.map((row) => {
              if (row.kind === "loading") {
                return (
                  <tr key={`loading-${row.parentId}`} className="bg-brand-950/10">
                    <td colSpan={10} className="px-4 py-2 pl-16 text-xs text-brand-500">
                      Loading child assets...
                    </td>
                  </tr>
                );
              }

              if (row.kind === "empty") {
                return (
                  <tr key={`empty-${row.parentId}`} className="bg-brand-950/10">
                    <td colSpan={10} className="px-4 py-2 pl-16 text-xs text-brand-500">
                      No child assets match the current filters.
                    </td>
                  </tr>
                );
              }

              const { asset, depth } = row;
              return (
                <AssetDataRow
                  key={asset.id}
                  asset={asset}
                  projectId={projectId}
                  projectName={projectName}
                  parentLabel={getParentLabel(asset, assetsById)}
                  depth={depth}
                  mode={mode}
                  expanded={expandedIds.has(asset.id)}
                  onToggleExpand={onToggleExpand}
                  selected={selectedIds.includes(asset.id)}
                  onToggleSelect={onToggleSelect}
                  selectable={asset.status !== "deleted"}
                />
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
