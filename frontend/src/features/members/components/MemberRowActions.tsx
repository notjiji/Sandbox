import { useEffect, useRef, useState } from "react";
import {
  Ban,
  CheckCircle2,
  Copy,
  Link2,
  Mail,
  MoreHorizontal,
  Pencil,
  Trash2,
} from "lucide-react";
import type { MemberSummary, RoleInfo } from "@/shared/types/member";
import type { OrganizationRole } from "@/shared/types/organization";

interface MemberRowActionsProps {
  member: MemberSummary;
  roles: RoleInfo[];
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

export default function MemberRowActions({
  member,
  roles,
  currentUserId,
  canManage,
  onEditRole,
  onSuspend,
  onReactivate,
  onRemove,
  onResendInvite,
  onCopyInviteLink,
  onRevokeInvite,
}: MemberRowActionsProps) {
  const [open, setOpen] = useState(false);
  const [editingRole, setEditingRole] = useState(false);
  const [busy, setBusy] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const isOwner = member.role === "owner";
  const isSelf = currentUserId && member.user_id === currentUserId;
  const isPending = member.status === "pending" || member.status === "invited";
  const isSuspended = member.status === "suspended";
  const isActive = member.status === "active";

  useEffect(() => {
    if (!open) return undefined;

    function handleClick(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpen(false);
        setEditingRole(false);
      }
    }

    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    try {
      await action();
      setOpen(false);
      setEditingRole(false);
    } finally {
      setBusy(false);
    }
  };

  if (!canManage) {
    return <span className="text-xs text-brand-600">—</span>;
  }

  return (
    <div className="relative" ref={menuRef}>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="btn-ghost inline-flex items-center gap-1 px-2 py-1.5 text-sm"
        aria-label="Member actions"
        disabled={busy}
      >
        <MoreHorizontal size={16} />
        Actions
      </button>

      {open && (
        <div className="absolute right-0 z-20 mt-2 min-w-[12rem] rounded-lg border border-brand-700/60 bg-void-100 py-1 shadow-crt">
          {member.membership_id && !isOwner && !isSelf && (
            <>
              <button
                type="button"
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-brand-200 hover:bg-brand-900/40"
                onClick={() => setEditingRole((value) => !value)}
              >
                <Pencil size={14} />
                Edit role
              </button>
              {editingRole && (
                <div className="border-t border-brand-800/50 px-3 py-2">
                  <select
                    defaultValue={member.role}
                    className="input-field py-1.5 text-sm"
                    onChange={(e) =>
                      void run(() =>
                        onEditRole(member.membership_id!, e.target.value as OrganizationRole),
                      )
                    }
                  >
                    {roles
                      .filter((role) => role.role !== "owner")
                      .map((role) => (
                        <option key={role.role} value={role.role}>
                          {role.role.replace(/_/g, " ")}
                        </option>
                      ))}
                  </select>
                </div>
              )}
            </>
          )}

          {member.membership_id && isActive && !isOwner && !isSelf && (
            <button
              type="button"
              className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-brand-200 hover:bg-brand-900/40"
              onClick={() => void run(() => onSuspend(member.membership_id!))}
            >
              <Ban size={14} />
              Suspend
            </button>
          )}

          {member.membership_id && isSuspended && !isOwner && (
            <button
              type="button"
              className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-brand-200 hover:bg-brand-900/40"
              onClick={() => void run(() => onReactivate(member.membership_id!))}
            >
              <CheckCircle2 size={14} />
              Reactivate
            </button>
          )}

          {member.invite_id && isPending && (
            <>
              <button
                type="button"
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-brand-200 hover:bg-brand-900/40"
                onClick={() => void run(() => onResendInvite(member.invite_id!))}
              >
                <Mail size={14} />
                Resend invitation
              </button>
              <button
                type="button"
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-brand-200 hover:bg-brand-900/40"
                onClick={() => void run(() => onCopyInviteLink(member.invite_id!))}
              >
                <Link2 size={14} />
                Copy invite link
              </button>
              <button
                type="button"
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-amber-300 hover:bg-brand-900/40"
                onClick={() => void run(() => onRevokeInvite(member.invite_id!))}
              >
                <Copy size={14} />
                Revoke invitation
              </button>
            </>
          )}

          {member.membership_id && !isOwner && !isSelf && (isActive || isSuspended) && (
            <button
              type="button"
              className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-rose-300 hover:bg-brand-900/40"
              onClick={() => void run(() => onRemove(member.membership_id!))}
            >
              <Trash2 size={14} />
              Remove
            </button>
          )}
        </div>
      )}
    </div>
  );
}
