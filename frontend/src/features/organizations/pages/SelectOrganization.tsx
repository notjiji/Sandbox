import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Building2, Plus } from "lucide-react";
import AppShell from "@/shared/layouts/AppShell";
import FormAlert from "@/shared/components/FormAlert";
import FormError from "@/shared/components/FormError";
import { ApiError } from "@/shared/api/client";
import type { ValidationErrors } from "@/shared/types/api";
import type { OrganizationSummary } from "@/shared/types/organization";
import { organizationsApi } from "../api";
import { membersApi } from "@/features/members/api";
import { getActiveOrganizations, getInvitedOrganizations, switchOrganization } from "../org";
import { orgStorage } from "../storage";
import { buildWelcomePath } from "@/shared/lib/welcome";

interface CreateOrgForm {
  name: string;
  description: string;
}

export default function SelectOrganization() {
  const navigate = useNavigate();
  const [organizations, setOrganizations] = useState<OrganizationSummary[]>([]);
  const [invited, setInvited] = useState<OrganizationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [alert, setAlert] = useState("");
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [form, setForm] = useState<CreateOrgForm>({ name: "", description: "" });

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const payload = await organizationsApi.listMine();
        if (!active) return;
        const activeOrgs = getActiveOrganizations(payload);
        const invitedOrgs = getInvitedOrganizations(payload);
        setOrganizations(activeOrgs);
        setInvited(invitedOrgs);

        if (activeOrgs.length === 1 && activeOrgs[0]) {
          orgStorage.setActiveOrgId(activeOrgs[0].id);
          navigate("/dashboard", { replace: true });
        }
      } catch (error) {
        if (active) {
          setAlert(error instanceof ApiError ? error.message : "Unable to load organizations.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [navigate]);

  const handleSelect = async (organizationId: string) => {
    try {
      await switchOrganization(organizationsApi, organizationId);
      navigate("/dashboard");
    } catch (error) {
      setAlert(error instanceof ApiError ? error.message : "Unable to select organization.");
    }
  };

  const handleAcceptInvite = async (organizationId: string) => {
    try {
      await membersApi.acceptInvitation(organizationId);
      const org = invited.find((item) => item.id === organizationId);
      orgStorage.setActiveOrgId(organizationId);
      if (org) {
        navigate(
          buildWelcomePath({
            id: org.id,
            name: org.name,
            slug: org.slug,
            role: org.role,
          }),
        );
      } else {
        navigate("/dashboard");
      }
    } catch (error) {
      setAlert(error instanceof ApiError ? error.message : "Unable to accept invitation.");
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) {
      setErrors({ name: "Organization name is required" });
      return;
    }

    setCreating(true);
    setAlert("");
    try {
      const created = await organizationsApi.create({
          name: form.name.trim(),
          description: form.description.trim() || undefined,
        });
      orgStorage.setActiveOrgId(created.id);
      navigate("/dashboard");
    } catch (error) {
      if (error instanceof ApiError) {
        setAlert(error.message);
      } else {
        setAlert("Unable to create organization.");
      }
    } finally {
      setCreating(false);
    }
  };

  return (
    <AppShell title="Select Organization" subtitle="Choose a workspace or create a new one.">
      {alert && <FormAlert message={alert} />}

      {loading ? (
        <div className="glass-panel animate-pulse p-8">Loading organizations...</div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-panel p-6"
          >
            <h2 className="mb-4 text-xl font-semibold text-brand-100">Your organizations</h2>
            {organizations.length === 0 ? (
              <p className="text-brand-500">No active organizations yet.</p>
            ) : (
              <ul className="space-y-3">
                {organizations.map((org) => (
                  <li key={org.id}>
                    <button
                      type="button"
                      onClick={() => handleSelect(org.id)}
                      className="flex w-full items-center justify-between rounded-lg border border-brand-800/50 px-4 py-3 text-left hover:border-brand-500/50"
                    >
                      <span>
                        <span className="block font-medium text-brand-100">{org.name}</span>
                        <span className="text-sm text-brand-500">{org.role}</span>
                      </span>
                      <Building2 size={18} className="text-brand-400" />
                    </button>
                  </li>
                ))}
              </ul>
            )}

            {invited.length > 0 && (
              <div className="mt-6 border-t border-brand-800/50 pt-6">
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-brand-400">
                  Pending invitations
                </h3>
                <ul className="space-y-3">
                  {invited.map((org) => (
                    <li key={org.id}>
                      <button
                        type="button"
                        onClick={() => handleAcceptInvite(org.id)}
                        className="w-full rounded-lg border border-amber-500/30 bg-amber-950/20 px-4 py-3 text-left hover:border-amber-400/50"
                      >
                        <span className="block font-medium text-brand-100">{org.name}</span>
                        <span className="text-sm text-amber-300">Accept invitation as {org.role}</span>
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
            onSubmit={handleCreate}
            className="glass-panel space-y-4 p-6"
          >
            <h2 className="text-xl font-semibold text-brand-100">Create organization</h2>
            <div>
              <label htmlFor="name" className="terminal-text mb-2 block">
                org_name
              </label>
              <input
                id="name"
                name="name"
                value={form.name}
                onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                className="input-field"
                placeholder="Acme Security"
              />
              <FormError message={errors.name} />
            </div>
            <div>
              <label htmlFor="description" className="terminal-text mb-2 block">
                description
              </label>
              <textarea
                id="description"
                name="description"
                rows={3}
                value={form.description}
                onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
                className="input-field"
                placeholder="Optional description"
              />
            </div>
            <button type="submit" disabled={creating} className="btn-primary inline-flex items-center gap-2">
              <Plus size={18} />
              {creating ? "Creating..." : "Create organization"}
            </button>
          </motion.form>
        </div>
      )}
    </AppShell>
  );
}
