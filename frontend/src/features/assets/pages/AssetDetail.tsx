import { useEffect, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ChevronDown, Pencil, Radar } from "lucide-react";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import { ApiError } from "@/shared/api/client";
import type { AssetOverview } from "@/shared/types/asset-overview";
import type { ProjectSummary } from "@/shared/types/project";
import { projectsApi } from "@/features/projects/api";
import ProjectNav from "@/features/projects/components/ProjectNav";
import {
  AssetCriticalityBadge,
  AssetEnvironmentBadge,
  AssetStatusBadge,
  AssetTypeBadge,
} from "../components/AssetBadges";
import AssetDashboard from "../components/AssetDashboard";
import AssetLifecycleActions from "../components/AssetLifecycleActions";
import AssetRelationshipsPanel from "../components/AssetRelationshipsPanel";
import AssetTimelinePanel from "../components/AssetTimelinePanel";
import { assetsApi } from "../api";
import {
  ASSET_CATEGORY_LABELS,
  ASSET_TYPE_LABELS,
  getPrimaryMetadataValue,
} from "../types";
import { formatActor, formatDateTime } from "../utils";

interface DetailFieldProps {
  label: string;
  children: ReactNode;
}

function DetailField({ label, children }: DetailFieldProps) {
  return (
    <div>
      <p className="terminal-text mb-1 text-xs text-brand-500">{label}</p>
      <div className="text-brand-100">{children}</div>
    </div>
  );
}

export default function AssetDetail() {
  const { projectId, assetId } = useParams<{ projectId: string; assetId: string }>();
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [overview, setOverview] = useState<AssetOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  const load = async () => {
    if (!projectId || !assetId) return;
    setLoading(true);
    setError(null);
    try {
      const [projectResponse, overviewResponse] = await Promise.all([
        projectsApi.get(projectId),
        assetsApi.overview(projectId, assetId),
      ]);
      setProject(projectResponse ?? null);
      setOverview(overviewResponse ?? null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load asset dashboard.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [projectId, assetId]);

  const asset = overview?.asset ?? null;
  const primaryValue = asset ? getPrimaryMetadataValue(asset) : null;
  const metadataEntries = asset?.metadata ? Object.entries(asset.metadata) : [];

  if (!projectId || !assetId) return null;

  return (
    <DashboardShell
      title={asset?.name ?? "Asset"}
      subtitle={asset ? (ASSET_TYPE_LABELS[asset.type] ?? asset.type) : "Asset command center"}
    >
      {error && <FormAlert message={error} />}
      <ProjectNav projectName={project?.name} assetName={asset?.name} active="overview" />

      {loading ? (
        <p className="text-brand-500">Loading asset dashboard...</p>
      ) : asset && overview ? (
        <div className="space-y-6">
          {asset.status === "deleted" && (
            <div className="rounded-lg border border-red-500/30 bg-red-950/20 px-4 py-3 text-sm text-red-200">
              This asset has been deleted. Restore it to edit details or run scans.
            </div>
          )}
          {asset.status === "archived" && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-950/20 px-4 py-3 text-sm text-amber-200">
              This asset is archived. Restore it to run scans; other details can still be edited.
            </div>
          )}

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-panel p-6"
          >
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <AssetTypeBadge type={asset.type} />
                  <AssetStatusBadge status={asset.status} />
                  <AssetCriticalityBadge criticality={asset.criticality} />
                  <AssetEnvironmentBadge environment={asset.environment} />
                </div>
                <h2 className="text-2xl font-semibold text-brand-50">{asset.name}</h2>
                {primaryValue && <p className="mt-1 text-brand-400">{primaryValue}</p>}
                {asset.description && (
                  <p className="mt-3 max-w-3xl text-sm leading-relaxed text-brand-300">
                    {asset.description}
                  </p>
                )}
              </div>

              <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
                {asset.status === "active" && (
                  <Link
                    to={`/projects/${projectId}/assets/${assetId}/scans`}
                    className="btn-primary inline-flex items-center gap-2"
                  >
                    <Radar size={18} />
                    Run scan
                  </Link>
                )}
                {asset.status !== "deleted" && (
                  <Link
                    to={`/projects/${projectId}/assets/${assetId}/edit`}
                    className="btn-ghost inline-flex items-center gap-2"
                  >
                    <Pencil size={18} />
                    Edit
                  </Link>
                )}
              </div>
            </div>

            <div className="mt-6">
              <AssetLifecycleActions projectId={projectId} asset={asset} onChanged={load} />
            </div>
          </motion.div>

          <AssetDashboard overview={overview} projectId={projectId} assetId={assetId} />

          <AssetTimelinePanel projectId={projectId} assetId={assetId} />

          <div className="glass-panel overflow-hidden">
            <button
              type="button"
              onClick={() => setDetailsOpen((open) => !open)}
              className="flex w-full items-center justify-between px-6 py-4 text-left"
            >
              <span className="text-lg font-semibold text-brand-100">Asset details</span>
              <ChevronDown
                size={18}
                className={`text-brand-500 transition ${detailsOpen ? "rotate-180" : ""}`}
              />
            </button>
            {detailsOpen && (
              <div className="space-y-6 border-t border-brand-800/50 px-6 py-6">
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <DetailField label="organization">{asset.organization_name ?? "—"}</DetailField>
                  <DetailField label="project">{asset.project_name ?? project?.name ?? "—"}</DetailField>
                  <DetailField label="external identifier">
                    {asset.external_identifier || primaryValue || "—"}
                  </DetailField>
                  <DetailField label="business unit">{asset.business_unit || "—"}</DetailField>
                  <DetailField label="owner">{asset.owner || "—"}</DetailField>
                  <DetailField label="asset category">
                    {asset.asset_category
                      ? (ASSET_CATEGORY_LABELS[asset.asset_category] ?? asset.asset_category)
                      : "—"}
                  </DetailField>
                  <DetailField label="created">{formatDateTime(asset.created_at)}</DetailField>
                  <DetailField label="updated">{formatDateTime(asset.updated_at)}</DetailField>
                  <DetailField label="created by">{formatActor(asset.created_by)}</DetailField>
                </div>
                {metadataEntries.length > 0 && (
                  <div>
                    <h3 className="mb-3 text-sm font-semibold text-brand-200">Type metadata</h3>
                    <dl className="space-y-3">
                      {metadataEntries.map(([key, value]) => (
                        <div
                          key={key}
                          className="flex items-start justify-between gap-4 border-b border-brand-800/40 pb-3 last:border-0 last:pb-0"
                        >
                          <dt className="terminal-text text-xs text-brand-500">{key}</dt>
                          <dd className="text-right text-sm text-brand-200">{value}</dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                )}
              </div>
            )}
          </div>

          <AssetRelationshipsPanel projectId={projectId} assetId={assetId} asset={asset} />
        </div>
      ) : null}
    </DashboardShell>
  );
}
