import type { DashboardFindingTrendPoint } from "@/shared/types/dashboard";

interface FindingTrendChartProps {
  points: DashboardFindingTrendPoint[];
}

const SERIES = [
  { key: "critical" as const, label: "Critical", tone: "bg-rose-500/70" },
  { key: "high" as const, label: "High", tone: "bg-orange-500/70" },
  { key: "medium" as const, label: "Medium", tone: "bg-amber-500/70" },
  { key: "low" as const, label: "Low", tone: "bg-brand-500/70" },
];

export default function FindingTrendChart({ points }: FindingTrendChartProps) {
  if (!points.length) {
    return <p className="text-sm text-brand-600">No open finding trend data in this range.</p>;
  }

  const max = Math.max(
    ...points.flatMap((p) => SERIES.map((s) => p[s.key])),
    1,
  );

  return (
    <div className="space-y-4">
      {SERIES.map((series) => (
        <div key={series.key} className="space-y-1">
          <div className="flex items-center justify-between text-xs text-brand-400">
            <span>{series.label}</span>
            <span>{points[points.length - 1]?.[series.key] ?? 0}</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-brand-900/70">
            <div className="flex h-full">
              {points.map((point, idx) => {
                const widthPct = 100 / points.length;
                const opacity = 0.25 + (point[series.key] / max) * 0.75;
                return (
                  <div
                    key={`${series.key}-${idx}`}
                    className={series.tone}
                    style={{ width: `${widthPct}%`, opacity }}
                    title={`${new Date(point.date).toLocaleDateString()}: ${point[series.key]}`}
                  />
                );
              })}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
