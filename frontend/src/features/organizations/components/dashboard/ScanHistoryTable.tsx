import { Link } from "react-router-dom";
import type { DashboardScanHistoryItem } from "@/shared/types/dashboard";

interface ScanHistoryTableProps {
  items: DashboardScanHistoryItem[];
}

function formatDuration(seconds: number | null) {
  if (seconds == null) return "—";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}m ${secs}s`;
}

function statusTone(status: string) {
  switch (status) {
    case "completed":
      return "text-emerald-400";
    case "failed":
      return "text-rose-400";
    case "cancelled":
      return "text-amber-400";
    default:
      return "text-brand-400";
  }
}

export default function ScanHistoryTable({ items }: ScanHistoryTableProps) {
  if (!items.length) {
    return (
      <p className="text-sm text-brand-600">
        No scans in this range yet. Run a scan to populate history.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-brand-800/60 text-left text-xs uppercase tracking-wide text-brand-500">
            <th className="px-2 py-2">Scan</th>
            <th className="px-2 py-2">Date</th>
            <th className="px-2 py-2">Asset</th>
            <th className="px-2 py-2">Duration</th>
            <th className="px-2 py-2">Plugins</th>
            <th className="px-2 py-2">Findings</th>
            <th className="px-2 py-2">Score</th>
            <th className="px-2 py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.scan_id} className="border-b border-brand-900/80 text-brand-200">
              <td className="px-2 py-2 font-mono text-xs text-brand-400">{item.scan_id.slice(0, 8)}</td>
              <td className="px-2 py-2 text-xs">
                {new Date(item.date).toLocaleString(undefined, {
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </td>
              <td className="px-2 py-2">
                <Link
                  className="text-brand-300 hover:text-brand-100"
                  to={`/projects/${item.project_id}/assets/${item.asset_id}/scans`}
                >
                  {item.asset_name}
                </Link>
              </td>
              <td className="px-2 py-2">{formatDuration(item.duration_seconds)}</td>
              <td className="px-2 py-2">{item.plugins}</td>
              <td className="px-2 py-2">{item.findings}</td>
              <td className="px-2 py-2">{item.score == null ? "—" : Math.round(item.score)}</td>
              <td className={`px-2 py-2 capitalize ${statusTone(item.status)}`}>{item.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
