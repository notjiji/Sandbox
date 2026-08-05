import type { FindingSummary } from "@/shared/types/finding";
import { severityClass, statusClass, statusLabel } from "../utils";

interface AssetFindingsTableProps {
  findings: FindingSummary[];
}

export default function AssetFindingsTable({ findings }: AssetFindingsTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead>
          <tr className="border-b border-brand-800/50 text-xs uppercase tracking-wider text-brand-500">
            <th className="px-3 py-3 font-medium">Severity</th>
            <th className="px-3 py-3 font-medium">Finding</th>
            <th className="px-3 py-3 font-medium">Status</th>
            <th className="px-3 py-3 font-medium text-right">Risk</th>
          </tr>
        </thead>
        <tbody>
          {findings.map((finding) => (
            <tr
              key={finding.id}
              className="border-b border-brand-800/30 transition hover:bg-brand-900/20"
            >
              <td className="px-3 py-3">
                <span
                  className={`text-xs font-semibold uppercase ${severityClass(finding.severity)}`}
                >
                  {finding.severity}
                </span>
              </td>
              <td className="px-3 py-3">
                <p className="font-medium text-brand-100">{finding.title}</p>
                {finding.description && (
                  <p className="mt-1 line-clamp-2 text-xs text-brand-600">{finding.description}</p>
                )}
              </td>
              <td className="px-3 py-3">
                <span className={`text-sm ${statusClass(finding.status)}`}>
                  {statusLabel(finding.status)}
                </span>
              </td>
              <td className="px-3 py-3 text-right tabular-nums text-brand-300">
                {finding.risk_score != null ? finding.risk_score.toFixed(0) : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
