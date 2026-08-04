import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";

interface StatCardProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  href?: string;
  accent?: "default" | "warning" | "danger";
  suffix?: string;
}

const accentClasses = {
  default: "text-brand-400",
  warning: "text-amber-400",
  danger: "text-rose-400",
};

export default function StatCard({
  label,
  value,
  icon: Icon,
  href,
  accent = "default",
  suffix,
}: StatCardProps) {
  const content = (
    <>
      <div className="flex items-start justify-between gap-3">
        <Icon size={20} className={accentClasses[accent]} />
        {suffix && <span className="text-xs text-brand-600">{suffix}</span>}
      </div>
      <p className="mt-4 text-3xl font-semibold tabular-nums text-brand-50">{value}</p>
      <p className="mt-1 text-sm text-brand-500">{label}</p>
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
