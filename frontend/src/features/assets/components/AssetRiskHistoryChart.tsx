import type { RiskHistoryPoint } from "@/shared/types/risk-history";

interface AssetRiskHistoryChartProps {
  points: RiskHistoryPoint[];
}

function scoreColor(score: number): string {
  if (score >= 80) return "#34d399";
  if (score >= 60) return "#fbbf24";
  return "#fb7185";
}

export default function AssetRiskHistoryChart({ points }: AssetRiskHistoryChartProps) {
  if (points.length === 0) {
    return (
      <p className="text-sm text-brand-600">
        Risk history will appear after multiple scans complete.
      </p>
    );
  }

  const width = 480;
  const height = 160;
  const padding = { top: 16, right: 12, bottom: 28, left: 32 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;

  const scores = points.map((point) => point.security_score);
  const minScore = Math.max(0, Math.min(...scores) - 8);
  const maxScore = Math.min(100, Math.max(...scores) + 8);
  const range = Math.max(maxScore - minScore, 1);

  const xForIndex = (index: number) =>
    padding.left + (index / Math.max(points.length - 1, 1)) * innerWidth;
  const yForScore = (score: number) =>
    padding.top + innerHeight - ((score - minScore) / range) * innerHeight;

  const linePath = points
    .map((point, index) => {
      const command = index === 0 ? "M" : "L";
      return `${command} ${xForIndex(index)} ${yForScore(point.security_score)}`;
    })
    .join(" ");

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-40 w-full" role="img" aria-label="Risk score trend">
      {[0, 25, 50, 75, 100].filter((tick) => tick >= minScore && tick <= maxScore).map((tick) => (
        <g key={tick}>
          <line
            x1={padding.left}
            x2={width - padding.right}
            y1={yForScore(tick)}
            y2={yForScore(tick)}
            stroke="rgba(120, 130, 160, 0.15)"
          />
          <text
            x={padding.left - 8}
            y={yForScore(tick) + 4}
            textAnchor="end"
            className="fill-brand-600 text-[10px]"
          >
            {tick}
          </text>
        </g>
      ))}

      <path d={linePath} fill="none" stroke="rgba(147, 197, 253, 0.8)" strokeWidth="2.5" />

      {points.map((point, index) => (
        <g key={point.id}>
          <circle
            cx={xForIndex(index)}
            cy={yForScore(point.security_score)}
            r={4}
            fill={scoreColor(point.security_score)}
            stroke="#0f172a"
            strokeWidth={1.5}
          />
          <text
            x={xForIndex(index)}
            y={height - 8}
            textAnchor="middle"
            className="fill-brand-600 text-[10px]"
          >
            {new Date(point.date).toLocaleDateString(undefined, {
              month: "short",
              day: "numeric",
            })}
          </text>
        </g>
      ))}
    </svg>
  );
}

export function RiskScoreTrail({ points }: { points: RiskHistoryPoint[] }) {
  if (points.length === 0) return null;

  const recent = [...points].slice(-5).reverse();

  return (
    <div className="flex flex-wrap items-center gap-2">
      {recent.map((point, index) => (
        <div key={point.id} className="flex items-center gap-2">
          <span
            className="text-2xl font-semibold tabular-nums"
            style={{ color: point.security_score >= 80 ? "#6ee7b7" : point.security_score >= 60 ? "#fcd34d" : "#fda4af" }}
          >
            {point.security_score.toFixed(0)}
          </span>
          {index < recent.length - 1 && (
            <span className="text-brand-600" aria-hidden>
              ↓
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
