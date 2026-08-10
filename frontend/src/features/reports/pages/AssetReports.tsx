import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { FileText, Sparkles } from "lucide-react";
import AssetAskAiPanel from "@/features/ai/components/AssetAskAiPanel";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import EmptyState from "@/shared/components/EmptyState";
import { ListSkeleton } from "@/shared/components/ui/Skeleton";
import AssetPagination from "@/features/assets/components/AssetPagination";
import { toast } from "@/shared/lib/toast";
import { ApiError } from "@/shared/api/client";
import type { AssetSummary } from "@/shared/types/asset";
import type { ProjectSummary } from "@/shared/types/project";
import type { ReportSummary, ReportType } from "@/shared/types/report";
import { assetsApi } from "@/features/assets/api";
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

export default function AssetReports() {
  const { projectId, assetId } = useParams<{ projectId: string; assetId: string }>();
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [asset, setAsset] = useState<AssetSummary | null>(null);
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(PAGE_SIZE);
  const [typeFilter, setTypeFilter] = useState<ReportType | "">("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [generatingType, setGeneratingType] = useState<ReportType | null>(null);
  const [actionId, setActionId] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [previewReport, setPreviewReport] = useState<ReportSummary | null>(null);
  const { canGenerateReport, canDeleteReport } = useOrganizationRole();

  const loadData = useCallback(async () => {
    if (!projectId || !assetId) return;
    const [projectResponse, assetResponse, reportsResponse] = await Promise.all([
      projectsApi.get(projectId),
      assetsApi.get(projectId, assetId),
      reportsApi.listForAsset(projectId, assetId, {
        page,
        limit,
        report_type: typeFilter || undefined,
        search: search.trim() || undefined,
      }),
    ]);
    setProject(projectResponse ?? null);
    setAsset(assetResponse ?? null);
    setReports(reportsResponse?.items ?? []);
    setTotal(reportsResponse?.total ?? 0);
  }, [assetId, limit, page, projectId, search, typeFilter]);

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

  const handleGenerate = async (reportType: ReportType) => {
    if (!projectId || !assetId) return;
    setGeneratingType(reportType);
    try {
      await reportsApi.createForAsset(projectId, assetId, {
        report_type: reportType,
        generate: true,
      });
      toast.success(`${REPORT_TYPES.find((t) => t.value === reportType)?.label} report generated.`);
      setPage(1);
      await loadData();
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to generate report.");
    } finally {
      setGeneratingType(null);
    }
  };

  const handleRegenerate = async (reportId: string) => {
    if (!projectId || !assetId) return;
    setActionId(reportId);
    try {
      await reportsApi.regenerateForAsset(projectId, assetId, reportId);
      toast.success("Report generation started.");
      await loadData();
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to generate report.");
    } finally {
      setActionId(null);
    }
  };

  const handleDownload = async (report: ReportSummary) => {
    if (!projectId || !assetId) return;
    try {
      const signed = await reportsApi.getDownloadUrlForAsset(projectId, assetId, report.id);
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
    <DashboardShell
      title="Reports"
      subtitle={asset ? `Reports for ${asset.name}` : "Asset reports"}
    >
      <ProjectNav projectName={project?.name} assetName={asset?.name} active="reports" />

      {canGenerateReport && (
        <div className="mb-6 flex flex-wrap gap-3">
          <button type="button" onClick={() => setModalOpen(true)} className="btn-primary inline-flex items-center gap-2">
            <Sparkles size={16} />
            Generate Report
          </button>
          {REPORT_TYPES.filter((type) => type.value === "executive" || type.value === "technical").map((type) => (
            <button
              key={type.value}
              type="button"
              disabled={generatingType === type.value}
              onClick={() => handleGenerate(type.value)}
              className="btn-ghost inline-flex items-center gap-2"
            >
              Quick {type.label}
            </button>
          ))}
        </div>
      )}

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel p-6"
      >
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-lg font-semibold text-brand-100">Report history</h2>
          <p className="text-sm text-brand-500">
            {total} report{total === 1 ? "" : "s"}
          </p>
        </div>

        <div className="mb-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setTypeFilter("")}
            className={`rounded-md border px-3 py-1.5 text-sm ${
              typeFilter === ""
                ? "border-brand-400 bg-brand-800/60 text-brand-100"
                : "border-brand-800/50 text-brand-400"
            }`}
          >
            All
          </button>
          {REPORT_TYPES.map((type) => (
            <button
              key={type.value}
              type="button"
              onClick={() => {
                setTypeFilter(type.value);
                setPage(1);
              }}
              className={`rounded-md border px-3 py-1.5 text-sm ${
                typeFilter === type.value
                  ? "border-brand-400 bg-brand-800/60 text-brand-100"
                  : "border-brand-800/50 text-brand-400"
              }`}
            >
              {type.label}
            </button>
          ))}
        </div>

        <input
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="input-field mb-4"
          placeholder="Search reports..."
        />

        {loading ? (
          <ListSkeleton rows={5} />
        ) : reports.length === 0 ? (
          <EmptyState
            compact
            icon={FileText}
            title={search || typeFilter ? "No matching reports" : "No reports yet"}
            description={
              search || typeFilter
                ? "Adjust your filters."
                : "Generate an Executive, Technical, Weekly, or Monthly report above."
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

      {asset && <AssetAskAiPanel assetName={asset.name} variant="compact" className="mt-6" />}

      {projectId && assetId && (
        <GenerateReportModal
          open={modalOpen}
          onClose={() => setModalOpen(false)}
          projectId={projectId}
          assetId={assetId}
          onCreated={() => void loadData()}
        />
      )}

      {previewReport && projectId && assetId && (
        <ReportPreviewModal
          open
          onClose={() => setPreviewReport(null)}
          projectId={projectId}
          assetId={assetId}
          reportId={previewReport.id}
          title={previewReport.name}
        />
      )}
    </DashboardShell>
  );
}
