import { Link } from "react-router-dom";
import type { DashboardUpcomingScan } from "@/shared/types/dashboard";
import { formatRelativeTime } from "@/features/organizations/utils/format";

interface UpcomingScansPanelProps {
  scans: DashboardUpcomingScan[];
}

export default function UpcomingScansPanel({ scans }: UpcomingScansPanelProps) {
  if (scans.length === 0) {
    return (
      <p className="text-sm text-brand-600">
        No scheduled scans. Enable schedules on asset scan pages.
      </p>
    );
  }

  return (
    <ul className="space-y-3">
      {scans.map((scan) => (
        <li key={scan.schedule_id}>
          <Link
            to={`/projects/${scan.project_id}/assets/${scan.asset_id}/scans`}
            className="flex items-center justify-between gap-3 rounded-lg border border-brand-800/40 bg-void-200/20 px-4 py-3 transition hover:border-brand-500/40"
          >
            <div className="min-w-0">
              <p className="truncate text-sm text-brand-100">{scan.asset_name}</p>
              <p className="text-xs capitalize text-brand-600">
                {scan.scan_type} · {scan.preset.replace(/_/g, " ")}
              </p>
            </div>
            <span className="shrink-0 text-xs text-brand-400">
              {formatRelativeTime(scan.next_run_at)}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
