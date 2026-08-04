import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { GitBranchPlus, Link2, Trash2 } from "lucide-react";
import FormAlert from "@/shared/components/FormAlert";
import { ApiError } from "@/shared/api/client";
import type { AssetRelationships, AssetSummary, AssetType } from "@/shared/types/asset";
import { assetsApi } from "../api";
import {
  ALLOWED_PARENT_TYPES,
  ASSET_LINK_TYPES,
  ASSET_LINK_TYPE_LABELS,
  ASSET_TYPE_LABELS,
  getPrimaryMetadataValue,
} from "../types";
import { AssetTypeBadge } from "./AssetBadges";
import AssetDependencyGraph from "./AssetDependencyGraph";

interface AssetRelationshipsPanelProps {
  projectId: string;
  assetId: string;
  asset: AssetSummary;
}

function RelationshipAssetRow({
  item,
  projectId,
  subtitle,
}: {
  item: AssetSummary;
  projectId: string;
  subtitle?: string;
}) {
  const primary = getPrimaryMetadataValue(item);
  return (
    <Link
      to={`/projects/${projectId}/assets/${item.id}`}
      className="flex items-start justify-between gap-4 rounded-lg border border-brand-800/50 px-4 py-3 transition-colors hover:border-brand-700/70 hover:bg-brand-900/20"
    >
      <div className="min-w-0">
        <p className="font-medium text-brand-100">{item.name}</p>
        {primary && <p className="mt-0.5 text-xs text-brand-500">{primary}</p>}
        {subtitle && <p className="mt-1 text-xs text-brand-600">{subtitle}</p>}
      </div>
      <AssetTypeBadge type={item.type} />
    </Link>
  );
}

export default function AssetRelationshipsPanel({
  projectId,
  assetId,
  asset,
}: AssetRelationshipsPanelProps) {
  const [relationships, setRelationships] = useState<AssetRelationships | null>(null);
  const [projectAssets, setProjectAssets] = useState<AssetSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [linkTargetId, setLinkTargetId] = useState("");
  const [linkType, setLinkType] = useState<(typeof ASSET_LINK_TYPES)[number]>("related");
  const [linkLabel, setLinkLabel] = useState("");
  const [linkSubmitting, setLinkSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [relationshipsResponse, assetsResponse] = await Promise.all([
        assetsApi.relationships(projectId, assetId),
        assetsApi.list(projectId, { limit: 100 }),
      ]);
      setRelationships(relationshipsResponse ?? null);
      setProjectAssets(assetsResponse?.items ?? []);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load relationships.");
    } finally {
      setLoading(false);
    }
  }, [projectId, assetId]);

  useEffect(() => {
    void load();
  }, [load]);

  const allowedChildTypes = useMemo(
    () =>
      (Object.entries(ALLOWED_PARENT_TYPES) as Array<[AssetType, AssetType[]]>)
        .filter(([, parents]) => parents.includes(asset.type))
        .map(([childType]) => childType),
    [asset.type],
  );

  const linkCandidates = useMemo(
    () => projectAssets.filter((item) => item.id !== assetId),
    [projectAssets, assetId],
  );

  const handleCreateLink = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!linkTargetId) return;
    setLinkSubmitting(true);
    setError(null);
    try {
      await assetsApi.createLink(projectId, assetId, {
        target_asset_id: linkTargetId,
        link_type: linkType,
        label: linkLabel.trim() || undefined,
      });
      setLinkTargetId("");
      setLinkLabel("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to create link.");
    } finally {
      setLinkSubmitting(false);
    }
  };

  const handleDeleteLink = async (linkId: string) => {
    setError(null);
    try {
      await assetsApi.deleteLink(projectId, assetId, linkId);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to remove link.");
    }
  };

  if (loading) {
    return <p className="text-sm text-brand-500">Loading relationships...</p>;
  }

  if (!relationships) return null;

  return (
    <div className="space-y-6">
      {error && <FormAlert message={error} />}

      {relationships.ancestors.length > 0 && (
        <div className="glass-panel p-6">
          <h2 className="mb-4 text-lg font-semibold text-brand-100">Parent Chain</h2>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            {relationships.ancestors.map((ancestor, index) => (
              <div key={ancestor.id} className="flex items-center gap-2">
                <Link
                  to={`/projects/${projectId}/assets/${ancestor.id}`}
                  className="rounded-full border border-brand-700/50 px-3 py-1 text-brand-200 hover:border-brand-500/60 hover:text-brand-50"
                >
                  {ancestor.name}
                </Link>
                {index < relationships.ancestors.length - 1 && (
                  <span className="text-brand-600">→</span>
                )}
              </div>
            ))}
            <span className="text-brand-600">→</span>
            <span className="rounded-full border border-brand-400/40 bg-brand-900/40 px-3 py-1 text-brand-100">
              {asset.name}
            </span>
          </div>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="glass-panel p-6">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-brand-100">Parent Asset</h2>
            <Link2 size={18} className="text-brand-500" />
          </div>
          {relationships.parent ? (
            <RelationshipAssetRow item={relationships.parent} projectId={projectId} />
          ) : (
            <p className="text-sm text-brand-500">No parent asset assigned.</p>
          )}
        </div>

        <div className="glass-panel p-6">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-brand-100">Child Assets</h2>
            {allowedChildTypes.length > 0 && (
              <Link
                to={`/projects/${projectId}/assets/new?parent_id=${assetId}&type=${allowedChildTypes[0]}`}
                className="btn-ghost inline-flex items-center gap-2 text-xs"
              >
                <GitBranchPlus size={16} />
                Add child
              </Link>
            )}
          </div>
          {relationships.children.length === 0 ? (
            <p className="text-sm text-brand-500">No child assets linked yet.</p>
          ) : (
            <div className="space-y-2">
              {relationships.children.map((child) => (
                <RelationshipAssetRow
                  key={child.id}
                  item={child}
                  projectId={projectId}
                  subtitle={ASSET_TYPE_LABELS[child.type]}
                />
              ))}
            </div>
          )}
          {relationships.descendants_count > relationships.children.length && (
            <p className="mt-3 text-xs text-brand-500">
              {relationships.descendants_count} total descendants in this branch.
            </p>
          )}
        </div>
      </div>

      <div className="glass-panel p-6">
        <h2 className="mb-4 text-lg font-semibold text-brand-100">Linked Assets</h2>
        {relationships.links.length === 0 ? (
          <p className="mb-4 text-sm text-brand-500">No peer links configured.</p>
        ) : (
          <ul className="mb-4 space-y-2">
            {relationships.links.map((link) => (
              <li
                key={link.id}
                className="flex items-center justify-between gap-3 rounded-lg border border-brand-800/50 px-4 py-3"
              >
                <div className="min-w-0">
                  <p className="text-sm text-brand-300">
                    <span className="text-brand-500">
                      {link.direction === "outbound" ? "→" : "←"}
                    </span>{" "}
                    {ASSET_LINK_TYPE_LABELS[link.link_type]}
                    {link.label ? ` · ${link.label}` : ""}
                  </p>
                  <Link
                    to={`/projects/${projectId}/assets/${link.asset.id}`}
                    className="font-medium text-brand-100 hover:text-brand-50"
                  >
                    {link.asset.name}
                  </Link>
                </div>
                {link.direction === "outbound" && (
                  <button
                    type="button"
                    onClick={() => void handleDeleteLink(link.id)}
                    className="btn-ghost inline-flex items-center gap-1 text-xs text-red-300"
                  >
                    <Trash2 size={14} />
                    Remove
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}

        <form onSubmit={handleCreateLink} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <select
            value={linkTargetId}
            onChange={(e) => setLinkTargetId(e.target.value)}
            className="input-field lg:col-span-2"
            aria-label="Link target asset"
          >
            <option value="">Select asset to link...</option>
            {linkCandidates.map((candidate) => (
              <option key={candidate.id} value={candidate.id}>
                {candidate.name} ({ASSET_TYPE_LABELS[candidate.type]})
              </option>
            ))}
          </select>
          <select
            value={linkType}
            onChange={(e) => setLinkType(e.target.value as (typeof ASSET_LINK_TYPES)[number])}
            className="input-field"
            aria-label="Link type"
          >
            {ASSET_LINK_TYPES.map((type) => (
              <option key={type} value={type}>
                {ASSET_LINK_TYPE_LABELS[type]}
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={!linkTargetId || linkSubmitting}
            className="btn-primary"
          >
            {linkSubmitting ? "Linking..." : "Add link"}
          </button>
          <input
            value={linkLabel}
            onChange={(e) => setLinkLabel(e.target.value)}
            className="input-field sm:col-span-2 lg:col-span-4"
            placeholder="Optional label"
          />
        </form>
      </div>

      <div className="glass-panel p-6">
        <h2 className="mb-4 text-lg font-semibold text-brand-100">Dependency Graph</h2>
        <AssetDependencyGraph graph={relationships.graph} projectId={projectId} />
      </div>
    </div>
  );
}
