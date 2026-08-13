import { Link } from "react-router-dom";
import { Bug } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import EmptyState from "@/shared/components/EmptyState";
import ErrorState from "@/shared/components/ErrorState";
import { ListSkeleton } from "@/shared/components/ui/Skeleton";
import { findingsApi } from "@/features/findings/api";
import AssetFindingsTable from "@/features/findings/components/AssetFindingsTable";

interface ServerFindingsPanelProps {
  projectId: string;
  assetId: string;
}

export default function ServerFindingsPanel({ projectId, assetId }: ServerFindingsPanelProps) {
  const query = useQuery({
    queryKey: ["asset-findings", projectId, assetId, "monitoring-tab"],
    queryFn: () =>
      findingsApi.listForAsset(projectId, assetId, {
        status_group: "open",
        sort: "risk_score",
        order: "desc",
        limit: 20,
      }),
  });

  if (query.isLoading) {
    return <ListSkeleton rows={5} />;
  }

  if (query.isError) {
    return <ErrorState compact onRetry={() => void query.refetch()} />;
  }

  const findings = query.data?.items ?? [];
  const total = query.data?.total ?? 0;

  if (findings.length === 0) {
    return (
      <EmptyState
        compact
        icon={Bug}
        title="No open findings"
        description="Security conditions from this agent and from scans will appear here."
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-brand-500">
          {total} open finding{total === 1 ? "" : "s"}
        </p>
        <Link
          to={`/projects/${projectId}/assets/${assetId}/findings`}
          className="text-xs text-brand-400 hover:text-brand-200"
        >
          View all
        </Link>
      </div>
      <AssetFindingsTable findings={findings} />
    </div>
  );
}
