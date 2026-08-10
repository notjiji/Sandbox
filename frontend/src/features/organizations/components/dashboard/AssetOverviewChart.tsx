import { Link } from "react-router-dom";
import type { DashboardAssetsSummary } from "@/shared/types/dashboard";
import { cn } from "@/shared/lib/utils";

interface AssetOverviewChartProps {
  assets: DashboardAssetsSummary;
  href: string;
}

const SEGMENTS = [
  { key: "websites" as const, label: "Websites", color: "bg-emerald-500" },
  { key: "domains" as const, label: "Domains", color: "bg-sky-500" },
  { key: "ips" as const, label: "Public IPs", color: "bg-violet-500" },
  { key: "servers" as const, label: "Servers", color: "bg-amber-500" },
];

export default function AssetOverviewChart({ assets, href }: AssetOverviewChartProps) {
  const total = assets.total || 1;

  return (
    <Link to={href} className="block space-y-4 transition hover:opacity-95">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-3xl font-semibold tabular-nums text-brand-50">{assets.total}</p>
          <p className="text-sm text-brand-500">Total assets</p>
        </div>
      </div>

      <div className="flex h-3 overflow-hidden rounded-full bg-brand-950/60">
        {SEGMENTS.map((segment) => {
          const count = assets[segment.key];
          if (count === 0) return null;
          const width = (count / total) * 100;
          return (
            <div
              key={segment.key}
              className={cn(segment.color, "h-full opacity-80")}
              style={{ width: `${width}%` }}
              title={`${segment.label}: ${count}`}
            />
          );
        })}
      </div>

      <ul className="grid grid-cols-2 gap-2">
        {SEGMENTS.map((segment) => (
          <li
            key={segment.key}
            className="flex items-center justify-between rounded-lg border border-brand-800/40 bg-void-200/20 px-3 py-2 text-sm"
          >
            <span className="flex items-center gap-2 text-brand-300">
              <span className={cn("h-2 w-2 rounded-full", segment.color)} />
              {segment.label}
            </span>
            <span className="tabular-nums text-brand-100">{assets[segment.key]}</span>
          </li>
        ))}
      </ul>
    </Link>
  );
}
