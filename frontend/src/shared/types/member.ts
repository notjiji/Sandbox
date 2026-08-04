import type { OrganizationRole, MemberStatus } from "./organization";

export interface MemberSummary {
  membership_id?: string | null;
  invite_id?: string | null;
  user_id?: string | null;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  role: OrganizationRole;
  status: MemberStatus | string;
  joined_at?: string | null;
  last_login?: string | null;
  invited_at?: string | null;
}

export interface InviteMemberRequest {
  email: string;
  role?: OrganizationRole;
}

export interface UpdateMemberRequest {
  role?: OrganizationRole;
  status?: MemberStatus;
}

export interface PendingInviteSummary {
  invite_id: string;
  email: string;
  role: OrganizationRole;
  status: string;
  invited_at: string;
  expires_at: string;
  membership_id?: string | null;
}

export interface InvitePreview {
  organization_id: string;
  organization_name: string;
  organization_slug: string;
  email: string;
  role: OrganizationRole;
  inviter_name: string;
  expires_at: string;
  user_exists: boolean;
  status: InviteLifecycleStatus;
}

export type InviteLifecycleStatus = "pending" | "accepted" | "expired" | "revoked";

export interface RoleInfo {
  role: OrganizationRole;
  description: string;
  permissions: string[];
}

export interface RolesListData {
  roles: RoleInfo[];
}

export interface MemberListData {
  items: MemberSummary[];
  total: number;
  page: number;
  limit: number;
}

export interface InviteListData {
  items: PendingInviteSummary[];
  total?: number;
}

export interface InviteLinkResponse {
  invite_id: string;
  invite_link: string;
  email: string;
}

export type MemberSortField = "name" | "email" | "role" | "status" | "joined_at" | "last_login";
export type SortOrder = "asc" | "desc";
export type MemberStatusFilter = "" | "active" | "pending" | "suspended";

export interface MemberListQuery {
  page?: number;
  limit?: number;
  search?: string;
  status?: MemberStatusFilter;
  role?: OrganizationRole | "";
  sort?: MemberSortField;
  order?: SortOrder;
}

export interface MemberFiltersState {
  search: string;
  status: MemberStatusFilter;
  role: OrganizationRole | "";
  sort: MemberSortField;
  order: SortOrder;
}

export const DEFAULT_MEMBER_FILTERS: MemberFiltersState = {
  search: "",
  status: "",
  role: "",
  sort: "name",
  order: "asc",
};

export const INVITE_STATUS_LABELS: Record<InviteLifecycleStatus, string> = {
  pending: "Pending",
  accepted: "Accepted",
  expired: "Expired",
  revoked: "Revoked",
};

export const MEMBER_STATUS_LABELS: Record<string, string> = {
  active: "Active",
  invited: "Pending",
  pending: "Pending",
  suspended: "Suspended",
};

export const ROLE_LABELS: Record<OrganizationRole, string> = {
  owner: "Owner",
  admin: "Admin",
  security_analyst: "Security Analyst",
  manager: "Manager",
  viewer: "Viewer",
};
