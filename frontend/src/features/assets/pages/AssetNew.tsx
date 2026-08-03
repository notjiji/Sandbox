import { useNavigate, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import { ApiError } from "@/shared/api/client";
import type { ProjectSummary } from "@/shared/types/project";
import { projectsApi } from "@/features/projects/api";
import ProjectNav from "@/features/projects/components/ProjectNav";
import AssetForm from "../components/AssetForm";
import { useProjectAssets } from "../hooks";

export default function AssetNew() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const { assets: parentAssets } = useProjectAssets(projectId, { limit: 100 });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) return;
    projectsApi
      .get(projectId)
      .then((response) => {
        setProject(response?.data ?? null);
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Unable to load project.");
      });
  }, [projectId]);

  if (!projectId) return null;

  return (
    <DashboardShell title="Add asset" subtitle="Register a new digital asset in this project.">
      {error && <FormAlert message={error} />}
      <ProjectNav projectName={project?.name} active="assets" />
      <div className="max-w-xl">
        <AssetForm
          mode="create"
          projectId={projectId}
          parentAssets={parentAssets}
          onSuccess={() => navigate(`/projects/${projectId}/assets`)}
        />
      </div>
    </DashboardShell>
  );
}
