import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { FileText, Sparkles } from "lucide-react";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import EmptyState from "@/shared/components/EmptyState";
import { ListSkeleton } from "@/shared/components/ui/Skeleton";
import AssetPagination from "@/features/assets/components/AssetPagination";
import { toast } from "@/shared/lib/toast";
import { ApiError } from "@/shared/api/client";
import type { ProjectSummary } from "@/shared/types/project";
import type { ReportSummary, ReportStatus, ReportType } from "@/shared/types/report";
import { projectsApi } from "@/features/projects/api";
import ProjectNav from "@/features/projects/components/ProjectNav";
import AssetReportsTable from "../components/AssetReportsTable";
import GenerateReportModal from "../components/GenerateReportModal";
import ReportPreviewModal from "../components/ReportPreviewModal";
import { useReportPolling } from "../hooks/useReportPolling";
import { reportsApi } from "../api";
import { REPORT_TYPES } from "../utils";
import { useOrganizationRole } from "@/shared/hooks/useOrganizationRole";

const PAGE_SIZE = 20;
const PRIMARY_REPORT_TYPES: ReportType[] = ["executive", "technical"];

export default function Reports() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(PAGE_SIZE);
  const [typeFilter, setTypeFilter] = useState<ReportType | "">("");
  const [statusFilter, setStatusFilter] = useState<ReportStatus | "">("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [previewReport, setPreviewReport] = useState<ReportSummary | null>(null);
  const { canGenerateReport, canDeleteReport } = useOrganizationRole();

  const loadData = useCallback(async () => {
    if (!projectId) return;
    const [projectResponse, reportsResponse] = await Promise.all([
      projectsApi.get(projectId),
      reportsApi.list(projectId, {
        page,
        limit,
        report_type: typeFilter || undefined,
        status: statusFilter || undefined,
        search: search.trim() || undefined,
      }),
    ]);
    setProject(projectResponse ?? null);
    setReports(reportsResponse?.items ?? []);
    setTotal(reportsResponse?.total ?? 0);
  }, [limit, page, projectId, search, statusFilter, typeFilter]);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      try {
        await loadData();
      } catch (error) {
        if (active) {
          toast.error(error instanceof ApiError ? error.message : "Unable to load reports.");
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

  useReportPolling({
    reports,
    onRefresh: loadData,
  });

  const handleRegenerate = async (reportId: string) => {
    if (!projectId) return;
    setActionId(reportId);
    try {
      await reportsApi.regenerate(projectId, reportId);
      toast.success("Report generation started.");
      await loadData();
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to regenerate report.");
    } finally {
      setActionId(null);
    }
  };

  const handleDownload = async (report: ReportSummary) => {
    if (!projectId) return;
    try {
      const signed = report.asset_id
        ? await reportsApi.getDownloadUrlForAsset(projectId, report.asset_id, report.id)
        : await reportsApi.getDownloadUrl(projectId, report.id);
      if (!signed) throw new Error("Missing download URL");
      await reportsApi.downloadSigned(signed.url, signed.filename);
      toast.success("Report downloaded.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to download report.");
    }
  };

  const handleDelete = async (reportId: string) => {
    if (!projectId) return;
    setActionId(reportId);
    try {
      await reportsApi.delete(projectId, reportId);
      toast.success("Report deleted.");
      await loadData();
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to delete report.");
    } finally {
      setActionId(null);
    }
  };

  return (
    <DashboardShell title="Reports" subtitle="Generate and manage security assessment reports.">
      <ProjectNav projectName={project?.name} active="reports" />

      {canGenerateReport && projectId && (
        <div className="mb-6">
          <button
            type="button"
            onClick={() => setModalOpen(true)}
            className="btn-primary inline-flex items-center gap-2"
          >
            <Sparkles size={16} />
            Generate Report
          </button>
        </div>
      )}

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel p-6"
      >
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-lg font-semibold text-brand-100">Reports library</h2>
          <p className="text-sm text-brand-500">
            {total} report{total === 1 ? "" : "s"}
          </p>
        </div>

        <div className="mb-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => {
              setTypeFilter("");
              setPage(1);
            }}
            className={`rounded-md border px-3 py-1.5 text-sm ${
              typeFilter === ""
                ? "border-brand-400 bg-brand-800/60 text-brand-100"
                : "border-brand-800/50 text-brand-400"
            }`}
          >
            All
          </button>
          {PRIMARY_REPORT_TYPES.map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => {
                setTypeFilter(type);
                setPage(1);
              }}
              className={`rounded-md border px-3 py-1.5 text-sm ${
                typeFilter === type
                  ? "border-brand-400 bg-brand-800/60 text-brand-100"
                  : "border-brand-800/50 text-brand-400"
              }`}
            >
              {REPORT_TYPES.find((item) => item.value === type)?.label ?? type}
            </button>
          ))}
        </div>

        <div className="mb-4 grid gap-3 sm:grid-cols-[1fr_12rem]">
          <input
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
            className="input-field"
            placeholder="Search reports..."
          />
          <select
            value={statusFilter}
            onChange={(event) => {
              setStatusFilter(event.target.value as ReportStatus | "");
              setPage(1);
            }}
            className="input-field"
            aria-label="Filter by status"
          >
            <option value="">All statuses</option>
            <option value="draft">Draft</option>
            <option value="generating">Generating</option>
            <option value="ready">Ready</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        {loading ? (
          <ListSkeleton rows={5} />
        ) : reports.length === 0 ? (
          <EmptyState
            compact
            icon={FileText}
            title={search || typeFilter || statusFilter ? "No matching reports" : "No reports yet"}
            description={
              search || typeFilter || statusFilter
                ? "Adjust your filters."
                : "Generate an Executive or Technical report to get started."
            }
          />
        ) : (
          <>
            <AssetReportsTable
              reports={reports}
              actionId={actionId}
              onGenerate={handleRegenerate}
              onDownload={handleDownload}
              onPreview={setPreviewReport}
              canDelete={canDeleteReport}
              onDelete={handleDelete}
            />
            <div className="mt-6">
              <AssetPagination
                page={page}
                limit={limit}
                total={total}
                pageSizeOptions={[20, 50]}
                onPageChange={setPage}
                onLimitChange={(nextLimit) => {
                  setLimit(nextLimit);
                  setPage(1);
                }}
              />
            </div>
          </>
        )}
      </motion.div>

      {projectId && (
        <GenerateReportModal
          open={modalOpen}
          onClose={() => setModalOpen(false)}
          projectId={projectId}
          onCreated={() => void loadData()}
        />
      )}

      {previewReport && projectId && (
        <ReportPreviewModal
          open
          onClose={() => setPreviewReport(null)}
          projectId={projectId}
          assetId={previewReport.asset_id ?? undefined}
          reportId={previewReport.id}
          title={previewReport.name}
        />
      )}
    </DashboardShell>
  );
}
