export type AgentStatus = "pending" | "online" | "offline" | "revoked";
export type AlertSeverity = "critical" | "high" | "medium" | "low" | "info";
export type AlertStatus = "open" | "resolved";

export interface ProcessInfo {
  pid?: number | null;
  name: string;
  cpu?: number | null;
  rss_mb?: number | null;
  user?: string | null;
}

export interface DiskFilesystem {
  filesystem: string;
  total_gb?: number | null;
  used_gb?: number | null;
  available_gb?: number | null;
  usage_percent?: number | null;
}

export interface MetricsPayload {
  cpu_usage?: number | null;
  cpu_percent?: number | null;
  load_1m?: number | null;
  load_avg?: number[] | null;
  cores?: number | null;
  total_mb?: number | null;
  used_mb?: number | null;
  available_mb?: number | null;
  usage_percent?: number | null;
  ram_percent?: number | null;
  ram_used_mb?: number | null;
  ram_total_mb?: number | null;
  disks?: DiskFilesystem[];
  disk_percent?: number | null;
  disk_used_gb?: number | null;
  disk_total_gb?: number | null;
  uptime_seconds?: number | null;
  boot_time?: string | null;
  last_reboot_at?: string | null;
  process_count?: number | null;
  processes?: ProcessInfo[];
}

export interface FirewallCheck {
  enabled?: boolean | null;
  backend?: string | null;
  default_incoming?: string | null;
}

export interface SshCheck {
  permit_root_login?: boolean | null;
  password_authentication?: boolean | null;
  port?: number | null;
}

export interface Fail2BanCheck {
  enabled?: boolean | null;
  jails?: string[];
}

export interface DockerCheck {
  installed?: boolean | null;
  running?: boolean | null;
  containers?: number | null;
}

export interface UpdatesCheck {
  available?: number | null;
  security?: number | null;
}

export interface SystemInfo {
  os?: string | null;
  kernel?: string | null;
  arch?: string | null;
  hostname?: string | null;
}

export interface SecurityPayload {
  firewall?: FirewallCheck | null;
  ssh?: SshCheck | null;
  fail2ban?: Fail2BanCheck | null;
  docker?: DockerCheck | null;
  updates?: UpdatesCheck | null;
  system?: SystemInfo | null;
}

export interface AgentSummary {
  id: string;
  asset_id: string;
  asset_name?: string | null;
  project_id: string;
  status: AgentStatus;
  hostname?: string | null;
  agent_version?: string | null;
  last_seen_at?: string | null;
  enrolled_at?: string | null;
}

export interface SnapshotSummary {
  collected_at: string;
  cpu_percent?: number | null;
  ram_percent?: number | null;
  disk_percent?: number | null;
  uptime_seconds?: number | null;
  process_count?: number | null;
}

export interface AlertSummary {
  id: string;
  alert_code: string;
  title: string;
  message?: string | null;
  evidence?: string | null;
  severity: AlertSeverity;
  status: AlertStatus;
  first_seen_at: string;
  last_seen_at: string;
  resolved_at?: string | null;
}

export interface MonitoringOverview {
  agent?: AgentSummary | null;
  latest?: SnapshotSummary | null;
  metrics?: MetricsPayload | null;
  security?: SecurityPayload | null;
  alerts: AlertSummary[];
  history: SnapshotSummary[];
}

export interface EnrollmentResponse {
  agent_id: string;
  asset_id: string;
  enrollment_token: string;
  expires_at: string;
  status: AgentStatus;
  install_command: string;
  python_command: string;
  api_url: string;
}

export interface OrgMonitoringServer {
  asset_id: string;
  asset_name: string;
  project_id: string;
  status: AgentStatus;
  hostname?: string | null;
  cpu_percent?: number | null;
  ram_percent?: number | null;
  disk_percent?: number | null;
  open_alerts: number;
  last_seen_at?: string | null;
}

export interface OrgMonitoringOverview {
  agents_online: number;
  agents_offline: number;
  agents_pending: number;
  open_alerts: number;
  servers: OrgMonitoringServer[];
}
