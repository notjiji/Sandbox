import { X } from "lucide-react";
import type { ScanCompareData } from "@/shared/types/scan";
import {
  formatDuration,
  formatScore,
  profileLabel,
  scanDisplayDate,
  statusClass,
} from "../utils";

interface ScanComparePanelProps {
  data: ScanCompareData | null;
  loading: boolean;
  onClose: () => void;
}

function deltaLabel(value: number | null | undefined, suffix = ""): string {
  if (value == null || Number.isNaN(value)) return "—";
  if (value === 0) return "No change";
  const sign = value > 0 ? "+" : "";
  return `${sign}${typeof value === "number" && !Number.isInteger(value) ? value.toFixed(1) : value}${suffix}`;
}

function deltaClass(value: number, invert = false): string {
  if (value === 0) return "text-brand-500";
  const improved = invert ? value < 0 : value > 0;
  return improved ? "text-emerald-300" : "text-red-300";
}

export default function ScanComparePanel({ data, loading, onClose }: ScanComparePanelProps) {
  if (!data && !loading) return null;

  return (
    <div className="fixed inset-0 z-[95] flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        aria-label="Close compare panel"
        onClick={onClose}
      />
      <div className="relative z-10 max-h-[90vh] w-full max-w-4xl overflow-y-auto glass-panel p-6 shadow-crt">
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-brand-100">Compare scans</h2>
            <p className="mt-1 text-sm text-brand-500">
              Side-by-side comparison of risk, findings, and duration.
            </p>
          </div>
          <button type="button" onClick={onClose} className="btn-ghost p-2" aria-label="Close">
            <X size={18} />
          </button>
        </div>

        {loading ? (
          <p className="text-sm text-brand-500">Loading comparison...</p>
        ) : data ? (
          <div className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <CompareCard title="Scan A" scan={data.scan_a} />
              <CompareCard title="Scan B" scan={data.scan_b} />
            </div>

            <section className="rounded-lg border border-brand-800/40 bg-void-200/20 p-4">
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-brand-500">
                Changes (B vs A)
              </h3>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <DiffItem
                  label="Risk score"
                  value={deltaLabel(data.diff.risk_score_delta)}
                  className={deltaClass(data.diff.risk_score_delta ?? 0, true)}
                />
                <DiffItem
                  label="Critical findings"
                  value={deltaLabel(data.diff.critical_count_delta)}
                  className={deltaClass(-(data.diff.critical_count_delta ?? 0))}
                />
                <DiffItem
                  label="Total findings"
                  value={deltaLabel(data.diff.findings_count_delta)}
                  className={deltaClass(-(data.diff.findings_count_delta ?? 0))}
                />
                <DiffItem
                  label="Duration"
                  value={deltaLabel(data.diff.duration_seconds_delta, "s")}
                  className="text-brand-300"
                />
              </div>
            </section>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function CompareCard({
  title,
  scan,
}: {
  title: string;
  scan: ScanCompareData["scan_a"];
}) {
  const metrics = scan.metrics ?? {};
  return (
    <div className="rounded-lg border border-brand-800/40 bg-void-200/20 p-4">
      <p className="text-xs uppercase tracking-wider text-brand-600">{title}</p>
      <h4 className="mt-1 font-medium text-brand-100">{profileLabel(scan.scan_type)}</h4>
      <p className="text-sm text-brand-500">{scanDisplayDate(scan)}</p>
      <dl className="mt-4 space-y-2 text-sm">
        <Row label="Status" value={scan.status} className={statusClass(scan.status)} />
        <Row label="Duration" value={formatDuration(metrics.duration_seconds)} />
        <Row
          label="Score"
          value={
            metrics.risk_score != null
              ? `${formatScore(metrics.risk_score)}${metrics.grade ? ` (${metrics.grade})` : ""}`
              : "—"
          }
        />
        <Row label="Critical" value={String(metrics.critical_count ?? 0)} />
        <Row label="Findings" value={String(metrics.findings_count ?? 0)} />
      </dl>
    </div>
  );
}

function Row({
  label,
  value,
  className,
}: {
  label: string;
  value: string;
  className?: string;
}) {
  return (
    <div className="flex justify-between gap-3">
      <dt className="text-brand-600">{label}</dt>
      <dd className={className ? `capitalize ${className}` : "text-brand-200"}>{value}</dd>
    </div>
  );
}

function DiffItem({
  label,
  value,
  className,
}: {
  label: string;
  value: string;
  className?: string;
}) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wider text-brand-600">{label}</p>
      <p className={`mt-1 font-medium ${className ?? "text-brand-200"}`}>{value}</p>
    </div>
  );
}
