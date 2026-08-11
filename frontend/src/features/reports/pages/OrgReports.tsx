import { useCallback, useEffect, useState } from "react";
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
import AssetReportsTable from "../components/AssetReportsTable";
import GenerateReportModal from "../components/GenerateReportModal";
import ReportPreviewModal from "../components/ReportPreviewModal";
import { useReportPolling } from "../hooks/useReportPolling";
import { reportsApi } from "../api";
import { REPORT_TYPES } from "../utils";
import { useOrganizationRole } from "@/shared/hooks/useOrganizationRole";

const PAGE_SIZE = 20;
const PRIMARY_REPORT_TYPES: ReportType[] = ["executive", "technical"];

export default function OrgReports() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(PAGE_SIZE);
  const [typeFilter, setTypeFilter] = useState<ReportType | "">("");
  const [statusFilter, setStatusFilter] = useState<ReportStatus | "">("");
  const [projectFilter, setProjectFilter] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalProjectId, setModalProjectId] = useState<string | null>(null);
  const [previewReport, setPreviewReport] = useState<ReportSummary | null>(null);
  const { canGenerateReport, canDeleteReport } = useOrganizationRole();

  const loadData = useCallback(async () => {
    const [projectsResponse, reportsResponse] = await Promise.all([
      projectsApi.list(),
      reportsApi.listForOrganization({
        page,
        limit,
        report_type: typeFilter || undefined,
        status: statusFilter || undefined,
        project_id: projectFilter || undefined,
        search: search.trim() || undefined,
      }),
    ]);
    setProjects(projectsResponse?.items ?? []);
    setReports(reportsResponse?.items ?? []);
    setTotal(reportsResponse?.total ?? 0);
  }, [limit, page, projectFilter, search, statusFilter, typeFilter]);

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

  const handleRegenerate = async (report: ReportSummary) => {
    setActionId(report.id);
    try {
      if (report.asset_id) {
        await reportsApi.regenerateForAsset(report.project_id, report.asset_id, report.id);
      } else {
        await reportsApi.regenerate(report.project_id, report.id);
      }
      toast.success("Report generation started.");
      await loadData();
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to regenerate report.");
    } finally {
      setActionId(null);
    }
  };

  const handleDownload = async (report: ReportSummary) => {
    try {
      const filename = `${report.name.replace(/\s+/g, "-").toLowerCase()}.pdf`;
      if (report.asset_id) {
        await reportsApi.downloadForAsset(report.project_id, report.asset_id, report.id, filename);
      } else {
        await reportsApi.download(report.project_id, report.id, filename);
      }
      toast.success("Report downloaded.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to download report.");
    }
  };

  const handleDelete = async (report: ReportSummary) => {
    setActionId(report.id);
    try {
      await reportsApi.delete(report.project_id, report.id);
      toast.success("Report deleted.");
      await loadData();
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to delete report.");
    } finally {
      setActionId(null);
    }
  };

  const openGenerateModal = () => {
    setModalProjectId(projectFilter || projects[0]?.id || null);
    setModalOpen(true);
  };

  return (
    <DashboardShell
      title="Reports"
      subtitle="Organization-wide security assessment reports across all projects."
    >
      {canGenerateReport && (
        <div className="mb-6">
          <button
            type="button"
            onClick={openGenerateModal}
            className="btn-primary inline-flex items-center gap-2"
            disabled={projects.length === 0}
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

        <div className="mb-4 grid gap-3 sm:grid-cols-[1fr_12rem_12rem]">
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
            value={projectFilter}
            onChange={(event) => {
              setProjectFilter(event.target.value);
              setPage(1);
            }}
            className="input-field"
            aria-label="Filter by project"
          >
            <option value="">All projects</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
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
            title={search || typeFilter || statusFilter || projectFilter ? "No matching reports" : "No reports yet"}
            description={
              search || typeFilter || statusFilter || projectFilter
                ? "Adjust your filters."
                : "Generate an Executive or Technical report to get started."
            }
          />
        ) : (
          <>
            <AssetReportsTable
              reports={reports}
              actionId={actionId}
              onGenerate={(reportId) => {
                const report = reports.find((item) => item.id === reportId);
                if (report) void handleRegenerate(report);
              }}
              onDownload={handleDownload}
              onPreview={setPreviewReport}
              canDelete={canDeleteReport}
              onDelete={(reportId) => {
                const report = reports.find((item) => item.id === reportId);
                if (report) void handleDelete(report);
              }}
              showProject
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

      {modalProjectId && (
        <GenerateReportModal
          open={modalOpen}
          onClose={() => setModalOpen(false)}
          projectId={modalProjectId}
          onCreated={() => void loadData()}
        />
      )}

      {previewReport && (
        <ReportPreviewModal
          open
          onClose={() => setPreviewReport(null)}
          projectId={previewReport.project_id}
          assetId={previewReport.asset_id ?? undefined}
          reportId={previewReport.id}
          title={previewReport.name}
        />
      )}
    </DashboardShell>
  );
}
