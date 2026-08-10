import { useEffect, useState } from "react";
import { FileText, Loader2, X } from "lucide-react";
import { scansApi } from "@/features/scans/api";
import { assetsApi } from "@/features/assets/api";
import { reportsApi } from "@/features/reports/api";
import { toast } from "@/shared/lib/toast";
import { ApiError } from "@/shared/api/client";
import type { AssetSummary } from "@/shared/types/asset";
import type { ReportSummary, ReportType } from "@/shared/types/report";
import type { ScanSummary } from "@/shared/types/scan";

const STEPS = [
  "Collecting assessment data",
  "Calculating statistics",
  "Generating AI summary",
  "Building report",
  "Creating PDF",
];

interface GenerateReportModalProps {
  open: boolean;
  onClose: () => void;
  projectId: string;
  assetId?: string;
  onCreated?: (report: ReportSummary) => void;
}

export default function GenerateReportModal({
  open,
  onClose,
  projectId,
  assetId: initialAssetId,
  onCreated,
}: GenerateReportModalProps) {
  const [assets, setAssets] = useState<AssetSummary[]>([]);
  const [scans, setScans] = useState<ScanSummary[]>([]);
  const [assetId, setAssetId] = useState(initialAssetId ?? "");
  const [scanId, setScanId] = useState("");
  const [reportType, setReportType] = useState<ReportType>("executive");
  const [loadingMeta, setLoadingMeta] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [stepIndex, setStepIndex] = useState(-1);
  const [createdReport, setCreatedReport] = useState<ReportSummary | null>(null);

  useEffect(() => {
    if (!open) return;
    setCreatedReport(null);
    setStepIndex(-1);
    setAssetId(initialAssetId ?? "");
    setScanId("");
    setReportType("executive");
  }, [open, initialAssetId]);

  useEffect(() => {
    if (!open || !projectId) return;
    let active = true;
    async function loadAssets() {
      setLoadingMeta(true);
      try {
        const response = await assetsApi.list(projectId, { limit: 100 });
        if (!active) return;
        const items = response?.items ?? [];
        setAssets(items);
        if (!initialAssetId && items[0]) setAssetId(items[0].id);
      } catch {
        if (active) setAssets([]);
      } finally {
        if (active) setLoadingMeta(false);
      }
    }
    void loadAssets();
    return () => {
      active = false;
    };
  }, [open, projectId, initialAssetId]);

  useEffect(() => {
    if (!open || !projectId || !assetId) {
      setScans([]);
      return;
    }
    let active = true;
    async function loadScans() {
      try {
        const response = await scansApi.list(projectId, assetId, { limit: 50 });
        if (!active) return;
        const items = response?.items ?? [];
        setScans(items);
        if (items[0]) setScanId(items[0].id);
      } catch {
        if (active) setScans([]);
      }
    }
    void loadScans();
    return () => {
      active = false;
    };
  }, [open, projectId, assetId]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!projectId) return;
    setSubmitting(true);
    setStepIndex(0);
    const timer = window.setInterval(() => {
      setStepIndex((value) => (value < STEPS.length - 1 ? value + 1 : value));
    }, 900);

    try {
      const payload = {
        report_type: reportType,
        scan_id: scanId || undefined,
        generate: true,
      };
      const report = initialAssetId || assetId
        ? await reportsApi.createForAsset(projectId, assetId || initialAssetId!, payload)
        : await reportsApi.create(projectId, {
            ...payload,
            asset_id: assetId || undefined,
          });
      setCreatedReport(report ?? null);
      onCreated?.(report!);
      toast.success("Report generated successfully.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to generate report.");
    } finally {
      window.clearInterval(timer);
      setSubmitting(false);
      setStepIndex(STEPS.length);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <button type="button" className="absolute inset-0 bg-black/70" aria-label="Close" onClick={onClose} />
      <div className="relative z-10 w-full max-w-lg rounded-xl border border-brand-700/50 bg-void-100 p-6 shadow-crt">
        <div className="mb-5 flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="rounded-lg border border-brand-600/40 bg-brand-900/30 p-2 text-brand-300">
              <FileText size={18} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-brand-50">Generate Security Report</h2>
              <p className="text-sm text-brand-500">Executive or technical PDF from scan data</p>
            </div>
          </div>
          <button type="button" onClick={onClose} className="btn-ghost p-2" aria-label="Close modal">
            <X size={18} />
          </button>
        </div>

        {createdReport ? (
          <div className="space-y-4">
            <p className="text-sm text-emerald-400">Report generated successfully.</p>
            <div className="rounded-lg border border-brand-800/50 bg-brand-950/20 p-4 text-sm text-brand-200">
              {createdReport.name}
            </div>
            <div className="flex flex-wrap gap-2">
              <button type="button" className="btn-primary" onClick={onClose}>
                Done
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {!initialAssetId && (
              <label className="block">
                <span className="mb-1 block text-xs font-medium text-brand-500">Asset</span>
                <select
                  className="input-field"
                  value={assetId}
                  onChange={(event) => setAssetId(event.target.value)}
                  disabled={loadingMeta || submitting}
                >
                  {assets.map((asset) => (
                    <option key={asset.id} value={asset.id}>
                      {asset.name}
                    </option>
                  ))}
                </select>
              </label>
            )}

            <label className="block">
              <span className="mb-1 block text-xs font-medium text-brand-500">Scan</span>
              <select
                className="input-field"
                value={scanId}
                onChange={(event) => setScanId(event.target.value)}
                disabled={submitting || scans.length === 0}
              >
                {scans.length === 0 ? (
                  <option value="">No scans available</option>
                ) : (
                  scans.map((scan) => (
                    <option key={scan.id} value={scan.id}>
                      {scan.scan_type} · {scan.status} ·{" "}
                      {scan.created_at
                        ? new Date(scan.created_at).toLocaleString()
                        : "Unknown date"}
                    </option>
                  ))
                )}
              </select>
            </label>

            <fieldset>
              <legend className="mb-2 text-xs font-medium text-brand-500">Report type</legend>
              <div className="grid gap-2 sm:grid-cols-2">
                {(["executive", "technical"] as ReportType[]).map((type) => (
                  <label
                    key={type}
                    className={`flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm ${
                      reportType === type
                        ? "border-brand-500/60 bg-brand-900/40 text-brand-100"
                        : "border-brand-800/50 text-brand-400"
                    }`}
                  >
                    <input
                      type="radio"
                      name="report_type"
                      value={type}
                      checked={reportType === type}
                      onChange={() => setReportType(type)}
                      disabled={submitting}
                    />
                    {type === "executive" ? "Executive" : "Technical"}
                  </label>
                ))}
              </div>
            </fieldset>

            {submitting && (
              <ul className="space-y-2 rounded-lg border border-brand-800/40 bg-brand-950/20 p-3 text-sm">
                {STEPS.map((step, index) => (
                  <li key={step} className="flex items-center gap-2 text-brand-300">
                    {index <= stepIndex ? (
                      <span className="text-emerald-400">✓</span>
                    ) : (
                      <Loader2 size={14} className="animate-spin text-brand-500" />
                    )}
                    {step}
                  </li>
                ))}
              </ul>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className="btn-ghost" onClick={onClose} disabled={submitting}>
                Cancel
              </button>
              <button type="submit" className="btn-primary inline-flex items-center gap-2" disabled={submitting}>
                {submitting && <Loader2 size={16} className="animate-spin" />}
                Generate Report
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
