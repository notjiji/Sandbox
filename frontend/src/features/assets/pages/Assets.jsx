import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import { ApiError } from "@/shared/api/client";
import { projectsApi } from "@/features/projects/api";
import ProjectNav from "@/features/projects/components/ProjectNav";
import AssetFilters from "../components/AssetFilters";
import AssetPagination from "../components/AssetPagination";
import AssetTable from "../components/AssetTable";
import AssetViewToggle from "../components/AssetViewToggle";
import { assetsApi } from "../api";
import { useProjectAssets } from "../hooks";
import { canUseTreeView } from "../utils/hierarchy";

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
  const [viewMode, setViewMode] = useState("tree");
  const [expandedIds, setExpandedIds] = useState(() => new Set());
  const [childrenByParentId, setChildrenByParentId] = useState({});
  const [loadingChildren, setLoadingChildren] = useState({});
  const [expandError, setExpandError] = useState(null);

  const treeAvailable = canUseTreeView(filters);
  const effectiveMode = treeAvailable && viewMode === "tree" ? "tree" : "flat";

  const query = useMemo(
    () => ({
      ...filters,
      page,
      limit: pageSize,
      roots_only: effectiveMode === "tree",
    }),
    [filters, page, pageSize, effectiveMode],
  );

  const childQuery = useMemo(
    () => ({
      status: filters.status || undefined,
      environment: filters.environment || undefined,
      criticality: filters.criticality || undefined,
    }),
    [filters.status, filters.environment, filters.criticality],
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

  useEffect(() => {
    setExpandedIds(new Set());
    setChildrenByParentId({});
    setLoadingChildren({});
    setExpandError(null);
  }, [filters, page, effectiveMode]);

  useEffect(() => {
    if (!treeAvailable && viewMode === "tree") {
      setViewMode("flat");
    }
  }, [treeAvailable, viewMode]);

  const handleFiltersChange = useCallback((next) => {
    setFilters(next);
    setPage(1);
  }, []);

  const handlePageSizeChange = useCallback((nextLimit) => {
    setPageSize(nextLimit);
    setPage(1);
  }, []);

  const handleToggleExpand = useCallback(async (assetId) => {
    if (expandedIds.has(assetId)) {
      setExpandedIds((prev) => {
        const next = new Set(prev);
        next.delete(assetId);
        return next;
      });
      return;
    }

    setExpandedIds((prev) => new Set(prev).add(assetId));

    if (childrenByParentId[assetId]) {
      return;
    }

    setLoadingChildren((prev) => ({ ...prev, [assetId]: true }));
    setExpandError(null);
    try {
      const response = await assetsApi.children(projectId, assetId, childQuery);
      setChildrenByParentId((prev) => ({
        ...prev,
        [assetId]: response?.data?.items ?? [],
      }));
    } catch (err) {
      setExpandError(err instanceof ApiError ? err.message : "Unable to load child assets.");
      setExpandedIds((prev) => {
        const next = new Set(prev);
        next.delete(assetId);
        return next;
      });
    } finally {
      setLoadingChildren((prev) => ({ ...prev, [assetId]: false }));
    }
  }, [childQuery, childrenByParentId, expandedIds, projectId]);

  const countLabel = loading
    ? "Loading assets..."
    : effectiveMode === "tree"
      ? `${total} root asset${total === 1 ? "" : "s"}`
      : `${total} asset${total === 1 ? "" : "s"}`;

  return (
    <DashboardShell title="Assets" subtitle="Search, filter, and manage digital assets.">
      {error && <FormAlert message={error} />}
      {expandError && <FormAlert message={expandError} />}
      <ProjectNav projectName={project?.name} active="assets" />

      <div className="space-y-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-1">
            <p className="text-sm text-brand-500">{countLabel}</p>
            {effectiveMode === "flat" && treeAvailable && viewMode === "flat" && (
              <p className="text-xs text-brand-600">Flat view shows all matching assets on one page.</p>
            )}
            {!treeAvailable && (
              <p className="text-xs text-brand-600">
                Tree view is unavailable while searching or filtering child asset types.
              </p>
            )}
          </div>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <AssetViewToggle
              mode={effectiveMode}
              onChange={setViewMode}
              treeAvailable={treeAvailable}
            />
            <Link to={`/projects/${projectId}/assets/new`} className="btn-primary w-fit">
              Add asset
            </Link>
          </div>
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
              mode={effectiveMode}
              expandedIds={expandedIds}
              childrenByParentId={childrenByParentId}
              loadingChildren={loadingChildren}
              onToggleExpand={handleToggleExpand}
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
