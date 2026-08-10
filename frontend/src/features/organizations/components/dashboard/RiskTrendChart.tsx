import type { RiskTrendPoint } from "@/shared/types/risk";

interface RiskTrendChartProps {
  points: RiskTrendPoint[];
}

export default function RiskTrendChart({ points }: RiskTrendChartProps) {
  if (points.length === 0) {
    return (
      <p className="text-sm text-brand-600">
        Risk history will appear after scans complete.
      </p>
    );
  }

  const maxScore = 100;

  return (
    <div className="-mx-1 overflow-x-auto px-1 pb-1">
      <div className="flex h-36 min-w-[280px] items-end gap-2 sm:min-w-0">
        {points.map((point) => {
          const height = Math.max(8, (point.security_score / maxScore) * 100);
          const barTone =
            point.security_score >= 80
              ? "bg-emerald-500/70"
              : point.security_score >= 60
                ? "bg-amber-500/70"
                : "bg-rose-500/70";

          return (
            <div
              key={point.date}
              className="group flex min-w-[2.5rem] flex-1 flex-col items-center gap-2"
            >
              <div className="relative flex w-full flex-1 items-end">
                <div
                  className={`w-full rounded-t transition-all group-hover:opacity-100 ${barTone}`}
                  style={{ height: `${height}%` }}
                  title={`${point.security_score.toFixed(0)} (${point.grade})`}
                />
              </div>
              <span className="text-[10px] text-brand-600">
                {new Date(point.date).toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                })}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
