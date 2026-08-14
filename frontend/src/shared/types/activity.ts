export type ActivityCategory =
  | "members"
  | "assets"
  | "scans"
  | "reports"
  | "security"
  | "projects"
  | "organization"
  | "findings"
  | "system";

export type AuditSeverity = "info" | "warning" | "error" | "critical";

export interface ActivityActor {
  id?: string | null;
  name: string;
  email?: string | null;
}

export interface ActivityEvent {
  id: string;
  message: string;
  category: ActivityCategory | string;
  action: string;
  actor?: ActivityActor | null;
  resource_type?: string | null;
  resource_id?: string | null;
  severity?: AuditSeverity | string;
  href?: string | null;
  created_at: string;
}

export interface OrganizationActivityData {
  items: ActivityEvent[];
  total: number;
  page: number;
  limit: number;
}

export interface ActivityFilters {
  action?: string;
  actor?: string;
  asset_id?: string;
  severity?: string;
  date_from?: string;
  date_to?: string;
}
