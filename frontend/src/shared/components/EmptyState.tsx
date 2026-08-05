import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/shared/lib/utils";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
  compact?: boolean;
}

export default function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
  compact = false,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-xl border border-dashed border-brand-800/50 bg-void-200/20 text-center",
        compact ? "px-4 py-8" : "px-6 py-12",
        className,
      )}
    >
      {Icon && (
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl border border-brand-700/50 bg-brand-950/50">
          <Icon size={22} className="text-brand-400" />
        </div>
      )}
      <p className="text-base font-medium text-brand-200">{title}</p>
      {description && (
        <p className="mt-2 max-w-sm text-sm text-brand-500">{description}</p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
