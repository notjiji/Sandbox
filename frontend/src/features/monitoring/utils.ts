import type {
  AgentStatus,
  AlertSeverity,
  SecurityCheckSummary,
  SecurityPayload,
  ServerSecuritySummary,
} from "@/shared/types/monitoring";

export const MONITORABLE_ASSET_TYPES = new Set(["server", "windows_server", "docker_host"]);

export function formatUptime(seconds?: number | null): string {
  if (seconds == null || seconds < 0) return "—";
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

export function formatUptimeCompact(seconds?: number | null): string {
  if (seconds == null || seconds < 0) return "—";
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days}d ${String(hours).padStart(2, "0")}h`;
  if (hours > 0) return `${hours}h ${String(minutes).padStart(2, "0")}m`;
  return `${minutes}m`;
}

export function formatUptimeDetailed(seconds?: number | null): string {
  if (seconds == null || seconds < 0) return "—";
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days > 0) {
    return `${days} day${days === 1 ? "" : "s"} ${String(hours).padStart(2, "0")}h ${String(minutes).padStart(2, "0")}m`;
  }
  if (hours > 0) {
    return `${hours}h ${String(minutes).padStart(2, "0")}m`;
  }
  return `${minutes}m`;
}

export function formatPercent(value?: number | null): string {
  if (value == null) return "—";
  return `${value.toFixed(0)}%`;
}

export function formatDateTime(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString();
}

export function usageTone(value?: number | null): "default" | "warning" | "danger" | "critical" {
  if (value == null) return "default";
  if (value >= 95) return "critical";
  if (value >= 90) return "danger";
  if (value >= 80) return "warning";
  return "default";
}

export function formatRelativeAge(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  const seconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
  if (seconds < 60) {
    return `${seconds} second${seconds === 1 ? "" : "s"} ago`;
  }
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 48) {
    return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  }
  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

export function heartbeatCaption(status?: AgentStatus | null, lastSeenAt?: string | null): string {
  if (!lastSeenAt) {
    return status === "pending" ? "Waiting for first heartbeat" : "No heartbeat yet";
  }
  const age = formatRelativeAge(lastSeenAt);
  if (status === "offline") return `Last seen: ${age}`;
  return `Last heartbeat: ${age}`;
}

export function agentStatusLabel(status: AgentStatus): string {
  switch (status) {
    case "online":
      return "Online";
    case "delayed":
      return "Delayed";
    case "offline":
      return "Offline";
    case "pending":
      return "Waiting for heartbeat";
    case "revoked":
      return "Revoked";
    default:
      return status;
  }
}

export function agentStatusDotClass(status?: AgentStatus | string | null): string {
  if (status === "online") return "bg-emerald-400";
  if (status === "delayed") return "bg-amber-400";
  if (status === "pending") return "bg-sky-400";
  if (status === "offline") return "bg-rose-400";
  return "bg-brand-500";
}

export function agentStatusBadgeClass(status?: AgentStatus | string | null): string {
  if (status === "online") return "border-emerald-500/40 bg-emerald-950/30 text-emerald-200";
  if (status === "delayed") return "border-amber-500/40 bg-amber-950/20 text-amber-200";
  if (status === "pending") return "border-sky-500/40 bg-sky-950/20 text-sky-200";
  if (status === "offline") return "border-rose-500/40 bg-rose-950/20 text-rose-200";
  return "border-brand-700/40 bg-brand-950/20 text-brand-300";
}

const UNKNOWN_CHECK: SecurityCheckSummary = { status: "unknown" };

function check(status: SecurityCheckSummary["status"], detail?: string | null): SecurityCheckSummary {
  return { status, detail: detail ?? null };
}

export function summarizeSecurity(security?: SecurityPayload | null): ServerSecuritySummary {
  if (!security) {
    return {
      ssh: UNKNOWN_CHECK,
      firewall: UNKNOWN_CHECK,
      fail2ban: UNKNOWN_CHECK,
      updates: UNKNOWN_CHECK,
      docker: UNKNOWN_CHECK,
    };
  }

  const ssh = security.ssh;
  let sshCheck = UNKNOWN_CHECK;
  if (ssh) {
    const protocolLegacy = ssh.protocol != null && String(ssh.protocol).split(",").includes("1");
    sshCheck =
      ssh.permit_root_login === true ||
      ssh.password_authentication === true ||
      ssh.pubkey_authentication === false ||
      protocolLegacy
        ? check("warn")
        : check("ok");
  }

  const firewall = security.firewall;
  let firewallCheck = UNKNOWN_CHECK;
  if (firewall && firewall.enabled != null) {
    firewallCheck = firewall.enabled === false ? check("warn") : check("ok");
  }

  const fail2ban = security.fail2ban;
  let fail2banCheck = UNKNOWN_CHECK;
  if (fail2ban) {
    const running = fail2ban.running ?? fail2ban.enabled;
    if (fail2ban.installed === false || running === false) fail2banCheck = check("warn");
    else if (fail2ban.installed === true && running === true) fail2banCheck = check("ok");
  }

  const updates = security.updates;
  let updatesCheck = UNKNOWN_CHECK;
  if (updates && updates.security != null) {
    updatesCheck = updates.security > 0 ? check("warn", String(updates.security)) : check("ok");
  }

  const docker = security.docker;
  let dockerCheck = UNKNOWN_CHECK;
  if (docker) {
    if (docker.installed === false) dockerCheck = check("ok");
    else if (docker.running === false) dockerCheck = check("warn");
    else if (docker.running === true) dockerCheck = check("ok");
  }

  return {
    ssh: sshCheck,
    firewall: firewallCheck,
    fail2ban: fail2banCheck,
    updates: updatesCheck,
    docker: dockerCheck,
  };
}

export const SECURITY_CHECK_ROWS: { key: keyof ServerSecuritySummary; label: string }[] = [
  { key: "ssh", label: "SSH" },
  { key: "firewall", label: "Firewall" },
  { key: "fail2ban", label: "Fail2Ban" },
  { key: "updates", label: "Updates" },
  { key: "docker", label: "Docker" },
];

export function severityClass(severity: AlertSeverity): string {
  switch (severity) {
    case "critical":
      return "border-rose-500/40 bg-rose-950/30 text-rose-200";
    case "high":
      return "border-orange-500/40 bg-orange-950/20 text-orange-200";
    case "medium":
      return "border-amber-500/40 bg-amber-950/20 text-amber-200";
    case "low":
      return "border-sky-500/40 bg-sky-950/20 text-sky-200";
    default:
      return "border-brand-700/40 bg-brand-950/20 text-brand-300";
  }
}

export function checkLabel(value?: boolean | null, yes = "Yes", no = "No"): string {
  if (value == null) return "Unknown";
  return value ? yes : no;
}

export function metricCpuPercent(metrics?: {
  cpu_usage?: number | null;
  cpu_percent?: number | null;
} | null): number | null | undefined {
  return metrics?.cpu_usage ?? metrics?.cpu_percent;
}

export function metricRamPercent(metrics?: {
  usage_percent?: number | null;
  ram_percent?: number | null;
} | null): number | null | undefined {
  return metrics?.usage_percent ?? metrics?.ram_percent;
}
