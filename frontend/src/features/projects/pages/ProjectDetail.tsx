import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import { ApiError } from "@/shared/api/client";
import type { ProjectOverview } from "@/shared/types/project-overview";
import { projectsApi } from "../api";
import ProjectDashboard from "../components/ProjectDashboard";
import ProjectLifecycleActions from "../components/ProjectLifecycleActions";
import ProjectNav from "../components/ProjectNav";

export default function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>();
  const [overview, setOverview] = useState<ProjectOverview | null>(null);
  const [alert, setAlert] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let active = true;
    if (!projectId) return undefined;

    async function load() {
      try {
        const response = await projectsApi.getOverview(projectId!);
        if (!active) return;
        setOverview(response ?? null);
      } catch (error) {
        if (active) {
          setAlert(error instanceof ApiError ? error.message : "Unable to load project.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [projectId, refreshKey]);

  return (
    <DashboardShell
      title={overview?.project.name ?? "Project"}
      subtitle={overview?.project.description ?? "Project workspace overview"}
    >
      {alert && <FormAlert message={alert} />}
      <ProjectNav projectName={overview?.project.name} active="overview" />

      {overview && (
        <div className="mb-6 flex justify-end">
          <ProjectLifecycleActions
            project={overview.project}
            compact
            onChanged={() => setRefreshKey((value) => value + 1)}
          />
        </div>
      )}

      {loading ? (
        <p className="text-brand-500">Loading project dashboard...</p>
      ) : !overview ? (
        <p className="text-brand-500">Project not found.</p>
      ) : (
        <ProjectDashboard overview={overview} projectId={projectId!} />
      )}
    </DashboardShell>
  );
}
