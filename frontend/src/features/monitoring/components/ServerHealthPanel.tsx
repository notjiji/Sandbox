import { Link } from "react-router-dom";
import { Activity } from "lucide-react";
import EmptyState from "@/shared/components/EmptyState";
import ErrorState from "@/shared/components/ErrorState";
import { PanelSkeleton } from "@/shared/components/ui/Skeleton";
import type { AgentStatus } from "@/shared/types/monitoring";
import { useOrganizationMonitoring } from "../hooks";
import { agentStatusLabel, formatPercent } from "../utils";
import { cn } from "@/shared/lib/utils";

function statusDot(status: AgentStatus): string {
  if (status === "online") return "bg-emerald-400";
  if (status === "pending") return "bg-amber-400";
  return "bg-rose-400";
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
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div>
          <p className="text-2xl font-semibold tabular-nums text-emerald-300">{data.agents_online}</p>
          <p className="text-xs text-brand-500">Online</p>
        </div>
        <div>
          <p className="text-2xl font-semibold tabular-nums text-rose-300">{data.agents_offline}</p>
          <p className="text-xs text-brand-500">Offline</p>
        </div>
        <div>
          <p className="text-2xl font-semibold tabular-nums text-amber-300">{data.agents_pending}</p>
          <p className="text-xs text-brand-500">Pending</p>
        </div>
        <div>
          <p className="text-2xl font-semibold tabular-nums text-brand-50">{data.open_alerts}</p>
          <p className="text-xs text-brand-500">Open alerts</p>
        </div>
      </div>

      <ul className="space-y-2">
        {data.servers.slice(0, 6).map((server) => (
          <li key={server.asset_id}>
            <Link
              to={`/projects/${server.project_id}/assets/${server.asset_id}/monitoring`}
              className="flex items-center justify-between gap-3 rounded-lg border border-brand-800/40 bg-void-200/20 px-4 py-3 transition hover:border-brand-500/40"
            >
              <div className="min-w-0">
                <p className="truncate text-sm text-brand-100">{server.asset_name}</p>
                <p className="mt-0.5 flex items-center gap-2 text-xs text-brand-500">
                  <span className={cn("h-1.5 w-1.5 rounded-full", statusDot(server.status))} />
                  {agentStatusLabel(server.status)}
                  {server.hostname ? ` · ${server.hostname}` : ""}
                </p>
              </div>
              <div className="shrink-0 text-right text-xs tabular-nums text-brand-400">
                <p>
                  CPU {formatPercent(server.cpu_percent)} · RAM {formatPercent(server.ram_percent)}
                </p>
                <p className="mt-0.5">
                  Disk {formatPercent(server.disk_percent)}
                  {server.open_alerts > 0 ? ` · ${server.open_alerts} alert(s)` : ""}
                </p>
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
