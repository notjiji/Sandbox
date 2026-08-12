import type { SnapshotSummary } from "@/shared/types/monitoring";

interface MetricsHistoryChartProps {
  points: SnapshotSummary[];
}

function polyline(values: Array<number | null | undefined>, width: number, height: number): string {
  const usable = values.map((value) => (value == null ? 0 : Math.max(0, Math.min(100, value))));
  if (usable.length === 0) return "";
  return usable
    .map((value, index) => {
      const x = usable.length === 1 ? width / 2 : (index / (usable.length - 1)) * width;
      const y = height - (value / 100) * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

export default function MetricsHistoryChart({ points }: MetricsHistoryChartProps) {
  if (points.length === 0) {
    return <p className="text-sm text-brand-600">History will appear after the first heartbeat.</p>;
  }

  const width = 640;
  const height = 140;
  const cpu = polyline(
    points.map((point) => point.cpu_percent),
    width,
    height,
  );
  const ram = polyline(
    points.map((point) => point.ram_percent),
    width,
    height,
  );
  const disk = polyline(
    points.map((point) => point.disk_percent),
    width,
    height,
  );

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} className="h-36 w-full" role="img" aria-label="CPU, RAM, and disk history">
        <polyline fill="none" stroke="rgb(52 211 153 / 0.85)" strokeWidth="2" points={cpu} />
        <polyline fill="none" stroke="rgb(125 211 252 / 0.85)" strokeWidth="2" points={ram} />
        <polyline fill="none" stroke="rgb(251 191 36 / 0.85)" strokeWidth="2" points={disk} />
      </svg>
      <div className="mt-3 flex flex-wrap gap-4 text-xs text-brand-500">
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-400" /> CPU
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-sky-300" /> RAM
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-amber-400" /> Disk
        </span>
      </div>
    </div>
  );
}
