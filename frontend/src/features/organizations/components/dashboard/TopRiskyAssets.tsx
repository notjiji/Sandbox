import { Link } from "react-router-dom";
import type { DashboardTopAsset } from "@/shared/types/dashboard";
import { cn } from "@/shared/lib/utils";

interface TopRiskyAssetsProps {
  assets: DashboardTopAsset[];
}

function scoreTone(score: number | null) {
  if (score == null) return "text-brand-400";
  if (score >= 80) return "text-emerald-400";
  if (score >= 60) return "text-amber-400";
  return "text-rose-400";
}

export default function TopRiskyAssets({ assets }: TopRiskyAssetsProps) {
  if (assets.length === 0) {
    return <p className="text-sm text-brand-600">Scan assets to rank risk by security score.</p>;
  }

  return (
    <ul className="space-y-2">
      {assets.map((asset) => (
        <li key={asset.asset_id}>
          <Link
            to={`/projects/${asset.project_id}/assets/${asset.asset_id}`}
            className="flex items-center justify-between gap-3 rounded-lg border border-brand-800/40 bg-void-200/20 px-4 py-3 transition hover:border-brand-500/40"
          >
            <span className="min-w-0 truncate text-sm text-brand-100">{asset.asset_name}</span>
            <span className={cn("shrink-0 text-sm font-semibold tabular-nums", scoreTone(asset.score))}>
              {asset.score != null ? asset.score.toFixed(0) : "—"}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
