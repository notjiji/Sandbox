import { Download, GitCompare, Play, Square } from "lucide-react";
import type { ScanSummary } from "@/shared/types/scan";
import { cn } from "@/shared/lib/utils";
import {
  formatDuration,
  formatScore,
  profileLabel,
  scanDisplayDate,
  statusClass,
} from "../utils";

interface ScanHistoryTableProps {
  scans: ScanSummary[];
  selectedIds: string[];
  actionId: string | null;
  onToggleSelect: (scanId: string) => void;
  onOpen: (scan: ScanSummary) => void;
  onRun: (scanId: string) => void;
  onCancel: (scanId: string) => void;
  onDownload: (scanId: string) => void;
  onCompare: () => void;
}

export default function ScanHistoryTable({
  scans,
  selectedIds,
  actionId,
  onToggleSelect,
  onOpen,
  onRun,
  onCancel,
  onDownload,
  onCompare,
}: ScanHistoryTableProps) {
  return (
    <div className="overflow-x-auto">
      <div className="mb-3 flex items-center justify-between gap-3">
        <p className="text-sm text-brand-500">{scans.length} scan{scans.length === 1 ? "" : "s"} on this page</p>
        <button
          type="button"
          disabled={selectedIds.length !== 2}
          onClick={onCompare}
          className="btn-ghost inline-flex items-center gap-2 text-sm disabled:opacity-40"
        >
          <GitCompare size={16} />
          Compare scans
        </button>
      </div>

      <table className="w-full min-w-[880px] text-left text-sm">
        <thead>
          <tr className="border-b border-brand-800/50 text-xs uppercase tracking-wider text-brand-500">
            <th className="px-3 py-3 font-medium">Compare</th>
            <th className="px-3 py-3 font-medium">Date</th>
            <th className="px-3 py-3 font-medium">Profile</th>
            <th className="px-3 py-3 font-medium">Duration</th>
            <th className="px-3 py-3 font-medium">Score</th>
            <th className="px-3 py-3 font-medium">Critical</th>
            <th className="px-3 py-3 font-medium">Status</th>
            <th className="px-3 py-3 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          {scans.map((scan) => {
            const metrics = scan.metrics ?? {};
            const selected = selectedIds.includes(scan.id);
            const canRun = scan.status === "pending" || scan.status === "failed";
            const canCancel =
              scan.status === "pending" || scan.status === "queued" || scan.status === "running";

            return (
              <tr
                key={scan.id}
                className={cn(
                  "border-b border-brand-800/30 transition hover:bg-brand-900/20",
                  selected && "bg-brand-900/30",
                )}
              >
                <td className="px-3 py-3">
                  <input
                    type="checkbox"
                    checked={selected}
                    onChange={() => onToggleSelect(scan.id)}
                    aria-label={`Select scan ${profileLabel(scan.scan_type)}`}
                    className="h-4 w-4 rounded border-brand-700 bg-brand-950"
                  />
                </td>
                <td className="px-3 py-3">
                  <button
                    type="button"
                    onClick={() => onOpen(scan)}
                    className="text-left text-brand-100 hover:text-brand-50"
                  >
                    {scanDisplayDate(scan)}
                  </button>
                </td>
                <td className="px-3 py-3 text-brand-200">{profileLabel(scan.scan_type)}</td>
                <td className="px-3 py-3 text-brand-400">
                  {formatDuration(metrics.duration_seconds)}
                </td>
                <td className="px-3 py-3">
                  {metrics.risk_score != null ? (
                    <span className="font-medium text-brand-100">
                      {formatScore(metrics.risk_score)}
                      {metrics.grade ? (
                        <span className="ml-1 text-xs text-brand-500">({metrics.grade})</span>
                      ) : null}
                    </span>
                  ) : (
                    <span className="text-brand-600">—</span>
                  )}
                </td>
                <td className="px-3 py-3">
                  <span
                    className={cn(
                      "font-medium",
                      (metrics.critical_count ?? 0) > 0 ? "text-red-300" : "text-brand-500",
                    )}
                  >
                    {metrics.critical_count ?? 0}
                  </span>
                </td>
                <td className={cn("px-3 py-3 capitalize", statusClass(scan.status))}>
                  {scan.status}
                </td>
                <td className="px-3 py-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      type="button"
                      onClick={() => onOpen(scan)}
                      className="btn-ghost px-2 py-1 text-xs"
                    >
                      Details
                    </button>
                    {canRun && (
                      <button
                        type="button"
                        disabled={actionId === scan.id}
                        onClick={() => onRun(scan.id)}
                        className="btn-primary inline-flex items-center gap-1 px-2 py-1 text-xs"
                      >
                        <Play size={12} />
                        Run
                      </button>
                    )}
                    {canCancel && (
                      <button
                        type="button"
                        disabled={actionId === scan.id}
                        onClick={() => onCancel(scan.id)}
                        className="btn-ghost inline-flex items-center gap-1 px-2 py-1 text-xs"
                      >
                        <Square size={12} />
                        Cancel
                      </button>
                    )}
                    {scan.status === "completed" && (
                      <button
                        type="button"
                        onClick={() => onDownload(scan.id)}
                        className="btn-ghost inline-flex items-center gap-1 px-2 py-1 text-xs"
                      >
                        <Download size={12} />
                        Report
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
