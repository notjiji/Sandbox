import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";
import { cn } from "@/shared/lib/utils";

export interface StatTrend {
  value: number;
  label: string;
  /** When true, a decrease is shown as positive (green). */
  invertColors?: boolean;
  decimals?: number;
}

interface StatCardProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  href?: string;
  accent?: "default" | "warning" | "danger";
  suffix?: string;
  trend?: StatTrend;
}

const accentClasses = {
  default: "text-brand-400",
  warning: "text-amber-400",
  danger: "text-rose-400",
};

function formatTrendValue(trend: StatTrend) {
  const decimals = trend.decimals ?? 0;
  const formatted =
    decimals > 0 ? trend.value.toFixed(decimals) : String(Math.round(trend.value));
  if (trend.value > 0) return `+${formatted}`;
  return formatted;
}

function trendTone(trend: StatTrend) {
  if (trend.value === 0) return "text-brand-600";
  const isGood = trend.invertColors ? trend.value < 0 : trend.value > 0;
  return isGood ? "text-emerald-400" : "text-rose-400";
}

export default function StatCard({
  label,
  value,
  icon: Icon,
  href,
  accent = "default",
  suffix,
  trend,
}: StatCardProps) {
  const content = (
    <>
      <div className="flex items-start justify-between gap-3">
        <Icon size={20} className={accentClasses[accent]} />
        {suffix && <span className="text-xs text-brand-600">{suffix}</span>}
      </div>
      <p className="mt-4 text-3xl font-semibold tabular-nums text-brand-50">{value}</p>
      <p className="mt-1 text-sm text-brand-500">{label}</p>
      {trend && trend.value !== 0 && (
        <p className={cn("mt-2 text-xs font-medium", trendTone(trend))}>
          {formatTrendValue(trend)} {trend.label}
        </p>
      )}
    </>
  );

  const className =
    "glass-panel block h-full p-5 transition hover:border-brand-500/40";

  if (href) {
    return (
      <Link to={href} className={className}>
        {content}
      </Link>
    );
  }

  return <div className={className}>{content}</div>;
}

interface SectionPanelProps {
  title: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function SectionPanel({ title, action, children, className = "" }: SectionPanelProps) {
  return (
    <section className={`glass-panel flex flex-col ${className}`}>
      <div className="flex items-center justify-between gap-3 border-b border-brand-800/50 px-5 py-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-brand-300">
          {title}
        </h2>
        {action}
      </div>
      <div className="flex-1 p-5">{children}</div>
    </section>
  );
}
