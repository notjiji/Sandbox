import type { ReportSummary } from "@/shared/types/report";
import { formatRelativeTime } from "@/features/organizations/utils/format";
import { reportTypeLabel, statusClass, statusLabel } from "../utils";
import { Download, Sparkles } from "lucide-react";

interface AssetReportsTableProps {
  reports: ReportSummary[];
  actionId: string | null;
  onGenerate: (reportId: string) => void;
  onDownload: (report: ReportSummary) => void;
}

export default function AssetReportsTable({
  reports,
  actionId,
  onGenerate,
  onDownload,
}: AssetReportsTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead>
          <tr className="border-b border-brand-800/50 text-xs uppercase tracking-wider text-brand-500">
            <th className="px-3 py-3 font-medium">Type</th>
            <th className="px-3 py-3 font-medium">Report</th>
            <th className="px-3 py-3 font-medium">Status</th>
            <th className="px-3 py-3 font-medium">Generated</th>
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
                {report.created_at ? formatRelativeTime(report.created_at) : "—"}
              </td>
              <td className="px-3 py-3">
                <div className="flex flex-wrap gap-2">
                  {report.status === "ready" ? (
                    <button
                      type="button"
                      onClick={() => onDownload(report)}
                      className="btn-primary inline-flex items-center gap-1 px-2 py-1 text-xs"
                    >
                      <Download size={12} />
                      PDF
                    </button>
                  ) : (
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
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
