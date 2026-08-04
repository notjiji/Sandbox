export type OrganizationRole =
  | "owner"
  | "admin"
  | "security_analyst"
  | "manager"
  | "viewer";
export type MemberStatus = "active" | "invited" | "suspended" | "pending";

export interface OrganizationSummary {
  id: string;
  name: string;
  slug: string;
  role: OrganizationRole;
  membership_status: MemberStatus;
  is_active: boolean;
}

export interface OrganizationDetail {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  industry?: string | null;
  website?: string | null;
  logo_url?: string | null;
  country?: string | null;
  timezone?: string | null;
  created_by?: string | null;
  is_active: boolean;
}

export interface CreateOrganizationRequest {
  name: string;
  slug?: string;
  description?: string;
  industry?: string;
  website?: string;
  logo_url?: string;
  country?: string;
  timezone?: string;
}

export interface UpdateOrganizationRequest {
  name?: string;
  description?: string;
  industry?: string;
  website?: string;
  logo_url?: string;
  country?: string;
  timezone?: string;
}

export interface OrganizationListData {
  items: OrganizationSummary[];
  total?: number;
}
