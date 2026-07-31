import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import { projectsApi } from "@/features/projects/api";
import ProjectNav from "@/features/projects/components/ProjectNav";
import AssetCreateForm from "../components/AssetCreateForm";
import AssetFilters from "../components/AssetFilters";
import AssetTable from "../components/AssetTable";
import { useProjectAssets } from "../hooks";

const DEFAULT_FILTERS = {
  search: "",
  type: "",
  status: "",
  environment: "",
  criticality: "",
};

export default function Assets() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [showCreate, setShowCreate] = useState(false);
  const { assets, total, loading, error, reload } = useProjectAssets(projectId, filters);
  const { assets: allAssets, reload: reloadParents } = useProjectAssets(projectId, { limit: 100 });

  useEffect(() => {
    let active = true;
    projectsApi.get(projectId).then((response) => {
      if (active) setProject(response?.data ?? null);
    }).catch(() => {});
    return () => {
      active = false;
    };
  }, [projectId]);

  const handleCreated = useCallback(async () => {
    setShowCreate(false);
    await Promise.all([reload(), reloadParents()]);
  }, [reload, reloadParents]);

  const summary = useMemo(() => {
    if (loading) return "Loading assets...";
    return `${total} asset${total === 1 ? "" : "s"} in this project`;
  }, [loading, total]);

  return (
    <DashboardShell title="Assets" subtitle="Search, filter, and manage digital assets.">
      {error && <FormAlert message={error} />}
      <ProjectNav projectName={project?.name} active="assets" />

      <div className="space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-brand-500">{summary}</p>
          <button
            type="button"
            onClick={() => setShowCreate((value) => !value)}
            className="btn-primary w-fit"
          >
            {showCreate ? "Hide form" : "Add asset"}
          </button>
        </div>

        <AssetFilters filters={filters} onChange={setFilters} />

        {loading ? (
          <p className="text-brand-500">Loading assets...</p>
        ) : (
          <AssetTable
            assets={assets}
            projectId={projectId}
            projectName={project?.name}
          />
        )}

        {showCreate && (
          <div className="grid gap-6 lg:grid-cols-[1fr_24rem]">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-panel p-6"
            >
              <h2 className="mb-2 text-lg font-semibold text-brand-100">Register a new asset</h2>
              <p className="text-sm text-brand-500">
                Assets start in Pending status. Activate them when ready to scan.
              </p>
            </motion.div>
            <AssetCreateForm
              projectId={projectId}
              parentAssets={allAssets}
              onCreated={handleCreated}
            />
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
