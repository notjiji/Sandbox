import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Archive,
  Bell,
  Palette,
  Save,
  Settings,
  Shield,
  Trash2,
  UserCog,
} from "lucide-react";
import DashboardShell from "../components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import FormError from "@/shared/components/FormError";
import { ApiError } from "@/shared/api/client";
import type { ValidationErrors } from "@/shared/types/api";
import type { OrganizationDetail } from "@/shared/types/organization";
import type {
  NotificationSettings,
  OrganizationSettings,
  SecuritySettings,
} from "@/shared/types/organization-settings";
import {
  LANGUAGE_OPTIONS,
  SESSION_TIMEOUT_OPTIONS,
  TIMEZONE_OPTIONS,
} from "@/shared/types/organization-settings";
import type { MemberSummary } from "@/shared/types/member";
import { membersApi } from "@/features/members/api";
import { organizationsApi } from "../api";
import { orgStorage } from "../storage";

const TABS = [
  { key: "general", label: "General", icon: Settings },
  { key: "branding", label: "Branding", icon: Palette },
  { key: "security", label: "Security", icon: Shield },
  { key: "notifications", label: "Notifications", icon: Bell },
  { key: "danger", label: "Danger Zone", icon: AlertTriangle },
] as const;

type SettingsTab = (typeof TABS)[number]["key"];

const DEFAULT_SETTINGS: OrganizationSettings = {
  language: "en",
  notifications: {
    email_enabled: true,
    weekly_reports: true,
    scan_complete: true,
    critical_findings: true,
  },
  security: {
    mfa_policy: "optional",
    password_min_length: 12,
    session_timeout_minutes: 480,
  },
};

interface GeneralForm {
  name: string;
  description: string;
  logo_url: string;
  timezone: string;
  language: string;
}

interface BrandingForm {
  logo_url: string;
  website: string;
  industry: string;
  country: string;
}

export default function OrgSettings() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = (searchParams.get("tab") as SettingsTab) || "general";

  const [org, setOrg] = useState<OrganizationDetail | null>(null);
  const [general, setGeneral] = useState<GeneralForm>({
    name: "",
    description: "",
    logo_url: "",
    timezone: "",
    language: "en",
  });
  const [branding, setBranding] = useState<BrandingForm>({
    logo_url: "",
    website: "",
    industry: "",
    country: "",
  });
  const [notifications, setNotifications] = useState<NotificationSettings>(
    DEFAULT_SETTINGS.notifications,
  );
  const [security, setSecurity] = useState<SecuritySettings>(DEFAULT_SETTINGS.security);
  const [members, setMembers] = useState<MemberSummary[]>([]);
  const [transferTarget, setTransferTarget] = useState("");
  const [canManage, setCanManage] = useState(false);
  const [isOwner, setIsOwner] = useState(false);
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [alert, setAlert] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dangerLoading, setDangerLoading] = useState<string | null>(null);

  const setTab = (next: SettingsTab) => setSearchParams({ tab: next });

  const applyOrg = (data: OrganizationDetail) => {
    const settings = data.settings ?? DEFAULT_SETTINGS;
    setOrg(data);
    setGeneral({
      name: data.name ?? "",
      description: data.description ?? "",
      logo_url: data.logo_url ?? "",
      timezone: data.timezone ?? "",
      language: settings.language ?? "en",
    });
    setBranding({
      logo_url: data.logo_url ?? "",
      website: data.website ?? "",
      industry: data.industry ?? "",
      country: data.country ?? "",
    });
    setNotifications({ ...DEFAULT_SETTINGS.notifications, ...settings.notifications });
    setSecurity({ ...DEFAULT_SETTINGS.security, ...settings.security });
  };

  const loadOrg = async () => {
    const [orgData, orgsData] = await Promise.all([
      organizationsApi.getCurrent(),
      organizationsApi.listMine(),
    ]);
    if (orgData) applyOrg(orgData);
    const activeOrgId = orgStorage.getActiveOrgId();
    const membership = orgsData?.items.find((item) => item.id === activeOrgId);
    if (membership) {
      setCanManage(["owner", "admin"].includes(membership.role));
      setIsOwner(membership.role === "owner");
    }
  };

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        await loadOrg();
      } catch (error) {
        if (active) {
          setAlert(error instanceof ApiError ? error.message : "Unable to load organization.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (tab !== "danger" || !isOwner) return undefined;
    let active = true;

    async function loadMembers() {
      try {
        const data = await membersApi.listMembers({ status: "active", limit: 100 });
        if (active) setMembers(data?.items.filter((m) => m.role !== "owner") ?? []);
      } catch {
        if (active) setMembers([]);
      }
    }

    void loadMembers();
    return () => {
      active = false;
    };
  }, [tab, isOwner]);

  const save = async (payload: Parameters<typeof organizationsApi.updateCurrent>[0]) => {
    setSaving(true);
    setAlert("");
    setSuccess("");
    try {
      const updated = await organizationsApi.updateCurrent(payload);
      if (updated) applyOrg(updated);
      setSuccess("Settings saved.");
    } catch (error) {
      setAlert(error instanceof ApiError ? error.message : "Unable to save settings.");
    } finally {
      setSaving(false);
    }
  };

  const handleGeneralSave = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!general.name.trim()) {
      setErrors({ name: "Organization name is required" });
      return;
    }
    await save({
      name: general.name.trim(),
      description: general.description.trim() || undefined,
      logo_url: general.logo_url.trim() || undefined,
      timezone: general.timezone || undefined,
      settings: { language: general.language },
    });
  };

  const handleBrandingSave = async (event: React.FormEvent) => {
    event.preventDefault();
    await save({
      logo_url: branding.logo_url.trim() || undefined,
      website: branding.website.trim() || undefined,
      industry: branding.industry.trim() || undefined,
      country: branding.country.trim().toUpperCase() || undefined,
    });
  };

  const handleNotificationsSave = async (event: React.FormEvent) => {
    event.preventDefault();
    await save({ settings: { notifications } });
  };

  const handleSecuritySave = async (event: React.FormEvent) => {
    event.preventDefault();
    await save({ settings: { security } });
  };

  const runDangerAction = async (key: string, action: () => Promise<void>, message: string) => {
    setDangerLoading(key);
    setAlert("");
    setSuccess("");
    try {
      await action();
      setSuccess(message);
    } catch (error) {
      setAlert(error instanceof ApiError ? error.message : "Action failed.");
    } finally {
      setDangerLoading(null);
    }
  };

  const handleTransfer = () => {
    if (!transferTarget) return;
    void runDangerAction(
      "transfer",
      async () => {
        await membersApi.transferOwnership(transferTarget);
        await loadOrg();
      },
      "Ownership transferred.",
    );
  };

  const handleArchive = () => {
    if (!window.confirm("Archive this organization? Members will lose access until restored.")) {
      return;
    }
    void runDangerAction(
      "archive",
      async () => {
        await organizationsApi.archiveCurrent();
        orgStorage.clear();
        navigate("/select-organization");
      },
      "Organization archived.",
    );
  };

  const handleDelete = () => {
    if (
      !window.confirm(
        "Delete this organization permanently? This deactivates the workspace and cannot be undone from the UI.",
      )
    ) {
      return;
    }
    void runDangerAction(
      "delete",
      async () => {
        await organizationsApi.deleteCurrent();
        orgStorage.clear();
        navigate("/select-organization");
      },
      "Organization deleted.",
    );
  };

  return (
    <DashboardShell title="Settings" subtitle="Manage organization profile and policies.">
      {alert && <FormAlert message={alert} />}
      {success && <FormAlert message={success} variant="success" />}

      <div className="mb-6 flex flex-wrap gap-2">
        {TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm transition ${
              tab === key
                ? "border-brand-500/50 bg-brand-900/40 text-brand-100"
                : "border-brand-800/50 text-brand-400 hover:border-brand-600/40 hover:text-brand-200"
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="glass-panel animate-pulse p-8">Loading settings...</div>
      ) : !org ? (
        <p className="text-brand-500">Organization not found.</p>
      ) : (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          {tab === "general" && (
            <form onSubmit={handleGeneralSave} className="glass-panel space-y-5 p-8">
              <h2 className="text-lg font-semibold text-brand-100">General</h2>
              <div>
                <label htmlFor="name" className="terminal-text mb-2 block">
                  organization_name
                </label>
                <input
                  id="name"
                  value={general.name}
                  onChange={(e) => setGeneral((prev) => ({ ...prev, name: e.target.value }))}
                  className="input-field"
                  disabled={!canManage}
                />
                <FormError message={errors.name} />
              </div>
              <div>
                <label htmlFor="description" className="terminal-text mb-2 block">
                  description
                </label>
                <textarea
                  id="description"
                  rows={4}
                  value={general.description}
                  onChange={(e) =>
                    setGeneral((prev) => ({ ...prev, description: e.target.value }))
                  }
                  className="input-field"
                  disabled={!canManage}
                />
              </div>
              <div>
                <label htmlFor="logo_url" className="terminal-text mb-2 block">
                  logo_url
                </label>
                <input
                  id="logo_url"
                  value={general.logo_url}
                  onChange={(e) =>
                    setGeneral((prev) => ({ ...prev, logo_url: e.target.value }))
                  }
                  className="input-field"
                  placeholder="https://..."
                  disabled={!canManage}
                />
              </div>
              <div className="grid gap-5 md:grid-cols-2">
                <div>
                  <label htmlFor="timezone" className="terminal-text mb-2 block">
                    timezone
                  </label>
                  <select
                    id="timezone"
                    value={general.timezone}
                    onChange={(e) =>
                      setGeneral((prev) => ({ ...prev, timezone: e.target.value }))
                    }
                    className="input-field"
                    disabled={!canManage}
                  >
                    <option value="">Select timezone</option>
                    {TIMEZONE_OPTIONS.map((tz) => (
                      <option key={tz} value={tz}>
                        {tz}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="language" className="terminal-text mb-2 block">
                    language
                  </label>
                  <select
                    id="language"
                    value={general.language}
                    onChange={(e) =>
                      setGeneral((prev) => ({ ...prev, language: e.target.value }))
                    }
                    className="input-field"
                    disabled={!canManage}
                  >
                    {LANGUAGE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <p className="text-sm text-brand-600">
                Slug: <span className="text-brand-400">{org.slug}</span>
              </p>
              {canManage && (
                <button type="submit" disabled={saving} className="btn-primary inline-flex gap-2">
                  <Save size={18} />
                  {saving ? "Saving..." : "Save changes"}
                </button>
              )}
            </form>
          )}

          {tab === "branding" && (
            <form onSubmit={handleBrandingSave} className="glass-panel space-y-5 p-8">
              <h2 className="text-lg font-semibold text-brand-100">Branding</h2>
              <p className="text-sm text-brand-500">
                Customize how your organization appears across the workspace.
              </p>
              {branding.logo_url && (
                <div className="flex items-center gap-4 rounded-lg border border-brand-800/50 bg-void-200/20 p-4">
                  <img
                    src={branding.logo_url}
                    alt="Organization logo preview"
                    className="h-14 w-14 rounded-lg border border-brand-700/50 object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = "none";
                    }}
                  />
                  <div>
                    <p className="text-sm text-brand-300">Logo preview</p>
                    <p className="text-xs text-brand-600">{branding.logo_url}</p>
                  </div>
                </div>
              )}
              <div>
                <label htmlFor="brand_logo" className="terminal-text mb-2 block">
                  logo_url
                </label>
                <input
                  id="brand_logo"
                  value={branding.logo_url}
                  onChange={(e) =>
                    setBranding((prev) => ({ ...prev, logo_url: e.target.value }))
                  }
                  className="input-field"
                  disabled={!canManage}
                />
              </div>
              <div className="grid gap-5 md:grid-cols-2">
                <div>
                  <label htmlFor="website" className="terminal-text mb-2 block">
                    website
                  </label>
                  <input
                    id="website"
                    value={branding.website}
                    onChange={(e) =>
                      setBranding((prev) => ({ ...prev, website: e.target.value }))
                    }
                    className="input-field"
                    disabled={!canManage}
                  />
                </div>
                <div>
                  <label htmlFor="industry" className="terminal-text mb-2 block">
                    industry
                  </label>
                  <input
                    id="industry"
                    value={branding.industry}
                    onChange={(e) =>
                      setBranding((prev) => ({ ...prev, industry: e.target.value }))
                    }
                    className="input-field"
                    disabled={!canManage}
                  />
                </div>
              </div>
              <div>
                <label htmlFor="country" className="terminal-text mb-2 block">
                  country
                </label>
                <input
                  id="country"
                  value={branding.country}
                  onChange={(e) =>
                    setBranding((prev) => ({ ...prev, country: e.target.value }))
                  }
                  className="input-field"
                  maxLength={2}
                  placeholder="US"
                  disabled={!canManage}
                />
              </div>
              {canManage && (
                <button type="submit" disabled={saving} className="btn-primary inline-flex gap-2">
                  <Save size={18} />
                  {saving ? "Saving..." : "Save branding"}
                </button>
              )}
            </form>
          )}

          {tab === "security" && (
            <form onSubmit={handleSecuritySave} className="glass-panel space-y-5 p-8">
              <h2 className="text-lg font-semibold text-brand-100">Security</h2>
              <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 px-4 py-3 text-sm text-brand-400">
                MFA policy enforcement is planned for a future release. Settings below are stored
                for your organization policy profile.
              </div>
              <div>
                <label htmlFor="mfa_policy" className="terminal-text mb-2 block">
                  mfa_policy
                </label>
                <select
                  id="mfa_policy"
                  value={security.mfa_policy}
                  onChange={(e) =>
                    setSecurity((prev) => ({ ...prev, mfa_policy: e.target.value }))
                  }
                  className="input-field"
                  disabled={!canManage}
                >
                  <option value="optional">Optional (future)</option>
                  <option value="required">Required (future)</option>
                  <option value="disabled">Disabled</option>
                </select>
              </div>
              <div className="grid gap-5 md:grid-cols-2">
                <div>
                  <label htmlFor="password_min" className="terminal-text mb-2 block">
                    password_min_length
                  </label>
                  <input
                    id="password_min"
                    type="number"
                    min={8}
                    max={128}
                    value={security.password_min_length}
                    onChange={(e) =>
                      setSecurity((prev) => ({
                        ...prev,
                        password_min_length: Number(e.target.value),
                      }))
                    }
                    className="input-field"
                    disabled={!canManage}
                  />
                </div>
                <div>
                  <label htmlFor="session_timeout" className="terminal-text mb-2 block">
                    session_timeout
                  </label>
                  <select
                    id="session_timeout"
                    value={security.session_timeout_minutes}
                    onChange={(e) =>
                      setSecurity((prev) => ({
                        ...prev,
                        session_timeout_minutes: Number(e.target.value),
                      }))
                    }
                    className="input-field"
                    disabled={!canManage}
                  >
                    {SESSION_TIMEOUT_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              {canManage && (
                <button type="submit" disabled={saving} className="btn-primary inline-flex gap-2">
                  <Save size={18} />
                  {saving ? "Saving..." : "Save security settings"}
                </button>
              )}
            </form>
          )}

          {tab === "notifications" && (
            <form onSubmit={handleNotificationsSave} className="glass-panel space-y-5 p-8">
              <h2 className="text-lg font-semibold text-brand-100">Notifications</h2>
              <p className="text-sm text-brand-500">
                Choose which email notifications your organization receives.
              </p>
              <ToggleRow
                label="Email notifications"
                description="Master switch for outbound email alerts."
                checked={notifications.email_enabled}
                onChange={(checked) =>
                  setNotifications((prev) => ({ ...prev, email_enabled: checked }))
                }
                disabled={!canManage}
              />
              <ToggleRow
                label="Weekly reports"
                description="Summary of security posture each week."
                checked={notifications.weekly_reports}
                onChange={(checked) =>
                  setNotifications((prev) => ({ ...prev, weekly_reports: checked }))
                }
                disabled={!canManage || !notifications.email_enabled}
              />
              <ToggleRow
                label="Scan complete"
                description="Notify when a scan finishes running."
                checked={notifications.scan_complete}
                onChange={(checked) =>
                  setNotifications((prev) => ({ ...prev, scan_complete: checked }))
                }
                disabled={!canManage || !notifications.email_enabled}
              />
              <ToggleRow
                label="Critical findings"
                description="Immediate alerts for critical severity issues."
                checked={notifications.critical_findings}
                onChange={(checked) =>
                  setNotifications((prev) => ({ ...prev, critical_findings: checked }))
                }
                disabled={!canManage || !notifications.email_enabled}
              />
              {canManage && (
                <button type="submit" disabled={saving} className="btn-primary inline-flex gap-2">
                  <Save size={18} />
                  {saving ? "Saving..." : "Save notification preferences"}
                </button>
              )}
            </form>
          )}

          {tab === "danger" && (
            <div className="space-y-4">
              {!isOwner ? (
                <div className="glass-panel p-6 text-sm text-brand-500">
                  Only the organization owner can manage danger zone actions.
                </div>
              ) : (
                <>
                  <div className="glass-panel space-y-4 border-rose-500/20 p-6">
                    <div className="flex items-center gap-2 text-brand-100">
                      <UserCog size={18} className="text-brand-400" />
                      <h3 className="font-semibold">Transfer ownership</h3>
                    </div>
                    <p className="text-sm text-brand-500">
                      Assign another active member as the new organization owner.
                    </p>
                    <select
                      value={transferTarget}
                      onChange={(e) => setTransferTarget(e.target.value)}
                      className="input-field max-w-md"
                    >
                      <option value="">Select new owner</option>
                      {members.map((member) => (
                        <option key={member.user_id} value={member.user_id ?? ""}>
                          {member.first_name} {member.last_name} ({member.email})
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      disabled={!transferTarget || dangerLoading !== null}
                      onClick={handleTransfer}
                      className="btn-ghost inline-flex items-center gap-2 text-sm"
                    >
                      <UserCog size={16} />
                      {dangerLoading === "transfer" ? "Transferring..." : "Transfer ownership"}
                    </button>
                  </div>

                  <div className="glass-panel space-y-4 border-amber-500/20 p-6">
                    <div className="flex items-center gap-2 text-brand-100">
                      <Archive size={18} className="text-amber-400" />
                      <h3 className="font-semibold">Archive organization</h3>
                    </div>
                    <p className="text-sm text-brand-500">
                      Hide the workspace from active use. Data is preserved but members lose access.
                    </p>
                    <button
                      type="button"
                      disabled={dangerLoading !== null}
                      onClick={handleArchive}
                      className="btn-ghost inline-flex items-center gap-2 text-sm text-amber-300"
                    >
                      <Archive size={16} />
                      {dangerLoading === "archive" ? "Archiving..." : "Archive organization"}
                    </button>
                  </div>

                  <div className="glass-panel space-y-4 border-rose-500/30 p-6">
                    <div className="flex items-center gap-2 text-rose-200">
                      <Trash2 size={18} />
                      <h3 className="font-semibold">Delete organization</h3>
                    </div>
                    <p className="text-sm text-brand-500">
                      Permanently deactivate this organization. This action cannot be undone.
                    </p>
                    <button
                      type="button"
                      disabled={dangerLoading !== null}
                      onClick={handleDelete}
                      className="btn-ghost inline-flex items-center gap-2 text-sm text-rose-300 hover:text-rose-200"
                    >
                      <Trash2 size={16} />
                      {dangerLoading === "delete" ? "Deleting..." : "Delete organization"}
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </motion.div>
      )}
    </DashboardShell>
  );
}

function ToggleRow({
  label,
  description,
  checked,
  onChange,
  disabled,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <label className="flex items-start justify-between gap-4 rounded-lg border border-brand-800/50 px-4 py-3">
      <div>
        <p className="font-medium text-brand-100">{label}</p>
        <p className="text-sm text-brand-500">{description}</p>
      </div>
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        disabled={disabled}
        className="mt-1"
      />
    </label>
  );
}
