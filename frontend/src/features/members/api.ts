import { apiRequest } from "@/shared/api/client";
import type { ApiEnvelope } from "@/shared/types/api";
import type {
  InviteListData,
  InviteMemberRequest,
  InvitePreview,
  MemberListData,
  MemberSummary,
  RolesListData,
  UpdateMemberRequest,
} from "@/shared/types/member";
import type { MessageResponse } from "@/shared/types/auth";

export const membersApi = {
  listMembers: () =>
    apiRequest<ApiEnvelope<MemberListData>>("/organizations/current/members", { auth: true }),

  listInvites: () =>
    apiRequest<ApiEnvelope<InviteListData>>("/organizations/current/invites", { auth: true }),

  inviteMember: (data: InviteMemberRequest) =>
    apiRequest<ApiEnvelope<MemberSummary>>("/organizations/current/members", {
      method: "POST",
      body: data,
      auth: true,
    }),

  acceptInvitation: (organizationId: string) =>
    apiRequest<ApiEnvelope<MessageResponse>>("/organizations/current/members/accept", {
      method: "POST",
      auth: true,
      organizationId,
    }),

  updateMember: (membershipId: string, data: UpdateMemberRequest) =>
    apiRequest<ApiEnvelope<MemberSummary>>(`/organizations/current/members/${membershipId}`, {
      method: "PATCH",
      body: data,
      auth: true,
    }),

  removeMember: (membershipId: string) =>
    apiRequest<ApiEnvelope<MessageResponse>>(`/organizations/current/members/${membershipId}`, {
      method: "DELETE",
      auth: true,
    }),

  revokeInvite: (inviteId: string) =>
    apiRequest<ApiEnvelope<MessageResponse>>(`/organizations/current/invites/${inviteId}`, {
      method: "DELETE",
      auth: true,
    }),

  previewInvite: (token: string) =>
    apiRequest<ApiEnvelope<InvitePreview>>(`/organizations/invites/${token}`),

  acceptInviteToken: (token: string) =>
    apiRequest<ApiEnvelope<MessageResponse>>(`/organizations/invites/${token}/accept`, {
      method: "POST",
      auth: true,
      organizationId: null,
    }),

  listRoles: () => apiRequest<ApiEnvelope<RolesListData>>("/organizations/roles"),
};
