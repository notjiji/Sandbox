import { useQuery } from "@tanstack/react-query";
import { assetsApi } from "@/features/assets/api";
import ActivityTimeline from "@/shared/components/activity/ActivityTimeline";
import ErrorState from "@/shared/components/ErrorState";
import { PanelSkeleton } from "@/shared/components/ui/Skeleton";
import type { AlertSummary } from "@/shared/types/monitoring";
import MonitoringAlertsList from "./MonitoringAlertsList";

interface ServerActivityPanelProps {
  projectId: string;
  assetId: string;
  alerts: AlertSummary[];
}

export default function ServerActivityPanel({
  projectId,
  assetId,
  alerts,
}: ServerActivityPanelProps) {
  const query = useQuery({
    queryKey: ["asset-timeline", projectId, assetId],
    queryFn: () => assetsApi.timeline(projectId, assetId, 30),
  });

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <div>
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-brand-500">Alerts</h3>
        <MonitoringAlertsList alerts={alerts} />
      </div>
      <div>
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-brand-500">Activity</h3>
        {query.isLoading ? (
          <PanelSkeleton lines={4} />
        ) : query.isError ? (
          <ErrorState compact onRetry={() => void query.refetch()} />
        ) : (
          <ActivityTimeline
            items={query.data?.items ?? []}
            emptyMessage="No activity recorded for this server yet."
            compact
          />
        )}
      </div>
    </div>
  );
}
