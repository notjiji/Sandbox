import type { OrganizationRole, MemberStatus } from "./organization";

export interface MemberSummary {
  membership_id: string;
  user_id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: OrganizationRole;
  status: MemberStatus;
  joined_at?: string | null;
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
}

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
}

export interface InviteListData {
  items: PendingInviteSummary[];
}
