import { motion } from "framer-motion";
import { ShieldAlert, TrendingDown, TrendingUp, Minus } from "lucide-react";
import StatCard from "./StatCard";
import type { DashboardOverview } from "@/shared/types/dashboard";
import { Layers, Shield } from "lucide-react";

interface SecurityScorePanelProps {
  overview: DashboardOverview;
  assetsHref: string;
  findingsHref: string;
  lastScanHref?: string;
}

function trendIcon(trend: string) {
  if (trend === "improving") return TrendingUp;
  if (trend === "declining") return TrendingDown;
  return Minus;
}

function scoreRingColor(score: number | null | undefined): string {
  if (score == null) return "stroke-brand-700";
  if (score >= 80) return "stroke-emerald-400";
  if (score >= 60) return "stroke-amber-400";
  return "stroke-rose-400";
}

export default function SecurityScorePanel({
  overview,
  assetsHref,
  findingsHref,
  lastScanHref,
}: SecurityScorePanelProps) {
  const { score, assets, findings, last_scan: lastScan } = overview;
  const TrendIcon = trendIcon(score.trend);
  const circumference = 2 * Math.PI * 54;
  const progress =
    score.current != null ? Math.min(100, Math.max(0, score.current)) / 100 : 0;
  const criticalTotal = findings.critical + findings.high;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      <div className="glass-panel relative overflow-hidden p-6 md:p-8">
        <div className="relative flex flex-col gap-8 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-6">
            <div className="relative h-32 w-32 shrink-0">
              <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
                <circle
                  cx="60"
                  cy="60"
                  r="54"
                  fill="none"
                  strokeWidth="8"
                  className="stroke-brand-900/80"
                />
                <circle
                  cx="60"
                  cy="60"
                  r="54"
                  fill="none"
                  strokeWidth="8"
                  strokeLinecap="round"
                  strokeDasharray={circumference}
                  strokeDashoffset={circumference * (1 - progress)}
                  className={`transition-all duration-700 ${scoreRingColor(score.current)}`}
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold tabular-nums text-brand-50">
                  {score.current != null ? score.current.toFixed(0) : "—"}
                </span>
                <span className="text-xs text-brand-500">/ 100</span>
              </div>
            </div>

            <div>
              <div className="flex items-center gap-2 text-brand-400">
                <ShieldAlert size={18} />
                <span className="text-sm font-medium uppercase tracking-wider">
                  Security Score
                </span>
              </div>
              {score.change != null && score.change !== 0 && (
                <p
                  className={`mt-2 text-sm font-medium ${
                    score.change > 0 ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {score.change > 0 ? "↑" : "↓"} {Math.abs(score.change)} points from last scan
                </p>
              )}
              <div className="mt-3 flex items-center gap-2 text-brand-500">
                <TrendIcon size={14} />
                <span className="text-sm capitalize">{score.trend}</span>
                {score.grade && (
                  <span className="rounded border border-brand-700/50 px-2 py-0.5 text-xs text-brand-300">
                    Grade {score.grade}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Security Score"
          value={score.current != null ? score.current.toFixed(0) : "—"}
          icon={Shield}
          suffix="/ 100"
          href={findingsHref}
          trend={
            score.change != null && score.change !== 0
              ? { value: score.change, label: "pts", decimals: 1 }
              : undefined
          }
        />
        <StatCard
          label="Critical Findings"
          value={criticalTotal}
          icon={ShieldAlert}
          href={findingsHref}
          accent={findings.critical > 0 ? "danger" : "default"}
        />
        <StatCard
          label="Assets"
          value={assets.total}
          icon={Layers}
          href={assetsHref}
        />
        <StatCard
          label="Last Scan"
          value={
            lastScan.timestamp
              ? new Date(lastScan.timestamp).toLocaleTimeString(undefined, {
                  hour: "2-digit",
                  minute: "2-digit",
                })
              : "—"
          }
          icon={Shield}
          suffix={lastScan.timestamp ? "local" : undefined}
          href={lastScanHref}
        />
      </div>
    </motion.div>
  );
}
