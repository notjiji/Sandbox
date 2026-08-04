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
  href?: string | null;
  created_at: string;
}

export interface OrganizationActivityData {
  items: ActivityEvent[];
  total: number;
  page: number;
  limit: number;
}
