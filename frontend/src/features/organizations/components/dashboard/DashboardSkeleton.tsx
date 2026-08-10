import { PanelSkeleton, SkeletonLine } from "@/shared/components/ui/Skeleton";

export default function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <PanelSkeleton lines={2} />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <SkeletonLine key={index} className="h-28 rounded-xl" />
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <PanelSkeleton lines={5} />
        <PanelSkeleton lines={5} />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <PanelSkeleton lines={4} />
        <PanelSkeleton lines={4} />
      </div>
    </div>
  );
}
