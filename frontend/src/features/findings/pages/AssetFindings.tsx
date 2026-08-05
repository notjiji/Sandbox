import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Bug } from "lucide-react";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import EmptyState from "@/shared/components/EmptyState";
import { ListSkeleton } from "@/shared/components/ui/Skeleton";
import AssetPagination from "@/features/assets/components/AssetPagination";
import { toast } from "@/shared/lib/toast";
import { ApiError } from "@/shared/api/client";
import type { AssetSummary } from "@/shared/types/asset";
import type { FindingSummary } from "@/shared/types/finding";
import type { ProjectSummary } from "@/shared/types/project";
import { assetsApi } from "@/features/assets/api";
import { projectsApi } from "@/features/projects/api";
import ProjectNav from "@/features/projects/components/ProjectNav";
import AssetFindingsFilters, {
  filtersToQuery,
  type AssetFindingsFiltersState,
} from "../components/AssetFindingsFilters";
import AssetFindingsTable from "../components/AssetFindingsTable";
import { findingsApi } from "../api";

const PAGE_SIZE = 20;

export default function AssetFindings() {
  const { projectId, assetId } = useParams<{ projectId: string; assetId: string }>();
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [asset, setAsset] = useState<AssetSummary | null>(null);
  const [findings, setFindings] = useState<FindingSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(PAGE_SIZE);
  const [filters, setFilters] = useState<AssetFindingsFiltersState>({
    search: "",
    status_group: "",
    severity: "",
    sort: "risk_score",
    order: "desc",
  });
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    if (!projectId || !assetId) return;
    const [projectResponse, assetResponse, findingsResponse] = await Promise.all([
      projectsApi.get(projectId),
      assetsApi.get(projectId, assetId),
      findingsApi.listForAsset(
        projectId,
        assetId,
        filtersToQuery(filters, page, limit),
      ),
    ]);
    setProject(projectResponse ?? null);
    setAsset(assetResponse ?? null);
    setFindings(findingsResponse?.items ?? []);
    setTotal(findingsResponse?.total ?? 0);
  }, [assetId, filters, limit, page, projectId]);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      try {
        await loadData();
      } catch (error) {
        if (active) {
          toast.error(error instanceof ApiError ? error.message : "Unable to load findings.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [loadData]);

  const handleFiltersChange = (next: AssetFindingsFiltersState) => {
    setFilters(next);
    setPage(1);
  };

  return (
    <DashboardShell
      title="Findings"
      subtitle={asset ? `Findings for ${asset.name}` : "Asset findings"}
    >
      <ProjectNav projectName={project?.name} assetName={asset?.name} active="findings" />

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel p-6"
      >
        <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-lg font-semibold text-brand-100">Findings</h2>
          <p className="text-sm text-brand-500">
            {total} finding{total === 1 ? "" : "s"}
          </p>
        </div>

        <AssetFindingsFilters filters={filters} onChange={handleFiltersChange} />

        <div className="mt-4">
          {loading ? (
            <ListSkeleton rows={6} />
          ) : findings.length === 0 ? (
            <EmptyState
              compact
              icon={Bug}
              title={
                filters.search || filters.severity || filters.status_group
                  ? "No matching findings"
                  : "No findings yet"
              }
              description={
                filters.search || filters.severity || filters.status_group
                  ? "Adjust your filters or search term."
                  : "Run a scan to discover vulnerabilities on this asset."
              }
            />
          ) : (
            <>
              <AssetFindingsTable findings={findings} />
              <div className="mt-6">
                <AssetPagination
                  page={page}
                  limit={limit}
                  total={total}
                  pageSizeOptions={[20, 50, 100]}
                  onPageChange={setPage}
                  onLimitChange={(nextLimit) => {
                    setLimit(nextLimit);
                    setPage(1);
                  }}
                />
              </div>
            </>
          )}
        </div>
      </motion.div>
    </DashboardShell>
  );
}
