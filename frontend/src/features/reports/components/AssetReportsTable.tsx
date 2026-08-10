import type { ReportSummary } from "@/shared/types/report";
import { formatRelativeTime } from "@/features/organizations/utils/format";
import { reportTypeLabel, statusClass, statusLabel } from "../utils";
import { Download, Eye, Sparkles, Trash2 } from "lucide-react";

interface AssetReportsTableProps {
  reports: ReportSummary[];
  actionId: string | null;
  onGenerate: (reportId: string) => void;
  onDownload: (report: ReportSummary) => void;
  onPreview: (report: ReportSummary) => void;
  onDelete?: (reportId: string) => void;
  canDelete?: boolean;
  showProject?: boolean;
}

export default function AssetReportsTable({
  reports,
  actionId,
  onGenerate,
  onDownload,
  onPreview,
  onDelete,
  canDelete = false,
  showProject = false,
}: AssetReportsTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[820px] text-left text-sm">
        <thead>
          <tr className="border-b border-brand-800/50 text-xs uppercase tracking-wider text-brand-500">
            <th className="px-3 py-3 font-medium">Type</th>
            {showProject && <th className="px-3 py-3 font-medium">Project</th>}
            <th className="px-3 py-3 font-medium">Report</th>
            <th className="px-3 py-3 font-medium">Status</th>
            <th className="px-3 py-3 font-medium">Generated</th>
            <th className="px-3 py-3 font-medium">By</th>
            <th className="px-3 py-3 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          {reports.map((report) => (
            <tr
              key={report.id}
              className="border-b border-brand-800/30 transition hover:bg-brand-900/20"
            >
              <td className="px-3 py-3 text-brand-200">{reportTypeLabel(report.report_type)}</td>
              {showProject && (
                <td className="px-3 py-3 text-brand-400">{report.project_name ?? "—"}</td>
              )}
              <td className="px-3 py-3">
                <p className="font-medium text-brand-100">{report.name}</p>
                {report.description && (
                  <p className="mt-1 text-xs text-brand-600">{report.description}</p>
                )}
              </td>
              <td className={`px-3 py-3 ${statusClass(report.status)}`}>
                {statusLabel(report.status)}
              </td>
              <td className="px-3 py-3 text-brand-500">
                {report.completed_at
                  ? formatRelativeTime(report.completed_at)
                  : report.created_at
                    ? formatRelativeTime(report.created_at)
                    : "—"}
              </td>
              <td className="px-3 py-3 text-brand-500">
                {report.created_by_name ?? "—"}
              </td>
              <td className="px-3 py-3">
                <div className="flex flex-wrap gap-2">
                  {report.status === "ready" && (
                    <>
                      <button
                        type="button"
                        onClick={() => onPreview(report)}
                        className="btn-ghost inline-flex items-center gap-1 px-2 py-1 text-xs"
                      >
                        <Eye size={12} />
                        Preview
                      </button>
                      <button
                        type="button"
                        onClick={() => onDownload(report)}
                        className="btn-primary inline-flex items-center gap-1 px-2 py-1 text-xs"
                      >
                        <Download size={12} />
                        PDF
                      </button>
                    </>
                  )}
                  {report.status !== "ready" && (
                    <button
                      type="button"
                      disabled={actionId === report.id || report.status === "generating"}
                      onClick={() => onGenerate(report.id)}
                      className="btn-ghost inline-flex items-center gap-1 px-2 py-1 text-xs"
                    >
                      <Sparkles size={12} />
                      Generate
                    </button>
                  )}
                  {canDelete && onDelete && (
                    <button
                      type="button"
                      disabled={actionId === report.id}
                      onClick={() => onDelete(report.id)}
                      className="btn-ghost inline-flex items-center gap-1 px-2 py-1 text-xs text-red-300"
                    >
                      <Trash2 size={12} />
                      Delete
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
