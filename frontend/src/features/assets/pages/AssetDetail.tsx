import { useEffect, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Pencil, Radar } from "lucide-react";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import { ApiError } from "@/shared/api/client";
import type { AssetSummary } from "@/shared/types/asset";
import type { ProjectSummary } from "@/shared/types/project";
import { projectsApi } from "@/features/projects/api";
import ProjectNav from "@/features/projects/components/ProjectNav";
import {
  AssetCriticalityBadge,
  AssetEnvironmentBadge,
  AssetStatusBadge,
  AssetTypeBadge,
} from "../components/AssetBadges";
import AssetLifecycleActions from "../components/AssetLifecycleActions";
import PlaceholderPanel from "../components/PlaceholderPanel";
import { assetsApi } from "../api";
import { useAssetAuditHistory } from "../hooks";
import { ASSET_TYPE_LABELS, getPrimaryMetadataValue } from "../types";
import { formatAuditAction, formatDateTime, UNAVAILABLE } from "../utils";

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
  const [asset, setAsset] = useState<AssetSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { auditLogs, loading: auditLoading } = useAssetAuditHistory(projectId, assetId);

  const load = async () => {
    if (!projectId || !assetId) return;
    setLoading(true);
    setError(null);
    try {
      const [projectResponse, assetResponse] = await Promise.all([
        projectsApi.get(projectId),
        assetsApi.get(projectId, assetId),
      ]);
      setProject(projectResponse ?? null);
      setAsset(assetResponse ?? null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load asset.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [projectId, assetId]);

  const primaryValue = asset ? getPrimaryMetadataValue(asset) : null;
  const metadataEntries = asset?.metadata ? Object.entries(asset.metadata) : [];

  if (!projectId || !assetId) return null;

  return (
    <DashboardShell
      title={asset?.name ?? "Asset"}
      subtitle={asset ? (ASSET_TYPE_LABELS[asset.type] ?? asset.type) : "Asset inventory detail"}
    >
      {error && <FormAlert message={error} />}
      <ProjectNav projectName={project?.name} assetName={asset?.name} active="overview" />

      {loading ? (
        <p className="text-brand-500">Loading asset...</p>
      ) : asset ? (
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
                    View scans
                  </Link>
                )}
                {asset.status !== "deleted" && (
                  <Link
                    to={`/projects/${projectId}/assets/${assetId}/edit`}
                    className="btn-ghost inline-flex items-center gap-2"
                  >
                    <Pencil size={18} />
                    {asset.status === "archived" ? "Edit details" : "Edit"}
                  </Link>
                )}
              </div>
            </div>

            <div className="mt-6">
              <AssetLifecycleActions projectId={projectId} asset={asset} onChanged={load} />
            </div>

            <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <DetailField label="criticality">
                <AssetCriticalityBadge criticality={asset.criticality} />
              </DetailField>
              <DetailField label="status">
                <AssetStatusBadge status={asset.status} />
              </DetailField>
              <DetailField label="environment">
                <AssetEnvironmentBadge environment={asset.environment} />
              </DetailField>
              <DetailField label="owner">{asset.owner || "—"}</DetailField>
            </div>

            {asset.tags.length > 0 && (
              <div className="mt-6">
                <p className="terminal-text mb-2 text-xs text-brand-500">tags</p>
                <div className="flex flex-wrap gap-2">
                  {asset.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full border border-brand-700/50 bg-brand-900/40 px-3 py-1 text-xs text-brand-300"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </motion.div>

          <div className="grid gap-6 lg:grid-cols-2">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-panel p-6"
            >
              <h2 className="mb-4 text-lg font-semibold text-brand-100">Metadata</h2>
              {metadataEntries.length === 0 ? (
                <p className="text-sm text-brand-500">No metadata recorded.</p>
              ) : (
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
              )}
            </motion.div>

            <PlaceholderPanel
              title="Last Scan"
              phase="Phase 5"
              description="Scan history and last-run timestamps will appear here once scanning is fully wired."
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <PlaceholderPanel
              title="Risk Score"
              phase="Phase 6"
              description="Asset-level risk scoring based on open findings and criticality weighting."
            />
            <PlaceholderPanel
              title="Recent Findings"
              phase="Phase 6"
              description="Latest vulnerabilities discovered on this asset will be listed here."
            />
          </div>

          <PlaceholderPanel
            title="Recent Reports"
            description="Generated reports that include this asset will appear in a future release."
          />

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-panel p-6"
          >
            <h2 className="mb-4 text-lg font-semibold text-brand-100">Audit History</h2>
            {auditLoading ? (
              <p className="text-sm text-brand-500">Loading audit history...</p>
            ) : auditLogs.length === 0 ? (
              <p className="text-sm text-brand-500">No audit events recorded yet.</p>
            ) : (
              <ul className="space-y-3">
                {auditLogs.map((entry) => (
                  <li
                    key={entry.id}
                    className="flex items-start justify-between gap-4 rounded-lg border border-brand-800/50 px-4 py-3"
                  >
                    <div>
                      <p className="font-medium text-brand-100">
                        {formatAuditAction(entry.action)}
                      </p>
                      {entry.details && Object.keys(entry.details).length > 0 && (
                        <p className="mt-1 text-xs text-brand-500">
                          {JSON.stringify(entry.details)}
                        </p>
                      )}
                    </div>
                    <time className="shrink-0 text-xs text-brand-500">
                      {formatDateTime(entry.created_at)}
                    </time>
                  </li>
                ))}
              </ul>
            )}
          </motion.div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <DetailField label="last scan">{UNAVAILABLE}</DetailField>
            <DetailField label="risk score">{UNAVAILABLE}</DetailField>
            <DetailField label="project">{project?.name ?? "—"}</DetailField>
            <DetailField label="children">{asset.children_count ?? 0}</DetailField>
          </div>
        </div>
      ) : null}
    </DashboardShell>
  );
}
