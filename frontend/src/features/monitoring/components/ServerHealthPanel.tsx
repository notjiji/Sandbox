import { Link } from "react-router-dom";
import { Activity } from "lucide-react";
import EmptyState from "@/shared/components/EmptyState";
import ErrorState from "@/shared/components/ErrorState";
import { PanelSkeleton } from "@/shared/components/ui/Skeleton";
import type { OrgMonitoringServer } from "@/shared/types/monitoring";
import { useOrganizationMonitoring } from "../hooks";
import {
  agentStatusDotClass,
  agentStatusLabel,
  formatPercent,
  formatUptimeCompact,
} from "../utils";
import SecuritySummaryList from "./SecuritySummaryList";
import { cn } from "@/shared/lib/utils";

function MetricRow({ label, value }: { label: string; value?: number | null }) {
  return (
    <div className="flex items-baseline justify-between gap-4 text-sm">
      <span className="text-brand-500">{label}</span>
      <span className="tabular-nums text-brand-100">{formatPercent(value)}</span>
    </div>
  );
}

function ServerCard({ server }: { server: OrgMonitoringServer }) {
  return (
    <Link
      to={`/projects/${server.project_id}/assets/${server.asset_id}/monitoring`}
      className="block rounded-lg border border-brand-800/40 bg-void-200/20 p-4 transition hover:border-brand-500/40"
    >
      <p className="truncate text-sm font-medium text-brand-50">{server.asset_name}</p>
      <p className="mt-1 flex items-center gap-2 text-sm text-brand-400">
        <span className={cn("h-2 w-2 rounded-full", agentStatusDotClass(server.status))} />
        {agentStatusLabel(server.status)}
      </p>

      <div className="mt-4 space-y-1.5">
        <MetricRow label="CPU" value={server.cpu_percent} />
        <MetricRow label="RAM" value={server.ram_percent} />
        <MetricRow label="Disk" value={server.disk_percent} />
      </div>

      <div className="mt-4 border-t border-brand-800/40 pt-3">
        <p className="text-xs uppercase tracking-wider text-brand-500">Uptime</p>
        <p className="mt-1 text-sm tabular-nums text-brand-100">
          {formatUptimeCompact(server.uptime_seconds)}
        </p>
      </div>

      <div className="mt-4 border-t border-brand-800/40 pt-3">
        <p className="mb-2 text-xs uppercase tracking-wider text-brand-500">Security</p>
        <SecuritySummaryList security={server.security} compact />
      </div>
    </Link>
  );
}

export default function ServerHealthPanel() {
  const query = useOrganizationMonitoring();

  if (query.isLoading) {
    return <PanelSkeleton lines={4} />;
  }

  if (query.isError) {
    return <ErrorState compact onRetry={() => void query.refetch()} />;
  }

  const data = query.data;
  if (!data || data.servers.length === 0) {
    return (
      <EmptyState
        compact
        icon={Activity}
        title="No servers connected"
        description="Enroll a monitoring agent on a server asset to see CPU, RAM, disk, and security posture here."
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        <div>
          <p className="text-2xl font-semibold tabular-nums text-emerald-300">{data.agents_online}</p>
          <p className="text-xs text-brand-500">Online</p>
        </div>
        <div>
          <p className="text-2xl font-semibold tabular-nums text-amber-300">{data.agents_delayed ?? 0}</p>
          <p className="text-xs text-brand-500">Delayed</p>
        </div>
        <div>
          <p className="text-2xl font-semibold tabular-nums text-rose-300">{data.agents_offline}</p>
          <p className="text-xs text-brand-500">Offline</p>
        </div>
        <div>
          <p className="text-2xl font-semibold tabular-nums text-sky-300">{data.agents_pending}</p>
          <p className="text-xs text-brand-500">Pending</p>
        </div>
        <div>
          <p className="text-2xl font-semibold tabular-nums text-brand-50">{data.open_alerts}</p>
          <p className="text-xs text-brand-500">Open alerts</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {data.servers.map((server) => (
          <ServerCard key={server.asset_id} server={server} />
        ))}
      </div>
    </div>
  );
}
