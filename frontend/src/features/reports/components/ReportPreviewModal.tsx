import { useEffect, useState } from "react";
import { Loader2, X } from "lucide-react";
import { reportsApi } from "@/features/reports/api";

interface ReportPreviewModalProps {
  open: boolean;
  onClose: () => void;
  projectId: string;
  reportId: string;
  assetId?: string;
  title: string;
}

export default function ReportPreviewModal({
  open,
  onClose,
  projectId,
  reportId,
  assetId,
  title,
}: ReportPreviewModalProps) {
  const [html, setHtml] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    let active = true;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const content = assetId
          ? await reportsApi.previewHtmlForAsset(projectId, assetId, reportId)
          : await reportsApi.previewHtml(projectId, reportId);
        if (active) setHtml(content);
      } catch {
        if (active) setError("Unable to load report preview.");
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, [open, projectId, reportId, assetId]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <button type="button" className="absolute inset-0 bg-black/70" aria-label="Close" onClick={onClose} />
      <div className="relative z-10 flex h-[85vh] w-full max-w-5xl flex-col overflow-hidden rounded-xl border border-brand-700/50 bg-void-100 shadow-crt">
        <div className="flex items-center justify-between border-b border-brand-800/50 px-4 py-3">
          <h2 className="text-sm font-semibold text-brand-100">{title}</h2>
          <button type="button" onClick={onClose} className="btn-ghost p-2" aria-label="Close preview">
            <X size={18} />
          </button>
        </div>
        <div className="flex-1 overflow-hidden bg-white">
          {loading ? (
            <div className="flex h-full items-center justify-center text-brand-500">
              <Loader2 className="animate-spin" size={24} />
            </div>
          ) : error ? (
            <div className="flex h-full items-center justify-center text-red-300">{error}</div>
          ) : (
            <iframe title={title} srcDoc={html} className="h-full w-full border-0 bg-white" />
          )}
        </div>
      </div>
    </div>
  );
}
