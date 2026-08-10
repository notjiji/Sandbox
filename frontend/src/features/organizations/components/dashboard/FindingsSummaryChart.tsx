import { Link } from "react-router-dom";
import type { SeverityBreakdown } from "@/shared/types/risk";
import { cn } from "@/shared/lib/utils";

interface FindingsSummaryChartProps {
  breakdown: SeverityBreakdown;
  projectId: string | null;
}

const SEVERITIES = [
  { key: "critical" as const, label: "Critical", tone: "bg-rose-500" },
  { key: "high" as const, label: "High", tone: "bg-orange-500" },
  { key: "medium" as const, label: "Medium", tone: "bg-amber-500" },
  { key: "low" as const, label: "Low", tone: "bg-brand-500" },
  { key: "info" as const, label: "Info", tone: "bg-brand-600" },
];

function findingsHref(projectId: string | null, severity: string) {
  if (!projectId) return "/projects";
  return `/projects/${projectId}/findings?severity=${severity}`;
}

export default function FindingsSummaryChart({
  breakdown,
  projectId,
}: FindingsSummaryChartProps) {
  const total = SEVERITIES.reduce((sum, item) => sum + breakdown[item.key], 0);
  const max = Math.max(...SEVERITIES.map((item) => breakdown[item.key]), 1);

  return (
    <div className="space-y-4">
      <div className="-mx-1 overflow-x-auto px-1 pb-1">
        <div className="flex h-36 min-w-[320px] items-end gap-2 sm:min-w-0">
          {SEVERITIES.map((item) => {
            const count = breakdown[item.key];
            const height = total === 0 ? 0 : Math.max(6, (count / max) * 100);
            const href = findingsHref(projectId, item.key);
            return (
              <Link
                key={item.key}
                to={href}
                className="group flex min-w-[3rem] flex-1 flex-col items-center gap-2 transition hover:opacity-90"
                title={`${item.label}: ${count}`}
              >
                <span className="text-xs tabular-nums text-brand-400">{count}</span>
                <div className="flex w-full flex-1 items-end">
                  <div
                    className={cn(
                      "w-full rounded-t transition-all",
                      item.tone,
                      "opacity-80 group-hover:opacity-100",
                    )}
                    style={{ height: `${height}%` }}
                  />
                </div>
                <span className="text-[10px] text-brand-600">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>
      {total === 0 && (
        <p className="text-center text-sm text-brand-600">No open findings</p>
      )}
    </div>
  );
}
