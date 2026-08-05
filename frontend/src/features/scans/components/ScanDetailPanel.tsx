import { X } from "lucide-react";
import { Link } from "react-router-dom";
import type { ScanSummary } from "@/shared/types/scan";
import { formatRelativeTime } from "@/features/organizations/utils/format";
import {
  formatDuration,
  formatScore,
  profileLabel,
  scanDisplayDate,
  statusClass,
} from "../utils";

interface ScanDetailPanelProps {
  scan: ScanSummary | null;
  loading: boolean;
  projectId: string;
  assetId: string;
  onClose: () => void;
  onDownload: (scanId: string) => void;
}

function lifecycleRows(scan: ScanSummary) {
  const lifecycle = scan.lifecycle ?? {};
  return [
    ["Pending", lifecycle.pending_at],
    ["Queued", lifecycle.queued_at],
    ["Running", lifecycle.running_at],
    ["Completed", lifecycle.completed_at],
    ["Failed", lifecycle.failed_at],
    ["Cancelled", lifecycle.cancelled_at],
  ].filter(([, value]) => value);
}

export default function ScanDetailPanel({
  scan,
  loading,
  projectId,
  assetId,
  onClose,
  onDownload,
}: ScanDetailPanelProps) {
  if (!scan && !loading) return null;

  const metrics = scan?.metrics ?? {};

  return (
    <div className="fixed inset-0 z-[90] flex justify-end">
      <button
        type="button"
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        aria-label="Close scan details"
        onClick={onClose}
      />
      <aside className="relative z-10 flex h-full w-full max-w-xl flex-col border-l border-brand-800/50 bg-void-100 shadow-crt">
        <div className="flex items-center justify-between border-b border-brand-800/50 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-brand-100">Scan details</h2>
            {scan && (
              <p className="text-sm text-brand-500">
                {profileLabel(scan.scan_type)} · {scanDisplayDate(scan)}
              </p>
            )}
          </div>
          <button type="button" onClick={onClose} className="btn-ghost p-2" aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-5">
          {loading ? (
            <p className="text-sm text-brand-500">Loading scan details...</p>
          ) : scan ? (
            <div className="space-y-6">
              <section className="grid grid-cols-2 gap-3">
                <MetricCard label="Status" value={scan.status} className={statusClass(scan.status)} />
                <MetricCard label="Duration" value={formatDuration(metrics.duration_seconds)} />
                <MetricCard
                  label="Risk score"
                  value={
                    metrics.risk_score != null
                      ? `${formatScore(metrics.risk_score)}${metrics.grade ? ` (${metrics.grade})` : ""}`
                      : "—"
                  }
                />
                <MetricCard label="Critical findings" value={String(metrics.critical_count ?? 0)} />
                <MetricCard label="Total findings" value={String(metrics.findings_count ?? 0)} />
              </section>

              <section>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-brand-500">
                  Plugins
                </h3>
                <div className="flex flex-wrap gap-2">
                  {(scan.profile_plugins ?? []).map((plugin) => (
                    <span
                      key={plugin}
                      className="rounded-md border border-brand-800/50 px-2 py-1 text-xs uppercase tracking-wide text-brand-300"
                    >
                      {plugin.replace(/_/g, " ")}
                    </span>
                  ))}
                </div>
              </section>

              <section>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-brand-500">
                  Lifecycle
                </h3>
                <ul className="space-y-2 text-sm">
                  {lifecycleRows(scan).map(([label, value]) => (
                    <li key={label} className="flex justify-between gap-4 text-brand-300">
                      <span>{label}</span>
                      <span className="text-brand-500">
                        {value ? formatRelativeTime(String(value)) : "—"}
                      </span>
                    </li>
                  ))}
                </ul>
              </section>

              {(scan.plugin_runs?.length ?? 0) > 0 && (
                <section>
                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-brand-500">
                    Plugin runs
                  </h3>
                  <ul className="space-y-2">
                    {scan.plugin_runs?.map((run) => (
                      <li
                        key={run.id}
                        className="rounded-lg border border-brand-800/40 bg-void-200/20 px-4 py-3"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <p className="font-medium text-brand-100">
                            {run.plugin_name.replace(/_/g, " ")}
                          </p>
                          <span className="text-xs capitalize text-brand-500">{run.status}</span>
                        </div>
                        <p className="mt-1 text-xs text-brand-600">
                          {run.findings_count ?? 0} findings ·{" "}
                          {formatDuration(run.duration_seconds)}
                        </p>
                        {run.error_message && (
                          <p className="mt-2 text-xs text-red-400">{run.error_message}</p>
                        )}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              <div className="flex flex-wrap gap-3">
                <Link
                  to={`/projects/${projectId}/assets/${assetId}/findings`}
                  className="btn-ghost text-sm"
                >
                  View findings
                </Link>
                {scan.status === "completed" && (
                  <button
                    type="button"
                    onClick={() => onDownload(scan.id)}
                    className="btn-primary text-sm"
                  >
                    Download report
                  </button>
                )}
              </div>
            </div>
          ) : null}
        </div>
      </aside>
    </div>
  );
}

function MetricCard({
  label,
  value,
  className,
}: {
  label: string;
  value: string;
  className?: string;
}) {
  return (
    <div className="rounded-lg border border-brand-800/40 bg-void-200/20 px-4 py-3">
      <p className="text-xs uppercase tracking-wider text-brand-600">{label}</p>
      <p className={className ? `mt-1 font-medium capitalize ${className}` : "mt-1 font-medium text-brand-100"}>
        {value}
      </p>
    </div>
  );
}
