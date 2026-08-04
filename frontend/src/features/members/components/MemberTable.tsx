import MemberAvatar from "./MemberAvatar";
import MemberRowActions from "./MemberRowActions";
import {
  MEMBER_STATUS_LABELS,
  ROLE_LABELS,
  type MemberSummary,
  type RoleInfo,
} from "@/shared/types/member";
import type { OrganizationRole } from "@/shared/types/organization";

function displayName(member: MemberSummary) {
  const name = `${member.first_name ?? ""} ${member.last_name ?? ""}`.trim();
  return name || member.email;
}

function formatDate(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function formatDateTime(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function statusClass(status: string) {
  switch (status) {
    case "active":
      return "bg-emerald-500/20 text-emerald-300";
    case "suspended":
      return "bg-rose-500/20 text-rose-300";
    case "invited":
    case "pending":
      return "bg-amber-500/20 text-amber-300";
    default:
      return "bg-brand-800/40 text-brand-400";
  }
}

interface MemberTableProps {
  members: MemberSummary[];
  roles: RoleInfo[];
  loading: boolean;
  currentUserId?: string | null;
  canManage: boolean;
  onEditRole: (membershipId: string, role: OrganizationRole) => Promise<void>;
  onSuspend: (membershipId: string) => Promise<void>;
  onReactivate: (membershipId: string) => Promise<void>;
  onRemove: (membershipId: string) => Promise<void>;
  onResendInvite: (inviteId: string) => Promise<void>;
  onCopyInviteLink: (inviteId: string) => Promise<void>;
  onRevokeInvite: (inviteId: string) => Promise<void>;
}

export default function MemberTable({
  members,
  roles,
  loading,
  currentUserId,
  canManage,
  onEditRole,
  onSuspend,
  onReactivate,
  onRemove,
  onResendInvite,
  onCopyInviteLink,
  onRevokeInvite,
}: MemberTableProps) {
  if (loading) {
    return <p className="text-brand-500">Loading members...</p>;
  }

  if (members.length === 0) {
    return (
      <p className="rounded-lg border border-brand-800/50 px-4 py-8 text-center text-brand-500">
        No members match your filters.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead>
          <tr className="border-b border-brand-800/60 text-xs uppercase tracking-wider text-brand-500">
            <th className="px-4 py-3 font-medium">Member</th>
            <th className="px-4 py-3 font-medium">Email</th>
            <th className="px-4 py-3 font-medium">Role</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">Last login</th>
            <th className="px-4 py-3 font-medium">Joined</th>
            <th className="px-4 py-3 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {members.map((member) => (
            <tr
              key={member.membership_id ?? member.invite_id ?? member.email}
              className="border-b border-brand-900/60 hover:bg-brand-900/20"
            >
              <td className="px-4 py-3">
                <div className="flex items-center gap-3">
                  <MemberAvatar
                    firstName={member.first_name}
                    lastName={member.last_name}
                    email={member.email}
                  />
                  <span className="font-medium text-brand-100">{displayName(member)}</span>
                </div>
              </td>
              <td className="px-4 py-3 text-brand-400">{member.email}</td>
              <td className="px-4 py-3 capitalize text-brand-300">
                {ROLE_LABELS[member.role] ?? member.role.replace(/_/g, " ")}
              </td>
              <td className="px-4 py-3">
                <span
                  className={`inline-flex rounded-full px-2.5 py-0.5 text-xs ${statusClass(member.status)}`}
                >
                  {MEMBER_STATUS_LABELS[member.status] ?? member.status}
                </span>
              </td>
              <td className="px-4 py-3 text-brand-500">{formatDateTime(member.last_login)}</td>
              <td className="px-4 py-3 text-brand-500">
                {member.joined_at ? formatDate(member.joined_at) : formatDate(member.invited_at)}
              </td>
              <td className="px-4 py-3 text-right">
                <MemberRowActions
                  member={member}
                  roles={roles}
                  currentUserId={currentUserId}
                  canManage={canManage}
                  onEditRole={onEditRole}
                  onSuspend={onSuspend}
                  onReactivate={onReactivate}
                  onRemove={onRemove}
                  onResendInvite={onResendInvite}
                  onCopyInviteLink={onCopyInviteLink}
                  onRevokeInvite={onRevokeInvite}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
