import type { SnapshotSummary } from "@/shared/types/monitoring";
import { formatPercent } from "../utils";

interface Series {
  label: string;
  color: string;
  fill: string;
  values: Array<number | null | undefined>;
}

interface HistoricalMetricChartProps {
  title: string;
  current: string;
  points: SnapshotSummary[];
  series: Series[];
  yMax: number;
  formatTick: (value: number) => string;
  hours?: number;
}

const WIDTH = 640;
const HEIGHT = 200;
const PAD_LEFT = 44;
const PAD_RIGHT = 12;
const PAD_TOP = 10;
const PAD_BOTTOM = 28;

function niceMax(value: number): number {
  if (value <= 0) return 1;
  const exp = 10 ** Math.floor(Math.log10(value));
  const n = value / exp;
  const nice = n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10;
  return nice * exp;
}

function plotX(index: number, count: number): number {
  const inner = WIDTH - PAD_LEFT - PAD_RIGHT;
  if (count <= 1) return PAD_LEFT + inner / 2;
  return PAD_LEFT + (index / (count - 1)) * inner;
}

function plotY(value: number, max: number): number {
  const inner = HEIGHT - PAD_TOP - PAD_BOTTOM;
  const clamped = Math.max(0, Math.min(max, value));
  return PAD_TOP + inner - (clamped / max) * inner;
}

function linePath(values: Array<number | null | undefined>, max: number): string {
  const coords = values
    .map((value, index) => {
      if (value == null) return null;
      return `${plotX(index, values.length).toFixed(1)},${plotY(value, max).toFixed(1)}`;
    })
    .filter((item): item is string => item != null);
  if (coords.length === 0) return "";
  return `M ${coords.join(" L ")}`;
}

function areaPath(values: Array<number | null | undefined>, max: number): string {
  const line = linePath(values, max);
  if (!line) return "";
  const first = values.findIndex((value) => value != null);
  const last = values.length - 1 - [...values].reverse().findIndex((value) => value != null);
  if (first < 0 || last < 0) return "";
  const baseline = plotY(0, max).toFixed(1);
  return `${line} L ${plotX(last, values.length).toFixed(1)},${baseline} L ${plotX(first, values.length).toFixed(1)},${baseline} Z`;
}

function ticks(max: number): number[] {
  return [0, 0.25, 0.5, 0.75, 1].map((ratio) => ratio * max);
}

export function formatBytesPerSec(value?: number | null): string {
  if (value == null) return "—";
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)} MB/s`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)} KB/s`;
  return `${value.toFixed(0)} B/s`;
}

export function percentMax(): number {
  return 100;
}

export function autoMax(values: Array<number | null | undefined>, floor = 1): number {
  const numeric = values.filter((value): value is number => value != null && Number.isFinite(value));
  return niceMax(Math.max(floor, ...numeric, 0));
}

export default function HistoricalMetricChart({
  title,
  current,
  points,
  series,
  yMax,
  formatTick,
  hours = 24,
}: HistoricalMetricChartProps) {
  const max = yMax > 0 ? yMax : 1;
  const yTicks = ticks(max);
  const midHours = Math.max(1, Math.round(hours / 2));

  return (
    <div>
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <h3 className="text-sm font-semibold text-brand-200">{title}</h3>
        <p className="text-lg font-semibold tabular-nums text-brand-50">{current}</p>
      </div>
      {points.length === 0 || series.every((item) => item.values.every((value) => value == null)) ? (
        <p className="text-sm text-brand-600">History will appear after the first heartbeat.</p>
      ) : (
        <>
          <svg
            viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
            className="h-44 w-full"
            role="img"
            aria-label={`${title} history, currently ${current}`}
          >
            {yTicks.map((tick) => {
              const y = plotY(tick, max);
              return (
                <g key={tick}>
                  <line
                    x1={PAD_LEFT}
                    x2={WIDTH - PAD_RIGHT}
                    y1={y}
                    y2={y}
                    stroke="rgb(148 163 184 / 0.18)"
                    strokeWidth="1"
                  />
                  <text
                    x={PAD_LEFT - 6}
                    y={y + 3}
                    textAnchor="end"
                    className="fill-brand-500"
                    fontSize="11"
                  >
                    {formatTick(tick)}
                  </text>
                </g>
              );
            })}
            {series.map((item) => (
              <g key={item.label}>
                <path d={areaPath(item.values, max)} fill={item.fill} />
                <path
                  d={linePath(item.values, max)}
                  fill="none"
                  stroke={item.color}
                  strokeWidth="2"
                  strokeLinejoin="round"
                  strokeLinecap="round"
                />
              </g>
            ))}
            <text x={PAD_LEFT} y={HEIGHT - 8} className="fill-brand-600" fontSize="11">
              {hours}h
            </text>
            <text
              x={(PAD_LEFT + WIDTH - PAD_RIGHT) / 2}
              y={HEIGHT - 8}
              textAnchor="middle"
              className="fill-brand-600"
              fontSize="11"
            >
              {midHours}h
            </text>
            <text x={WIDTH - PAD_RIGHT} y={HEIGHT - 8} textAnchor="end" className="fill-brand-600" fontSize="11">
              now
            </text>
          </svg>
          {series.length > 1 && (
            <div className="mt-2 flex flex-wrap gap-4 text-xs text-brand-500">
              {series.map((item) => (
                <span key={item.label} className="inline-flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full" style={{ background: item.color }} />
                  {item.label}
                </span>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

interface MetricsHistoryChartProps {
  points: SnapshotSummary[];
  hours?: number;
}

export function MetricsHistoryGrid({ points, hours = 24 }: MetricsHistoryChartProps) {
  const cpu = points.map((point) => point.cpu_percent);
  const ram = points.map((point) => point.ram_percent);
  const disk = points.map((point) => point.disk_percent);
  const load = points.map((point) => point.load_1m);
  const rx = points.map((point) => point.network_rx_bytes_sec);
  const tx = points.map((point) => point.network_tx_bytes_sec);
  const last = points[points.length - 1];

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <div className="glass-panel p-5">
        <HistoricalMetricChart
          title="CPU"
          current={formatPercent(last?.cpu_percent)}
          points={points}
          hours={hours}
          yMax={percentMax()}
          formatTick={(value) => `${value.toFixed(0)}%`}
          series={[
            {
              label: "CPU",
              color: "rgb(52 211 153)",
              fill: "rgb(52 211 153 / 0.12)",
              values: cpu,
            },
          ]}
        />
      </div>
      <div className="glass-panel p-5">
        <HistoricalMetricChart
          title="RAM"
          current={formatPercent(last?.ram_percent)}
          points={points}
          hours={hours}
          yMax={percentMax()}
          formatTick={(value) => `${value.toFixed(0)}%`}
          series={[
            {
              label: "RAM",
              color: "rgb(125 211 252)",
              fill: "rgb(125 211 252 / 0.12)",
              values: ram,
            },
          ]}
        />
      </div>
      <div className="glass-panel p-5">
        <HistoricalMetricChart
          title="Disk"
          current={formatPercent(last?.disk_percent)}
          points={points}
          hours={hours}
          yMax={percentMax()}
          formatTick={(value) => `${value.toFixed(0)}%`}
          series={[
            {
              label: "Disk",
              color: "rgb(251 191 36)",
              fill: "rgb(251 191 36 / 0.12)",
              values: disk,
            },
          ]}
        />
      </div>
      <div className="glass-panel p-5">
        <HistoricalMetricChart
          title="Network"
          current={
            last?.network_rx_bytes_sec == null && last?.network_tx_bytes_sec == null
              ? "—"
              : formatBytesPerSec((last?.network_rx_bytes_sec ?? 0) + (last?.network_tx_bytes_sec ?? 0))
          }
          points={points}
          hours={hours}
          yMax={autoMax([...rx, ...tx], 1024)}
          formatTick={formatBytesPerSec}
          series={[
            {
              label: "Receive",
              color: "rgb(167 139 250)",
              fill: "rgb(167 139 250 / 0.12)",
              values: rx,
            },
            {
              label: "Transmit",
              color: "rgb(244 114 182)",
              fill: "rgb(244 114 182 / 0.08)",
              values: tx,
            },
          ]}
        />
      </div>
      <div className="glass-panel p-5">
        <HistoricalMetricChart
          title="Load"
          current={last?.load_1m != null ? last.load_1m.toFixed(2) : "—"}
          points={points}
          hours={hours}
          yMax={autoMax(load, 1)}
          formatTick={(value) => value.toFixed(value >= 10 ? 0 : 1)}
          series={[
            {
              label: "Load 1m",
              color: "rgb(251 146 60)",
              fill: "rgb(251 146 60 / 0.12)",
              values: load,
            },
          ]}
        />
      </div>
    </div>
  );
}
