import { AlertCircle, RefreshCw } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/shared/lib/utils";

interface ErrorStateProps {
  title?: string;
  description?: ReactNode;
  onRetry?: () => void;
  retryLabel?: string;
  className?: string;
  compact?: boolean;
}

export default function ErrorState({
  title = "Something went wrong",
  description = "We couldn't load this content. Please try again.",
  onRetry,
  retryLabel = "Try again",
  className,
  compact = false,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-xl border border-dashed border-red-500/30 bg-red-950/10 text-center",
        compact ? "px-4 py-8" : "px-6 py-12",
        className,
      )}
      role="alert"
    >
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl border border-red-500/30 bg-red-950/30">
        <AlertCircle size={22} className="text-red-300" />
      </div>
      <p className="text-base font-medium text-red-200">{title}</p>
      {description && (
        <div className="mt-2 max-w-md text-sm text-red-300/80">{description}</div>
      )}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="btn-ghost mt-5 inline-flex items-center gap-2 text-sm text-red-200 hover:text-red-100"
        >
          <RefreshCw size={14} />
          {retryLabel}
        </button>
      )}
    </div>
  );
}
