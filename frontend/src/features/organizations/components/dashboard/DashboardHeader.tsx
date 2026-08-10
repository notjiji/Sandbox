import { Link } from "react-router-dom";
import { FileText, Radar } from "lucide-react";
import { formatRelativeTime } from "@/features/organizations/utils/format";
import type { DashboardLastScan } from "@/shared/types/dashboard";

interface DashboardHeaderProps {
  lastScan: DashboardLastScan;
  canRunScan: boolean;
  canGenerateReport?: boolean;
  primaryProjectId: string | null;
  onGenerateReport?: () => void;
}

export default function DashboardHeader({
  lastScan,
  canRunScan,
  canGenerateReport = false,
  primaryProjectId,
  onGenerateReport,
}: DashboardHeaderProps) {
  const runScanHref = primaryProjectId ? `/projects/${primaryProjectId}/assets` : "/projects";

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 className="text-xl font-semibold text-brand-50">Security Overview</h2>
        <p className="mt-1 text-sm text-brand-500">
          Last scan:{" "}
          {lastScan.timestamp ? (
            <span className="text-brand-300">{formatRelativeTime(lastScan.timestamp)}</span>
          ) : (
            "No scans yet"
          )}
          {lastScan.asset_name && (
            <span className="text-brand-600"> · {lastScan.asset_name}</span>
          )}
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        {canGenerateReport && primaryProjectId && onGenerateReport && (
          <button type="button" onClick={onGenerateReport} className="btn-ghost inline-flex shrink-0 items-center gap-2">
            <FileText size={16} />
            Generate Report
          </button>
        )}
        {canRunScan && (
          <Link to={runScanHref} className="btn-primary inline-flex shrink-0 items-center gap-2">
            <Radar size={16} />
            Run Scan
          </Link>
        )}
      </div>
    </div>
  );
}
