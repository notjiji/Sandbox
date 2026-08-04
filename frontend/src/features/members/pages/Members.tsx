import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import Pagination from "@/shared/components/Pagination";
import { ApiError } from "@/shared/api/client";
import type { ValidationErrors } from "@/shared/types/api";
import type { MemberFiltersState, RoleInfo } from "@/shared/types/member";
import { DEFAULT_MEMBER_FILTERS } from "@/shared/types/member";
import type { OrganizationRole } from "@/shared/types/organization";
import { organizationsApi } from "@/features/organizations/api";
import { orgStorage } from "@/features/organizations/storage";
import { usersApi } from "@/features/users/api";
import { membersApi } from "../api";
import InviteMemberForm, { type InviteForm } from "../components/InviteMemberForm";
import MemberFilters from "../components/MemberFilters";
import MemberTable from "../components/MemberTable";
import { useOrganizationMembers } from "../hooks/useOrganizationMembers";

export default function Members() {
  const [roles, setRoles] = useState<RoleInfo[]>([]);
  const [filters, setFilters] = useState<MemberFiltersState>(DEFAULT_MEMBER_FILTERS);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(20);
  const [form, setForm] = useState<InviteForm>({ email: "", role: "viewer" });
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [alert, setAlert] = useState("");
  const [success, setSuccess] = useState("");
  const [inviting, setInviting] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [canManage, setCanManage] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const { members, total, loading, error } = useOrganizationMembers({
    page,
    limit,
    filters,
    reloadToken: refreshKey,
  });

  useEffect(() => {
    let active = true;

    async function loadMeta() {
      try {
        const [rolesRes, orgsRes, profileRes] = await Promise.all([
          membersApi.listRoles(),
          organizationsApi.listMine(),
          usersApi.getMe(),
        ]);
        if (!active) return;
        setRoles(rolesRes?.roles ?? []);
        setCurrentUserId(profileRes?.id ?? null);

        const activeOrgId = orgStorage.getActiveOrgId();
        const currentOrg = orgsRes?.items.find((org) => org.id === activeOrgId);
        if (currentOrg) {
          setCanManage(["owner", "admin"].includes(currentOrg.role));
        }
      } catch {
        if (active) setRoles([]);
      }
    }

    void loadMeta();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    setPage(1);
  }, [filters.search, filters.status, filters.role, filters.sort, filters.order]);

  useEffect(() => {
    if (error) setAlert(error);
  }, [error]);

  const refresh = () => setRefreshKey((value) => value + 1);

  const handleInvite = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!form.email.trim()) {
      setErrors({ email: "Email is required" });
      return;
    }

    setInviting(true);
    setAlert("");
    setSuccess("");
    try {
      await membersApi.inviteMember({
        email: form.email.trim().toLowerCase(),
        role: form.role,
      });
      setSuccess("Invitation sent successfully.");
      setForm({ email: "", role: "viewer" });
      refresh();
    } catch (err) {
      setAlert(err instanceof ApiError ? err.message : "Unable to send invitation.");
    } finally {
      setInviting(false);
    }
  };

  const runAction = async (action: () => Promise<void>, successMessage: string) => {
    setAlert("");
    setSuccess("");
    try {
      await action();
      setSuccess(successMessage);
      refresh();
    } catch (err) {
      setAlert(err instanceof ApiError ? err.message : "Action failed.");
    }
  };

  const handleEditRole = async (membershipId: string, role: OrganizationRole) => {
    await runAction(
      () => membersApi.updateMember(membershipId, { role }).then(() => undefined),
      "Member role updated.",
    );
  };

  const handleSuspend = async (membershipId: string) => {
    await runAction(
      () => membersApi.updateMember(membershipId, { status: "suspended" }).then(() => undefined),
      "Member suspended.",
    );
  };

  const handleReactivate = async (membershipId: string) => {
    await runAction(
      () => membersApi.updateMember(membershipId, { status: "active" }).then(() => undefined),
      "Member reactivated.",
    );
  };

  const handleRemove = async (membershipId: string) => {
    await runAction(
      () => membersApi.removeMember(membershipId).then(() => undefined),
      "Member removed.",
    );
  };

  const handleResendInvite = async (inviteId: string) => {
    await runAction(
      () => membersApi.resendInvite(inviteId, true).then(() => undefined),
      "Invitation resent.",
    );
  };

  const handleCopyInviteLink = async (inviteId: string) => {
    setAlert("");
    setSuccess("");
    try {
      const result = await membersApi.resendInvite(inviteId, false);
      if (result?.invite_link) {
        await navigator.clipboard.writeText(result.invite_link);
        setSuccess("Invite link copied to clipboard.");
      }
    } catch (err) {
      setAlert(err instanceof ApiError ? err.message : "Unable to copy invite link.");
    }
  };

  const handleRevokeInvite = async (inviteId: string) => {
    await runAction(
      () => membersApi.revokeInvite(inviteId).then(() => undefined),
      "Invitation revoked.",
    );
  };

  return (
    <DashboardShell title="Members" subtitle="Manage team access, roles, and invitations.">
      {alert && <FormAlert message={alert} />}
      {success && <FormAlert message={success} variant="success" />}

      <div className="grid gap-6 xl:grid-cols-[1fr_22rem]">
        <div className="space-y-4">
          <MemberFilters filters={filters} roles={roles} onChange={setFilters} />

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-panel overflow-hidden"
          >
            <div className="border-b border-brand-800/50 px-5 py-4">
              <h2 className="text-lg font-semibold text-brand-100">Team members</h2>
              <p className="text-sm text-brand-500">
                {total} member{total === 1 ? "" : "s"} in this organization
              </p>
            </div>

            <div className="p-2 sm:p-4">
              <MemberTable
                members={members}
                roles={roles}
                loading={loading}
                currentUserId={currentUserId}
                canManage={canManage}
                onEditRole={handleEditRole}
                onSuspend={handleSuspend}
                onReactivate={handleReactivate}
                onRemove={handleRemove}
                onResendInvite={handleResendInvite}
                onCopyInviteLink={handleCopyInviteLink}
                onRevokeInvite={handleRevokeInvite}
              />
            </div>

            <div className="border-t border-brand-800/50 px-5 py-4">
              <Pagination
                page={page}
                limit={limit}
                total={total}
                onPageChange={setPage}
                onLimitChange={(nextLimit) => {
                  setLimit(nextLimit);
                  setPage(1);
                }}
              />
            </div>
          </motion.div>
        </div>

        <InviteMemberForm
          form={form}
          roles={roles}
          errors={errors}
          inviting={inviting}
          onChange={setForm}
          onSubmit={handleInvite}
        />
      </div>
    </DashboardShell>
  );
}
