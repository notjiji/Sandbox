import { useNavigate, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import { ApiError } from "@/shared/api/client";
import type { AssetSummary } from "@/shared/types/asset";
import type { ProjectSummary } from "@/shared/types/project";
import { projectsApi } from "@/features/projects/api";
import ProjectNav from "@/features/projects/components/ProjectNav";
import AssetForm from "../components/AssetForm";
import { assetsApi } from "../api";
import { useProjectAssets } from "../hooks";

export default function AssetEdit() {
  const { projectId, assetId } = useParams<{ projectId: string; assetId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [asset, setAsset] = useState<AssetSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { assets: parentAssets } = useProjectAssets(projectId, { limit: 100 });

  useEffect(() => {
    if (!projectId || !assetId) return undefined;
    let active = true;
    setLoading(true);
    Promise.all([projectsApi.get(projectId), assetsApi.get(projectId, assetId)])
      .then(([projectResponse, assetResponse]) => {
        if (!active) return;
        setProject(projectResponse?.data ?? null);
        setAsset(assetResponse?.data ?? null);
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof ApiError ? err.message : "Unable to load asset.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [projectId, assetId]);

  if (!projectId || !assetId) return null;

  return (
    <DashboardShell title="Edit asset" subtitle={asset?.name ?? "Update asset details"}>
      {error && <FormAlert message={error} />}
      <ProjectNav projectName={project?.name} assetName={asset?.name} active="overview" />

      {loading ? (
        <p className="text-brand-500">Loading asset...</p>
      ) : asset?.status === "deleted" ? (
        <div className="glass-panel max-w-xl space-y-3 p-6">
          <p className="text-brand-200">Deleted assets cannot be edited.</p>
          <button
            type="button"
            onClick={() => navigate(`/projects/${projectId}/assets/${assetId}`)}
            className="btn-ghost"
          >
            Back to asset detail
          </button>
        </div>
      ) : asset ? (
        <div className="max-w-xl">
          <AssetForm
            mode="edit"
            projectId={projectId}
            assetId={assetId}
            asset={asset}
            parentAssets={parentAssets}
            onSuccess={() => navigate(`/projects/${projectId}/assets/${assetId}`)}
          />
        </div>
      ) : null}
    </DashboardShell>
  );
}
