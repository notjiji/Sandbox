import { cn } from "@/shared/lib/utils";

interface SkeletonProps {
  className?: string;
}

export function SkeletonLine({ className }: SkeletonProps) {
  return <div className={cn("animate-pulse rounded-md bg-brand-900/50", className)} />;
}

export function PanelSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="glass-panel space-y-4 p-6">
      <SkeletonLine className="h-5 w-1/3" />
      {Array.from({ length: lines }).map((_, index) => (
        <SkeletonLine key={index} className="h-12 w-full" />
      ))}
    </div>
  );
}

export function ListSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, index) => (
        <div
          key={index}
          className="flex items-center gap-3 rounded-lg border border-brand-800/40 bg-void-200/20 px-4 py-3"
        >
          <SkeletonLine className="h-10 w-10 shrink-0 rounded-full" />
          <div className="min-w-0 flex-1 space-y-2">
            <SkeletonLine className="h-4 w-2/5" />
            <SkeletonLine className="h-3 w-1/4" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-2">
      <SkeletonLine className="mb-4 h-8 w-full" />
      {Array.from({ length: rows }).map((_, index) => (
        <SkeletonLine key={index} className="h-14 w-full rounded-lg" />
      ))}
    </div>
  );
}
