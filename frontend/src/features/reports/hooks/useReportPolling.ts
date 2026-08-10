import { useEffect } from "react";
import type { ReportSummary } from "@/shared/types/report";

interface UseReportPollingOptions {
  reports: ReportSummary[];
  enabled?: boolean;
  intervalMs?: number;
  onRefresh: () => void | Promise<void>;
}

export function useReportPolling({
  reports,
  enabled = true,
  intervalMs = 3000,
  onRefresh,
}: UseReportPollingOptions) {
  const hasGenerating = reports.some((report) => report.status === "generating");

  useEffect(() => {
    if (!enabled || !hasGenerating) return undefined;
    const timer = window.setInterval(() => {
      void onRefresh();
    }, intervalMs);
    return () => window.clearInterval(timer);
  }, [enabled, hasGenerating, intervalMs, onRefresh]);
}
