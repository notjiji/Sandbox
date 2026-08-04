import { motion } from "framer-motion";
import { ShieldAlert, TrendingDown, TrendingUp, Minus } from "lucide-react";
import type { DashboardMetrics } from "@/shared/types/risk";

interface SecurityScoreHeroProps {
  security: DashboardMetrics;
}

function trendIcon(trend: string) {
  if (trend === "improving") return TrendingUp;
  if (trend === "declining") return TrendingDown;
  return Minus;
}

function gradeColor(grade: string | null | undefined): string {
  if (!grade) return "text-brand-400";
  const letter = grade.charAt(0).toUpperCase();
  if (letter === "A" || letter === "B") return "text-emerald-400";
  if (letter === "C" || letter === "D") return "text-amber-400";
  return "text-rose-400";
}

function scoreRingColor(score: number | null | undefined): string {
  if (score == null) return "stroke-brand-700";
  if (score >= 80) return "stroke-emerald-400";
  if (score >= 60) return "stroke-amber-400";
  return "stroke-rose-400";
}

export default function SecurityScoreHero({ security }: SecurityScoreHeroProps) {
  const score = security.overall_security_score;
  const grade = security.organization_grade;
  const TrendIcon = trendIcon(security.trend);
  const circumference = 2 * Math.PI * 54;
  const progress = score != null ? Math.min(100, Math.max(0, score)) / 100 : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel relative overflow-hidden p-6 md:p-8"
    >
      <div className="pointer-events-none absolute -right-8 -top-8 h-40 w-40 rounded-full bg-brand-500/10 blur-3xl" />

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
                className={`transition-all duration-700 ${scoreRingColor(score)}`}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-bold tabular-nums text-brand-50">
                {score != null ? score.toFixed(0) : "—"}
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
            <p className={`mt-2 text-4xl font-bold ${gradeColor(grade)}`}>
              {grade ?? "N/A"}
            </p>
            <p className="mt-1 capitalize text-sm text-brand-500">
              {security.risk_level?.replace(/_/g, " ") ?? "No data yet"}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:gap-6">
          <MetricPill label="Critical" value={security.critical_findings} tone="danger" />
          <MetricPill label="High" value={security.high_findings} tone="warning" />
          <MetricPill label="At risk" value={security.assets_at_risk} />
          <MetricPill label="Unscanned" value={security.unscanned_assets} />
        </div>

        <div className="flex items-center gap-2 rounded-lg border border-brand-800/60 bg-void-200/40 px-4 py-3">
          <TrendIcon size={16} className="text-brand-400" />
          <div>
            <p className="text-xs text-brand-600">Trend</p>
            <p className="text-sm capitalize text-brand-200">{security.trend}</p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function MetricPill({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: number;
  tone?: "default" | "warning" | "danger";
}) {
  const valueClass =
    tone === "danger"
      ? "text-rose-400"
      : tone === "warning"
        ? "text-amber-400"
        : "text-brand-100";

  return (
    <div className="rounded-lg border border-brand-800/50 bg-void-200/30 px-4 py-3 text-center">
      <p className={`text-2xl font-semibold tabular-nums ${valueClass}`}>{value}</p>
      <p className="mt-0.5 text-xs text-brand-600">{label}</p>
    </div>
  );
}
