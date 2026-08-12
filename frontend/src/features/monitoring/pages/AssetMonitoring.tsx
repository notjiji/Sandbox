import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { Activity, Copy, Server } from "lucide-react";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import { SectionPanel } from "@/features/organizations/components/dashboard/StatCard";
import ErrorState from "@/shared/components/ErrorState";
import EmptyState from "@/shared/components/EmptyState";
import { ApiError } from "@/shared/api/client";
import { toast } from "@/shared/lib/toast";
import { useConfirm } from "@/shared/hooks/useConfirm";
import { useOrganizationRole } from "@/shared/hooks/useOrganizationRole";
import { assetsApi } from "@/features/assets/api";
import { projectsApi } from "@/features/projects/api";
import ProjectNav from "@/features/projects/components/ProjectNav";
import { useQuery } from "@tanstack/react-query";
import type { EnrollmentResponse } from "@/shared/types/monitoring";
import { monitoringApi } from "../api";
import { useAssetMonitoring } from "../hooks";
import { monitoringKeys } from "../query-keys";
import {
  MONITORABLE_ASSET_TYPES,
  agentStatusLabel,
  formatPercent,
  formatUptime,
} from "../utils";
import UsageGauge from "../components/UsageGauge";
import MetricsHistoryChart from "../components/MetricsHistoryChart";
import SecurityChecksPanel from "../components/SecurityChecksPanel";
import MonitoringAlertsList from "../components/MonitoringAlertsList";
import { cn } from "@/shared/lib/utils";

function statusClass(status?: string): string {
  if (status === "online") return "border-emerald-500/40 bg-emerald-950/30 text-emerald-200";
  if (status === "pending") return "border-amber-500/40 bg-amber-950/20 text-amber-200";
  if (status === "offline") return "border-rose-500/40 bg-rose-950/20 text-rose-200";
  return "border-brand-700/40 bg-brand-950/20 text-brand-300";
}

export default function AssetMonitoring() {
  const { projectId, assetId } = useParams<{ projectId: string; assetId: string }>();
  const queryClient = useQueryClient();
  const { canManageMonitoring } = useOrganizationRole();
  const { confirm } = useConfirm();
  const [enrollment, setEnrollment] = useState<EnrollmentResponse | null>(null);
  const [busy, setBusy] = useState(false);

  const projectQuery = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => projectsApi.get(projectId!),
    enabled: Boolean(projectId),
  });
  const assetQuery = useQuery({
    queryKey: ["asset", projectId, assetId],
    queryFn: () => assetsApi.get(projectId!, assetId!),
    enabled: Boolean(projectId && assetId),
  });
  const monitoringQuery = useAssetMonitoring(projectId, assetId);

  const asset = assetQuery.data;
  const overview = monitoringQuery.data;
  const monitorable = asset ? MONITORABLE_ASSET_TYPES.has(asset.type) : false;

  const enroll = async () => {
    if (!projectId || !assetId) return;
    setBusy(true);
    try {
      const result = await monitoringApi.enroll(projectId, assetId);
      setEnrollment(result);
      toast.success("Agent enrolled. Copy the token now — it is shown only once.");
      await queryClient.invalidateQueries({ queryKey: monitoringKeys.all });
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to enroll agent.");
    } finally {
      setBusy(false);
    }
  };

  const revoke = async () => {
    if (!projectId || !assetId) return;
    const ok = await confirm({
      title: "Revoke monitoring agent?",
      description: "The current token will stop working immediately. You can enroll again later.",
      confirmLabel: "Revoke",
      destructive: true,
    });
    if (!ok) return;
    setBusy(true);
    try {
      await monitoringApi.revoke(projectId, assetId);
      setEnrollment(null);
      toast.success("Monitoring agent revoked.");
      await queryClient.invalidateQueries({ queryKey: monitoringKeys.all });
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to revoke agent.");
    } finally {
      setBusy(false);
    }
  };

  const copy = async (value: string, label: string) => {
    try {
      await navigator.clipboard.writeText(value);
      toast.success(`${label} copied`);
    } catch {
      toast.error("Unable to copy to clipboard.");
    }
  };

  if (!projectId || !assetId) return null;

  return (
    <DashboardShell
      title="Server monitoring"
      subtitle="Agent-reported health and security posture"
    >
      <ProjectNav
        projectName={projectQuery.data?.name}
        assetName={asset?.name}
        active="monitoring"
      />

      {monitoringQuery.isError ? (
        <ErrorState
          title="Couldn't load monitoring"
          description={
            monitoringQuery.error instanceof ApiError
              ? monitoringQuery.error.message
              : "Unable to load monitoring data."
          }
          onRetry={() => void monitoringQuery.refetch()}
        />
      ) : asset && !monitorable ? (
        <EmptyState
          icon={Server}
          title="Monitoring is for servers"
          description="Enroll an agent on a Linux server, Windows server, or Docker host asset."
        />
      ) : (
        <div className="space-y-6">
          <div className="glass-panel flex flex-col gap-4 p-6 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <span
                  className={cn(
                    "rounded-full border px-3 py-1 text-xs uppercase tracking-wider",
                    statusClass(overview?.agent?.status),
                  )}
                >
                  {overview?.agent ? agentStatusLabel(overview.agent.status) : "Not enrolled"}
                </span>
                {overview?.agent?.agent_version && (
                  <span className="text-xs text-brand-500">v{overview.agent.agent_version}</span>
                )}
              </div>
              <h2 className="text-xl font-semibold text-brand-50">{asset?.name ?? "Server"}</h2>
              <p className="mt-1 text-sm text-brand-400">
                {overview?.agent?.hostname || overview?.security?.system?.hostname || "No heartbeat yet"}
                {overview?.latest?.uptime_seconds != null
                  ? ` · up ${formatUptime(overview.latest.uptime_seconds)}`
                  : ""}
              </p>
            </div>
            {canManageMonitoring && (
              <div className="flex flex-wrap gap-2">
                <button type="button" className="btn-primary" onClick={() => void enroll()} disabled={busy}>
                  {overview?.agent ? "Rotate token" : "Enroll agent"}
                </button>
                {overview?.agent && overview.agent.status !== "revoked" && (
                  <button
                    type="button"
                    className="rounded-lg border border-rose-500/40 px-4 py-2 text-sm text-rose-200 hover:bg-rose-950/30"
                    onClick={() => void revoke()}
                    disabled={busy}
                  >
                    Revoke
                  </button>
                )}
              </div>
            )}
          </div>

          {enrollment && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-950/20 p-5">
              <p className="text-sm font-medium text-amber-100">Save this token now. It will not be shown again.</p>
              <div className="mt-3 flex flex-col gap-2">
                <code className="break-all rounded bg-void-100/80 px-3 py-2 text-xs text-brand-100">
                  {enrollment.token}
                </code>
                <code className="break-all rounded bg-void-100/80 px-3 py-2 text-xs text-brand-100">
                  {enrollment.install_command}
                </code>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="inline-flex items-center gap-2 rounded-lg border border-brand-700/50 px-3 py-1.5 text-xs text-brand-200"
                  onClick={() => void copy(enrollment.token, "Token")}
                >
                  <Copy size={14} /> Copy token
                </button>
                <button
                  type="button"
                  className="inline-flex items-center gap-2 rounded-lg border border-brand-700/50 px-3 py-1.5 text-xs text-brand-200"
                  onClick={() => void copy(enrollment.install_command, "Install command")}
                >
                  <Copy size={14} /> Copy install command
                </button>
              </div>
            </div>
          )}

          {!overview?.agent && !enrollment ? (
            <EmptyState
              icon={Activity}
              title="Connect this server"
              description="The agent runs on the host and sends metrics over HTTPS. The platform never SSHs into the server."
              action={
                canManageMonitoring ? (
                  <button type="button" className="btn-primary" onClick={() => void enroll()} disabled={busy}>
                    Enroll agent
                  </button>
                ) : undefined
              }
            />
          ) : (
            <>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <UsageGauge
                  label="CPU"
                  value={overview?.metrics?.cpu_percent}
                  detail={
                    overview?.metrics?.load_avg?.length
                      ? `load ${overview.metrics.load_avg.map((n) => n.toFixed(2)).join(", ")}`
                      : undefined
                  }
                />
                <UsageGauge
                  label="RAM"
                  value={overview?.metrics?.ram_percent}
                  detail={
                    overview?.metrics?.ram_used_mb != null && overview?.metrics?.ram_total_mb != null
                      ? `${overview.metrics.ram_used_mb.toFixed(0)} / ${overview.metrics.ram_total_mb.toFixed(0)} MB`
                      : undefined
                  }
                />
                <UsageGauge
                  label="Disk"
                  value={overview?.metrics?.disk_percent}
                  detail={
                    overview?.metrics?.disk_used_gb != null && overview?.metrics?.disk_total_gb != null
                      ? `${overview.metrics.disk_used_gb.toFixed(1)} / ${overview.metrics.disk_total_gb.toFixed(1)} GB`
                      : undefined
                  }
                />
              </div>

              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <SectionPanel title="24h history">
                  <MetricsHistoryChart points={overview?.history ?? []} />
                </SectionPanel>
                <SectionPanel title="Security checks">
                  <SecurityChecksPanel security={overview?.security} />
                </SectionPanel>
              </div>

              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <SectionPanel title="Alerts">
                  <MonitoringAlertsList alerts={overview?.alerts ?? []} />
                </SectionPanel>
                <SectionPanel title="Processes">
                  {(overview?.metrics?.processes ?? []).length === 0 ? (
                    <p className="text-sm text-brand-600">Process list will appear after the first heartbeat.</p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-sm">
                        <thead className="text-xs uppercase tracking-wider text-brand-500">
                          <tr>
                            <th className="pb-2">Process</th>
                            <th className="pb-2">User</th>
                            <th className="pb-2 text-right">RSS</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(overview?.metrics?.processes ?? []).map((proc) => (
                            <tr key={`${proc.pid}-${proc.name}`} className="border-t border-brand-800/40">
                              <td className="py-2 text-brand-100">{proc.name || "—"}</td>
                              <td className="py-2 text-brand-400">{proc.user || "—"}</td>
                              <td className="py-2 text-right tabular-nums text-brand-300">
                                {proc.rss_mb != null ? `${proc.rss_mb.toFixed(0)} MB` : "—"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {overview?.metrics?.process_count != null && (
                        <p className="mt-3 text-xs text-brand-600">
                          {overview.metrics.process_count} processes · CPU {formatPercent(overview.metrics.cpu_percent)}
                        </p>
                      )}
                    </div>
                  )}
                </SectionPanel>
              </div>
            </>
          )}
        </div>
      )}
    </DashboardShell>
  );
}
