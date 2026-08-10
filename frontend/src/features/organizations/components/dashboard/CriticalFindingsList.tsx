import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import type { DashboardCriticalFinding } from "@/shared/types/dashboard";
import { cn } from "@/shared/lib/utils";

interface CriticalFindingsListProps {
  findings: DashboardCriticalFinding[];
  projectId: string | null;
}

function severityDot(severity: string) {
  if (severity === "critical") return "bg-rose-400";
  if (severity === "high") return "bg-orange-400";
  return "bg-amber-400";
}

export default function CriticalFindingsList({
  findings,
  projectId,
}: CriticalFindingsListProps) {
  const viewAllHref = projectId
    ? `/projects/${projectId}/findings?severity=critical`
    : "/projects";

  if (findings.length === 0) {
    return <p className="text-sm text-brand-600">No critical or high findings right now.</p>;
  }

  return (
    <div className="space-y-3">
      <ul className="space-y-2">
        {findings.map((finding) => (
          <li key={finding.finding_id}>
            <Link
              to={`/projects/${finding.project_id}/assets/${finding.asset_id}/findings`}
              className="flex items-start gap-3 rounded-lg border border-brand-800/40 bg-void-200/20 px-4 py-3 transition hover:border-brand-500/40"
            >
              <span
                className={cn("mt-1.5 h-2 w-2 shrink-0 rounded-full", severityDot(finding.severity))}
                aria-hidden
              />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm text-brand-100">{finding.title}</p>
                <p className="text-xs text-brand-600">
                  {finding.asset_name} · {finding.severity}
                </p>
              </div>
            </Link>
          </li>
        ))}
      </ul>
      <Link
        to={viewAllHref}
        className="inline-flex items-center gap-1 text-xs text-brand-400 hover:text-brand-200"
      >
        View all findings
        <ChevronRight size={14} />
      </Link>
    </div>
  );
}
