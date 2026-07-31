import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import { projectsApi } from "@/features/projects/api";
import ProjectNav from "@/features/projects/components/ProjectNav";
import AssetFilters from "../components/AssetFilters";
import AssetPagination from "../components/AssetPagination";
import AssetTable from "../components/AssetTable";
import { useProjectAssets } from "../hooks";

const PAGE_SIZE_OPTIONS = [10, 20, 50];
const DEFAULT_PAGE_SIZE = 20;

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
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);

  const query = useMemo(
    () => ({ ...filters, page, limit: pageSize }),
    [filters, page, pageSize],
  );

  const { assets, total, loading, error } = useProjectAssets(projectId, query);

  useEffect(() => {
    let active = true;
    projectsApi.get(projectId).then((response) => {
      if (active) setProject(response?.data ?? null);
    }).catch(() => {});
    return () => {
      active = false;
    };
  }, [projectId]);

  const handleFiltersChange = useCallback((next) => {
    setFilters(next);
    setPage(1);
  }, []);

  const handlePageSizeChange = useCallback((nextLimit) => {
    setPageSize(nextLimit);
    setPage(1);
  }, []);

  return (
    <DashboardShell title="Assets" subtitle="Search, filter, and manage digital assets.">
      {error && <FormAlert message={error} />}
      <ProjectNav projectName={project?.name} active="assets" />

      <div className="space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-brand-500">
            {loading ? "Loading assets..." : `${total} asset${total === 1 ? "" : "s"} in this project`}
          </p>
          <Link to={`/projects/${projectId}/assets/new`} className="btn-primary w-fit">
            Add asset
          </Link>
        </div>

        <AssetFilters filters={filters} onChange={handleFiltersChange} />

        {loading ? (
          <p className="text-brand-500">Loading assets...</p>
        ) : (
          <>
            <AssetTable
              assets={assets}
              projectId={projectId}
              projectName={project?.name}
            />
            <AssetPagination
              page={page}
              limit={pageSize}
              total={total}
              pageSizeOptions={PAGE_SIZE_OPTIONS}
              onPageChange={setPage}
              onLimitChange={handlePageSizeChange}
            />
          </>
        )}
      </div>
    </DashboardShell>
  );
}
