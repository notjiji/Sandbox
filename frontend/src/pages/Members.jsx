import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Mail, UserPlus } from "lucide-react";
import DashboardShell from "../components/DashboardShell";
import FormAlert from "../components/FormAlert";
import FormError from "../components/FormError";
import { orgApi, ApiError } from "../lib/api";

export default function Members() {
  const [members, setMembers] = useState([]);
  const [invites, setInvites] = useState([]);
  const [roles, setRoles] = useState([]);
  const [form, setForm] = useState({ email: "", role: "viewer" });
  const [errors, setErrors] = useState({});
  const [alert, setAlert] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);
  const [inviting, setInviting] = useState(false);

  const loadData = async () => {
    const [membersRes, invitesRes, rolesRes] = await Promise.all([
      orgApi.listMembers(),
      orgApi.listInvites(),
      orgApi.listRoles(),
    ]);
    setMembers(membersRes?.data?.items ?? []);
    setInvites(invitesRes?.data?.items ?? []);
    setRoles(rolesRes?.roles ?? []);
  };

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        await loadData();
      } catch (error) {
        if (active) {
          setAlert(error instanceof ApiError ? error.message : "Unable to load members.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    load();
    return () => {
      active = false;
    };
  }, []);

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!form.email.trim()) {
      setErrors({ email: "Email is required" });
      return;
    }

    setInviting(true);
    setAlert("");
    setSuccess("");
    try {
      await orgApi.inviteMember({
        email: form.email.trim().toLowerCase(),
        role: form.role,
      });
      setSuccess("Invitation sent successfully.");
      setForm({ email: "", role: "viewer" });
      await loadData();
    } catch (error) {
      setAlert(error instanceof ApiError ? error.message : "Unable to send invitation.");
    } finally {
      setInviting(false);
    }
  };

  const handleRevokeInvite = async (inviteId) => {
    try {
      await orgApi.revokeInvite(inviteId);
      setSuccess("Invitation revoked.");
      await loadData();
    } catch (error) {
      setAlert(error instanceof ApiError ? error.message : "Unable to revoke invitation.");
    }
  };

  const handleRemoveMember = async (membershipId) => {
    try {
      await orgApi.removeMember(membershipId);
      setSuccess("Member removed.");
      await loadData();
    } catch (error) {
      setAlert(error instanceof ApiError ? error.message : "Unable to remove member.");
    }
  };

  return (
    <DashboardShell title="Members" subtitle="Manage team access and send invitations.">
      {alert && <FormAlert message={alert} />}
      {success && <FormAlert message={success} variant="success" />}

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass-panel p-6">
          <h2 className="mb-4 text-lg font-semibold text-brand-100">Team members</h2>
          {loading ? (
            <p className="text-brand-500">Loading...</p>
          ) : members.length === 0 ? (
            <p className="text-brand-500">No members yet.</p>
          ) : (
            <ul className="space-y-3">
              {members.map((member) => (
                <li
                  key={member.membership_id}
                  className="flex items-center justify-between rounded-lg border border-brand-800/50 px-4 py-3"
                >
                  <div>
                    <p className="font-medium text-brand-100">
                      {member.first_name} {member.last_name}
                    </p>
                    <p className="text-sm text-brand-500">{member.email}</p>
                    <p className="text-xs uppercase tracking-wide text-brand-600">
                      {member.role} · {member.status}
                    </p>
                  </div>
                  {member.role !== "owner" && member.status === "active" && (
                    <button
                      type="button"
                      onClick={() => handleRemoveMember(member.membership_id)}
                      className="btn-ghost text-sm text-red-300"
                    >
                      Remove
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}

          {invites.length > 0 && (
            <div className="mt-8 border-t border-brand-800/50 pt-6">
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-brand-400">
                Pending email invitations
              </h3>
              <ul className="space-y-3">
                {invites.map((invite) => (
                  <li
                    key={invite.invite_id}
                    className="flex items-center justify-between rounded-lg border border-amber-500/20 px-4 py-3"
                  >
                    <div>
                      <p className="font-medium text-brand-100">{invite.email}</p>
                      <p className="text-sm text-brand-500">{invite.role}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRevokeInvite(invite.invite_id)}
                      className="btn-ghost text-sm"
                    >
                      Revoke
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>

        <motion.form
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          onSubmit={handleInvite}
          className="glass-panel h-fit space-y-4 p-6"
        >
          <h2 className="text-lg font-semibold text-brand-100">Invite member</h2>
          <p className="text-sm text-brand-500">
            Invites work for existing and new users. An email will be sent with a secure link.
          </p>

          <div>
            <label htmlFor="email" className="terminal-text mb-2 block">
              email_addr
            </label>
            <input
              id="email"
              name="email"
              type="email"
              value={form.email}
              onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))}
              className="input-field"
              placeholder="teammate@company.com"
            />
            <FormError message={errors.email} />
          </div>

          <div>
            <label htmlFor="role" className="terminal-text mb-2 block">
              role
            </label>
            <select
              id="role"
              name="role"
              value={form.role}
              onChange={(e) => setForm((prev) => ({ ...prev, role: e.target.value }))}
              className="input-field"
            >
              {roles
                .filter((role) => role.role !== "owner")
                .map((role) => (
                  <option key={role.role} value={role.role}>
                    {role.role}
                  </option>
                ))}
            </select>
          </div>

          <button type="submit" disabled={inviting} className="btn-primary inline-flex w-full items-center justify-center gap-2">
            <UserPlus size={18} />
            {inviting ? "Sending..." : "Send invitation"}
          </button>

          <p className="flex items-start gap-2 text-xs text-brand-600">
            <Mail size={14} className="mt-0.5 shrink-0" />
            Recipients without an account can register using the invite link.
          </p>
        </motion.form>
      </div>
    </DashboardShell>
  );
}
