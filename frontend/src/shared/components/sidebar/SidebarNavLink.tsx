import { Link } from "react-router-dom";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/shared/lib/utils";

interface SidebarNavLinkProps {
  to: string;
  label: string;
  icon: LucideIcon;
  active?: boolean;
  collapsed?: boolean;
  disabled?: boolean;
  badge?: string;
  onNavigate?: () => void;
}

export default function SidebarNavLink({
  to,
  label,
  icon: Icon,
  active = false,
  collapsed = false,
  disabled = false,
  badge,
  onNavigate,
}: SidebarNavLinkProps) {
  const className = cn(
    "group flex w-full items-center gap-3 rounded-lg border px-3 py-2.5 text-sm transition-colors",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400/60 focus-visible:ring-offset-2 focus-visible:ring-offset-void",
    active
      ? "border-brand-500/50 bg-brand-900/50 text-brand-50 shadow-glow"
      : "border-transparent text-brand-300 hover:border-brand-700/50 hover:bg-brand-950/60 hover:text-brand-100",
    collapsed && "justify-center px-2",
    disabled && "pointer-events-none opacity-50",
  );

  const content = (
    <>
      <Icon size={18} aria-hidden className="shrink-0" />
      {!collapsed && (
        <>
          <span className="flex-1 truncate font-dyslexic">{label}</span>
          {badge && (
            <span className="rounded border border-brand-600/40 bg-brand-950/80 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-brand-400">
              {badge}
            </span>
          )}
        </>
      )}
    </>
  );

  if (disabled) {
    return (
      <span className={className} aria-disabled="true" title={collapsed ? label : undefined}>
        {content}
      </span>
    );
  }

  return (
    <Link
      to={to}
      className={className}
      aria-current={active ? "page" : undefined}
      title={collapsed ? label : undefined}
      onClick={onNavigate}
    >
      {content}
    </Link>
  );
}
